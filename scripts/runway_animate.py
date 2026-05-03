#!/usr/bin/env python3
"""
Runway Gen-3 API automation script for batch image-to-video generation.

This script automates the workflow of:
1. Discovering HIGH priority shots from storyboard-timing.md
2. Loading image files and motion prompts
3. Generating videos via Runway API
4. Tracking progress and handling failures
5. Saving outputs to animations/ directory

Usage:
    python runway-animate.py --story luna-y-la-estrella-perdida
    python runway-animate.py --story luna-y-la-estrella-perdida --shots 2B,6D,7C
    python runway-animate.py --story luna-y-la-estrella-perdida --resume
    python runway-animate.py --story luna-y-la-estrella-perdida --mock
"""
import os
import sys
import json
import time
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Model costs per second (USD)
MODEL_COSTS = {
    "gen4.5": 0.12,
    "gen4_turbo": 0.05
}

# Priority levels
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"


def load_config() -> Dict:
    """
    Load configuration from .env file.
    
    Returns:
        Dict containing configuration values
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Load .env from scripts directory
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
    
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        raise ValueError(
            "RUNWAY_API_KEY not configured. "
            "Copy scripts/.env.example to scripts/.env and add your API key."
        )
    
    return {
        'api_key': api_key,
        'api_base_url': os.getenv('RUNWAY_API_BASE_URL', 'https://api.runwayml.com/v1'),
        'default_model': os.getenv('RUNWAY_DEFAULT_MODEL', 'gen4_turbo'),
        'default_duration': int(os.getenv('RUNWAY_DEFAULT_DURATION', '10')),
        'timeout': int(os.getenv('RUNWAY_TIMEOUT', '300')),
        'poll_interval': int(os.getenv('RUNWAY_POLL_INTERVAL', '5')),
        'max_budget': float(os.getenv('RUNWAY_MAX_BUDGET', '50.00')),
        'warn_threshold': float(os.getenv('RUNWAY_WARN_THRESHOLD', '40.00')),
        'stories_path': os.getenv('STORIES_PATH', 'stories'),
        'renders_path': os.getenv('RENDERS_PATH', 'renders'),
        'animations_path': os.getenv('ANIMATIONS_PATH', 'animations'),
    }


def estimate_cost(shots: List[Dict], model: str, duration: int) -> Tuple[float, float]:
    """
    Calculate estimated cost range for batch video generation.
    
    Args:
        shots: List of shot dictionaries with metadata
        model: Model name (gen4_turbo or gen4.5)
        duration: Video duration in seconds
        
    Returns:
        Tuple of (min_cost, max_cost) in USD
        
    Note:
        Actual costs may vary based on:
        - Content moderation failures (credited)
        - API rate limits causing retries
        - Premium model features used
    """
    if model not in MODEL_COSTS:
        raise ValueError(f"Unknown model: {model}. Valid models: {list(MODEL_COSTS.keys())}")
    
    cost_per_second = MODEL_COSTS[model]
    cost_per_video = cost_per_second * duration
    
    # Min cost: all videos succeed on first try
    min_cost = len(shots) * cost_per_video
    
    # Max cost: 20% failure rate requiring retries (conservative estimate)
    max_cost = min_cost * 1.2
    
    return (round(min_cost, 2), round(max_cost, 2))


def discover_shots(story_slug: str, config: Dict) -> List[Dict]:
    """
    Parse storyboard-timing.md and extract HIGH priority shots.
    
    Args:
        story_slug: Story directory name (e.g., 'luna-y-la-estrella-perdida')
        config: Configuration dictionary
        
    Returns:
        List of shot dictionaries with keys:
        - shot_id: e.g., '2B'
        - scene: e.g., 'Scene 2'
        - duration: duration in seconds
        - render_file: filename in renders/ directory
        - priority: 'HIGH' (always for this function)
        - spectacle_marker: marker like ⭐ SPECTACLE if present
        
    Raises:
        FileNotFoundError: If storyboard-timing.md doesn't exist
    """
    project_root = Path(__file__).parent.parent
    storyboard_path = project_root / config['stories_path'] / story_slug / 'storyboard-timing.md'
    
    if not storyboard_path.exists():
        raise FileNotFoundError(f"Storyboard not found: {storyboard_path}")
    
    with open(storyboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    shots = []
    
    # Parse shots using regex patterns
    # Pattern: #### Shot <ID> - <Title> [<markers>]
    # Priority is marked in special comments or keywords
    shot_pattern = re.compile(
        r'#### Shot ([0-9A-Z]+) - (.+?)(?:\s+(⭐|💖|🦸‍♀️|💫)\s+(\w+))?$',
        re.MULTILINE
    )
    
    # Find all shots and check for HIGH priority markers
    for match in shot_pattern.finditer(content):
        shot_id = match.group(1)
        shot_title = match.group(2)
        marker_emoji = match.group(3)
        marker_text = match.group(4)
        
        # Extract section after this shot until next shot or scene
        shot_pos = match.end()
        next_match = shot_pattern.search(content, shot_pos)
        shot_section = content[shot_pos:(next_match.start() if next_match else len(content))]
        
        # Check for HIGH priority indicators:
        # 1. Spectacle markers (⭐ SPECTACLE, 💖 EMOTIONAL CORE, etc.)
        # 2. Explicit HIGH priority in comments
        is_high_priority = False
        spectacle_marker = None
        
        if marker_emoji and marker_text:
            if marker_text in ['SPECTACLE', 'EMOTIONAL', 'EPIC', 'MONEY']:
                is_high_priority = True
                spectacle_marker = f"{marker_emoji} {marker_text}"
        
        # Also check for explicit HIGH in section
        if 'priority: HIGH' in shot_section.lower() or '**priority**: high' in shot_section.lower():
            is_high_priority = True
        
        if not is_high_priority:
            continue  # Skip non-HIGH priority shots
        
        # Extract duration
        duration_match = re.search(r'\*\*Duración\*\*:\s*(\d+)\s+segundos?', shot_section)
        duration = int(duration_match.group(1)) if duration_match else 10
        
        # Extract render filename
        render_match = re.search(r'\*\*Archivo\*\*:\s*`(.+?)`', shot_section)
        if not render_match:
            print(f"⚠️  Warning: Shot {shot_id} has no render file specified, skipping")
            continue
        
        render_file = render_match.group(1)
        
        # Extract scene number from position in file
        scene_match = re.search(rf'### ESCENA (\d+):.+?{re.escape(shot_id)}', content, re.DOTALL)
        scene = f"Scene {scene_match.group(1)}" if scene_match else "Unknown"
        
        shots.append({
            'shot_id': shot_id,
            'scene': scene,
            'title': shot_title.strip(),
            'duration': duration,
            'render_file': render_file,
            'priority': PRIORITY_HIGH,
            'spectacle_marker': spectacle_marker
        })
    
    return shots


def load_motion_prompt(story_slug: str, shot_id: str, config: Dict) -> Optional[str]:
    """
    Load motion prompt for a shot from prompts-es.md (Spanish version preferred).
    
    Args:
        story_slug: Story directory name
        shot_id: Shot identifier (e.g., '2B')
        config: Configuration dictionary
        
    Returns:
        Motion prompt string or None if not found
        
    Note:
        Motion prompts should be in format:
        #### Motion Prompt for Shot <ID>
        ```
        <motion prompt text>
        ```
    """
    project_root = Path(__file__).parent.parent
    
    # Try Spanish version first, then English
    for prompts_file in ['prompts-es.md', 'prompts.md']:
        prompts_path = project_root / config['stories_path'] / story_slug / 'prompts' / prompts_file
        
        if not prompts_path.exists():
            continue
        
        with open(prompts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for motion prompt section for this shot
        # Pattern: #### Motion Prompt for Shot <ID> or ### Prompt <ID>
        pattern = rf'####\s+(?:Motion Prompt for Shot|Prompt)\s+{shot_id}.*?```\s*(.+?)\s*```'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
    
    # If no motion prompt found, return generic prompt
    print(f"⚠️  Warning: No motion prompt found for shot {shot_id}, using generic prompt")
    return "Smooth camera movement, subtle character animation, cinematic lighting"


def generate_video_mock(shot: Dict, config: Dict) -> Dict:
    """
    Mock video generation for testing without consuming API credits.
    
    Args:
        shot: Shot dictionary
        config: Configuration dictionary
        
    Returns:
        Result dictionary with success status and metadata
    """
    print(f"  🎬 [MOCK] Generating video for shot {shot['shot_id']}...")
    time.sleep(2)  # Simulate API call
    
    # Simulate 80% success rate
    import random
    success = random.random() < 0.8
    
    if success:
        return {
            'success': True,
            'shot_id': shot['shot_id'],
            'video_url': f"https://mock.runway.com/videos/{shot['shot_id']}.mp4",
            'output_path': f"animations/{shot['shot_id']}.mp4",
            'credits_used': shot['duration'] * MODEL_COSTS[config['default_model']],
            'generation_time': 120,
            'message': 'Mock generation successful'
        }
    else:
        return {
            'success': False,
            'shot_id': shot['shot_id'],
            'error': 'Mock failure: Content moderation (random)',
            'credits_used': 0
        }


def generate_video_real(shot: Dict, config: Dict, motion_prompt: str) -> Dict:
    """
    Generate video via Runway API (real implementation).
    
    Args:
        shot: Shot dictionary
        config: Configuration dictionary
        motion_prompt: Motion description for video generation
        
    Returns:
        Result dictionary with success status and metadata
        
    Raises:
        ImportError: If runwayml package not installed
    """
    try:
        from runwayml import RunwayML
    except ImportError:
        raise ImportError(
            "runwayml package not installed. "
            "Install with: pip install runwayml"
        )
    
    print(f"  🎬 Generating video for shot {shot['shot_id']}...")
    
    project_root = Path(__file__).parent.parent
    story_path = project_root / config['stories_path'] / shot['story_slug']
    
    # Load image file
    image_path = story_path / shot['render_file']
    if not image_path.exists():
        return {
            'success': False,
            'shot_id': shot['shot_id'],
            'error': f'Image file not found: {image_path}',
            'credits_used': 0
        }
    
    # Initialize Runway client
    client = RunwayML(api_key=config['api_key'])
    
    try:
        # Read image as base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Create generation task
        start_time = time.time()
        
        # API call to generate video
        task = client.image_to_video.create(
            model=config['default_model'],
            prompt_image=image_data,
            prompt_text=motion_prompt,
            duration=shot['duration'],
            ratio="16:9"
        )
        
        # Poll for completion
        timeout = config['timeout']
        poll_interval = config['poll_interval']
        elapsed = 0
        
        while elapsed < timeout:
            status = client.tasks.retrieve(task.id)
            
            if status.status == 'SUCCEEDED':
                generation_time = int(time.time() - start_time)
                
                # Download video
                output_dir = story_path / config['animations_path']
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"{shot['shot_id']}.mp4"
                
                # Download from URL
                import requests
                response = requests.get(status.output[0], timeout=30)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    'success': True,
                    'shot_id': shot['shot_id'],
                    'video_url': status.output[0],
                    'output_path': str(output_path.relative_to(project_root)),
                    'credits_used': shot['duration'] * MODEL_COSTS[config['default_model']],
                    'generation_time': generation_time,
                    'task_id': task.id
                }
            
            elif status.status == 'FAILED':
                return {
                    'success': False,
                    'shot_id': shot['shot_id'],
                    'error': status.failure_reason or 'Unknown error',
                    'credits_used': 0,
                    'task_id': task.id
                }
            
            # Still processing
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        # Timeout
        return {
            'success': False,
            'shot_id': shot['shot_id'],
            'error': f'Timeout after {timeout}s',
            'credits_used': 0,
            'task_id': task.id
        }
        
    except Exception as e:
        return {
            'success': False,
            'shot_id': shot['shot_id'],
            'error': str(e),
            'credits_used': 0
        }


def save_progress(progress: Dict, story_slug: str, config: Dict):
    """
    Save progress to JSON file for resume capability.
    
    Args:
        progress: Progress dictionary containing results and metadata
        story_slug: Story directory name
        config: Configuration dictionary
    """
    project_root = Path(__file__).parent.parent
    story_path = project_root / config['stories_path'] / story_slug
    progress_dir = story_path / config['animations_path']
    progress_dir.mkdir(exist_ok=True)
    
    progress_path = progress_dir / 'progress.json'
    
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Progress saved to {progress_path.relative_to(project_root)}")


def load_progress(story_slug: str, config: Dict) -> Optional[Dict]:
    """
    Load existing progress from JSON file.
    
    Args:
        story_slug: Story directory name
        config: Configuration dictionary
        
    Returns:
        Progress dictionary or None if file doesn't exist
    """
    project_root = Path(__file__).parent.parent
    story_path = project_root / config['stories_path'] / story_slug
    progress_path = story_path / config['animations_path'] / 'progress.json'
    
    if not progress_path.exists():
        return None
    
    with open(progress_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_shots_to_process(shots: List[Dict], shot_ids: Optional[List[str]], 
                            existing_progress: Optional[Dict]) -> List[Dict]:
    """
    Filter shots based on CLI arguments and existing progress.
    
    Args:
        shots: All discovered HIGH priority shots
        shot_ids: Specific shot IDs requested via --shots argument
        existing_progress: Existing progress dictionary if --resume
        
    Returns:
        Filtered list of shots to process
    """
    # Filter by specific shot IDs if provided
    if shot_ids:
        shots = [s for s in shots if s['shot_id'] in shot_ids]
        if not shots:
            print(f"❌ No matching shots found for IDs: {shot_ids}")
            return []
    
    # Filter out already completed shots if resuming
    if existing_progress:
        completed_ids = {r['shot_id'] for r in existing_progress.get('results', []) 
                        if r['success']}
        shots = [s for s in shots if s['shot_id'] not in completed_ids]
        if not shots:
            print("✅ All shots already completed!")
            return []
        print(f"📝 Resuming: {len(shots)} shots remaining")
    
    return shots


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Runway Gen-3 API automation for batch video generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all HIGH priority shots
  python runway-animate.py --story luna-y-la-estrella-perdida
  
  # Generate specific shots only
  python runway-animate.py --story luna-y-la-estrella-perdida --shots 2B,6D,7C,7D
  
  # Resume interrupted batch
  python runway-animate.py --story luna-y-la-estrella-perdida --resume
  
  # Test without using API credits
  python runway-animate.py --story luna-y-la-estrella-perdida --mock
        """
    )
    
    parser.add_argument(
        '--story',
        required=True,
        help='Story slug (directory name under stories/)'
    )
    parser.add_argument(
        '--shots',
        help='Comma-separated shot IDs (e.g., 2B,6D,7C,7D). If omitted, processes all HIGH priority shots.'
    )
    parser.add_argument(
        '--model',
        default=None,
        choices=['gen4_turbo', 'gen4.5'],
        help='Model to use (default from .env or gen4_turbo)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Override video duration in seconds (5-10, default from .env or 10)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from existing progress.json, skip completed shots'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Mock mode: test workflow without using API credits'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    
    # Override config with CLI arguments
    if args.model:
        config['default_model'] = args.model
    if args.duration:
        if not (5 <= args.duration <= 10):
            print("❌ Duration must be between 5 and 10 seconds")
            return 1
        config['default_duration'] = args.duration
    
    story_slug = args.story
    shot_ids_filter = args.shots.split(',') if args.shots else None
    
    print(f"\n🎬 Runway Gen-3 Video Generation")
    print(f"{'='*60}")
    print(f"Story: {story_slug}")
    print(f"Model: {config['default_model']}")
    print(f"Duration: {config['default_duration']}s")
    print(f"Mode: {'MOCK' if args.mock else 'REAL API'}")
    print(f"{'='*60}\n")
    
    # Discover shots
    try:
        print("📋 Discovering HIGH priority shots from storyboard...")
        all_shots = discover_shots(story_slug, config)
        
        if not all_shots:
            print("❌ No HIGH priority shots found in storyboard")
            return 1
        
        print(f"✅ Found {len(all_shots)} HIGH priority shots")
        for shot in all_shots:
            marker = f" {shot['spectacle_marker']}" if shot['spectacle_marker'] else ""
            print(f"   • {shot['shot_id']}: {shot['title']}{marker}")
        print()
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    
    # Load existing progress if resuming
    existing_progress = load_progress(story_slug, config) if args.resume else None
    if existing_progress:
        print(f"📝 Loaded existing progress: {len(existing_progress.get('results', []))} shots completed")
    
    # Filter shots to process
    shots_to_process = filter_shots_to_process(all_shots, shot_ids_filter, existing_progress)
    
    if not shots_to_process:
        return 0
    
    # Estimate cost
    min_cost, max_cost = estimate_cost(shots_to_process, config['default_model'], 
                                       config['default_duration'])
    
    print(f"💰 Cost Estimate:")
    print(f"   Model: {config['default_model']} (${MODEL_COSTS[config['default_model']]}/sec)")
    print(f"   Shots: {len(shots_to_process)} × {config['default_duration']}s")
    print(f"   Range: ${min_cost} - ${max_cost} USD")
    
    if max_cost > config['warn_threshold']:
        print(f"   ⚠️  Warning: Estimated cost exceeds ${config['warn_threshold']} threshold")
    
    if not args.mock and max_cost > config['max_budget']:
        print(f"   ❌ Estimated cost exceeds budget limit of ${config['max_budget']}")
        print(f"   Reduce shots or increase RUNWAY_MAX_BUDGET in .env")
        return 1
    
    print()
    
    # Generate videos
    print(f"🎬 Generating {len(shots_to_process)} videos...\n")
    
    results = existing_progress.get('results', []) if existing_progress else []
    total_credits = existing_progress.get('total_credits_used', 0.0) if existing_progress else 0.0
    
    for i, shot in enumerate(shots_to_process, 1):
        print(f"[{i}/{len(shots_to_process)}] Shot {shot['shot_id']}: {shot['title']}")
        
        # Add story_slug to shot dict for generate functions
        shot['story_slug'] = story_slug
        
        # Load motion prompt
        motion_prompt = load_motion_prompt(story_slug, shot['shot_id'], config)
        print(f"  📝 Motion: {motion_prompt[:60]}...")
        
        # Generate video
        if args.mock:
            result = generate_video_mock(shot, config)
        else:
            result = generate_video_real(shot, config, motion_prompt)
        
        results.append(result)
        total_credits += result.get('credits_used', 0)
        
        # Display result
        if result['success']:
            print(f"  ✅ Success! Output: {result['output_path']}")
            print(f"  💰 Credits used: ${result['credits_used']:.2f}")
            print(f"  ⏱️  Generation time: {result['generation_time']}s")
        else:
            print(f"  ❌ Failed: {result['error']}")
        
        print()
        
        # Save progress after each shot
        progress = {
            'story': story_slug,
            'timestamp': datetime.now().isoformat(),
            'model': config['default_model'],
            'duration': config['default_duration'],
            'total_shots': len(shots_to_process),
            'completed_shots': i,
            'total_credits_used': round(total_credits, 2),
            'results': results
        }
        save_progress(progress, story_slug, config)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🏁 Generation Complete")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"💰 Total credits used: ${total_credits:.2f}")
    
    if failed:
        print(f"\n❌ Failed shots:")
        for result in failed:
            print(f"   • {result['shot_id']}: {result['error']}")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
