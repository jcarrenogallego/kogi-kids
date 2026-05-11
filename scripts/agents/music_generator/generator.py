"""
Music Generator Agent.

Generates Suno prompts for each scene based on emotional tone and duration.
Guides user through manual Suno UI workflow.
Validates downloaded music files match timing requirements.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


# Emotional tone templates for Suno prompts
MUSIC_TEMPLATES = {
    "calm": "Soft piano melody, gentle strings, peaceful atmosphere, Disney-like, warm and comforting",
    "wonder": "Magical orchestral, twinkling chimes, sense of discovery, enchanted feeling, light and playful",
    "adventure": "Uplifting orchestral, moderate tempo, adventure theme, heroic undertones, exciting energy",
    "mystery": "Subtle strings, low woodwinds, mysterious atmosphere, tension building, careful pacing",
    "tense": "Dramatic strings, building tension, urgent pace, dark forest ambiance, suspenseful",
    "emotional": "Warm piano, heartfelt strings, emotional crescendo, touching moment, gentle and sincere",
    "triumphant": "Grand orchestral, victorious theme, soaring melody, epic finale, joyful resolution",
    "resolution": "Peaceful piano, gentle strings, calming conclusion, satisfied feeling, lullaby-like"
}

# Scene-specific emotional tone mapping (Luna y la Estrella Perdida)
SCENE_EMOTIONS = {
    1: "calm",        # Bedroom Opening - peaceful night
    2: "wonder",      # Garden Star Falls - magical discovery
    3: "emotional",   # Garden Connection - heartfelt moment
    4: "adventure",   # Forest Threshold - journey begins
    5: "mystery",     # Owl's Tree - wise encounter
    6: "tense",       # Dark Forest Rescue - danger
    7: "triumphant",  # Hilltop Climax - epic finale
    8: "resolution"   # Bedroom Resolution - peaceful ending
}


@dataclass
class MusicPrompt:
    """
    Represents a Suno music generation prompt for one scene.
    
    Attributes:
        scene_id: Scene number
        title: Scene title
        duration: Target duration in seconds
        emotional_tone: Primary emotion (calm, wonder, adventure, etc.)
        prompt: Complete Suno prompt text
        output_file: Expected output filename (scene_N.mp3)
    """
    scene_id: int
    title: str
    duration: float
    emotional_tone: str
    prompt: str
    output_file: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class MusicGenerator:
    """
    Generates music prompts and validates downloaded files.
    
    This agent handles the MANUAL workflow with Suno UI:
    1. Reads timing.json for scene structure
    2. Generates prompts based on scene emotional tone
    3. Displays step-by-step Suno UI instructions
    4. Validates downloaded MP3 files exist and match durations
    """
    
    def __init__(self, story_dir: Path):
        """
        Initialize music generator.
        
        Args:
            story_dir: Path to story directory (e.g., stories/luna-y-la-estrella-perdida/)
        """
        self.story_dir = story_dir
        self.audio_dir = story_dir / "audio"
        self.music_dir = self.audio_dir / "music"
        self.config_dir = self.audio_dir / "config"
        
        # Create directories if they don't exist
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_timing(self) -> Dict:
        """
        Load timing.json file.
        
        Returns:
            Timing data dictionary
            
        Raises:
            FileNotFoundError: If timing.json doesn't exist
            json.JSONDecodeError: If timing.json is malformed
        """
        timing_file = self.audio_dir / "timing.json"
        
        if not timing_file.exists():
            raise FileNotFoundError(
                f"timing.json not found at {timing_file}. "
                "Run timing extraction first."
            )
        
        with open(timing_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_prompts(self, timing_data: Dict) -> List[MusicPrompt]:
        """
        Generate Suno prompts for all scenes.
        
        Args:
            timing_data: Timing data from timing.json
            
        Returns:
            List of MusicPrompt objects
        """
        prompts = []
        
        for scene in timing_data.get("scenes", []):
            scene_number = scene["scene_number"]
            title = scene["title"]
            duration = scene["total_duration"]
            
            # Get emotional tone from scene mapping, fallback to calm
            emotional_tone = SCENE_EMOTIONS.get(scene_number, "calm")
            
            # Get template or default to calm
            template = MUSIC_TEMPLATES.get(emotional_tone, MUSIC_TEMPLATES["calm"])
            
            # Build complete prompt
            prompt = f"{template}, duration: {int(duration)} seconds, cinematic quality"
            
            # Output filename
            output_file = f"scene_{scene_number}.mp3"
            
            music_prompt = MusicPrompt(
                scene_id=scene_number,
                title=title,
                duration=duration,
                emotional_tone=emotional_tone,
                prompt=prompt,
                output_file=output_file
            )
            
            prompts.append(music_prompt)
            logger.info(f"Generated prompt for Scene {scene_number}: {emotional_tone} ({duration}s)")
        
        return prompts
    
    def save_prompts(self, prompts: List[MusicPrompt]) -> Path:
        """
        Save prompts to music_prompts.json for reference.
        
        Args:
            prompts: List of MusicPrompt objects
            
        Returns:
            Path to saved file
        """
        output_file = self.config_dir / "music_prompts.json"
        
        prompts_data = {
            "story": self.story_dir.name,
            "total_scenes": len(prompts),
            "prompts": [p.to_dict() for p in prompts]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved music prompts to {output_file}")
        return output_file
    
    def display_instructions(self, prompts: List[MusicPrompt]):
        """
        Display step-by-step Suno UI instructions to user.
        
        Args:
            prompts: List of MusicPrompt objects to generate
        """
        print("\n" + "="*60)
        print("🎵 SUNO MUSIC GENERATION - Manual Workflow")
        print("="*60)
        print(f"\nYou need to generate {len(prompts)} music tracks using Suno UI.")
        print(f"Total duration: {sum(p.duration for p in prompts):.0f} seconds")
        print("\n📋 Instructions:")
        print("1. Go to: https://suno.com/create")
        print("2. For each prompt below:")
        print("   a) Copy the prompt text")
        print("   b) Paste into Suno prompt field")
        print("   c) Click 'Create'")
        print("   d) Wait for generation (~2-3 minutes)")
        print("   e) Download MP3 file")
        print(f"   f) Save as: {self.music_dir}/scene_N.mp3")
        print("\n" + "-"*60)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] Scene {prompt.scene_id}: {prompt.title}")
            print(f"Duration: {prompt.duration:.0f} seconds")
            print(f"Emotion: {prompt.emotional_tone}")
            print(f"\n📝 Prompt to copy:")
            print(f"   {prompt.prompt}")
            print(f"\n💾 Save as: {prompt.output_file}")
            print("-"*60)
        
        print("\n⚠️  Important:")
        print("- Download each file with the exact name shown above")
        print(f"- Save all files to: {self.music_dir}/")
        print("- Suno may generate slightly different durations (±2-3s is OK)")
        print("\nAfter downloading all files, run the orchestrator again to validate.")
        print("="*60 + "\n")
    
    def validate_downloads(self, prompts: List[MusicPrompt]) -> Dict[str, any]:
        """
        Validate that all music files were downloaded.
        
        Args:
            prompts: List of expected MusicPrompt objects
            
        Returns:
            Dictionary with validation results:
            {
                "success": bool,
                "missing_files": List[str],
                "validated_files": List[Dict],
                "total_duration": float
            }
        """
        missing_files = []
        validated_files = []
        total_duration = 0.0
        
        for prompt in prompts:
            file_path = self.music_dir / prompt.output_file
            
            if not file_path.exists():
                missing_files.append(prompt.output_file)
                logger.warning(f"Missing music file: {prompt.output_file}")
            else:
                # Basic validation (file exists and has size)
                file_size = file_path.stat().st_size
                
                if file_size == 0:
                    missing_files.append(prompt.output_file)
                    logger.error(f"Corrupted file (0 bytes): {prompt.output_file}")
                else:
                    validated_files.append({
                        "scene_id": prompt.scene_id,
                        "file": prompt.output_file,
                        "expected_duration": prompt.duration,
                        "file_size_mb": round(file_size / (1024 * 1024), 2)
                    })
                    total_duration += prompt.duration
                    logger.info(f"✓ Validated: {prompt.output_file} ({file_size/1024:.1f} KB)")
        
        success = len(missing_files) == 0
        
        if success:
            logger.info(f"All {len(prompts)} music files validated successfully")
        else:
            logger.error(f"Missing {len(missing_files)} music files")
        
        return {
            "success": success,
            "missing_files": missing_files,
            "validated_files": validated_files,
            "total_duration": total_duration,
            "files_found": len(validated_files),
            "files_expected": len(prompts)
        }
    
    def run(self) -> Dict[str, any]:
        """
        Execute full music generation workflow.
        
        Returns:
            Dictionary with execution results
        """
        logger.info("Starting music generation workflow")
        
        # Load timing data
        timing_data = self.load_timing()
        logger.info(f"Loaded timing data for {len(timing_data.get('scenes', []))} scenes")
        
        # Generate prompts
        prompts = self.generate_prompts(timing_data)
        logger.info(f"Generated {len(prompts)} music prompts")
        
        # Save prompts to JSON
        prompts_file = self.save_prompts(prompts)
        
        # Check if files already exist
        validation = self.validate_downloads(prompts)
        
        if validation["success"]:
            logger.info("All music files already exist and validated")
            print(f"\n✅ All {len(prompts)} music files found and validated")
            print(f"Total duration: {validation['total_duration']:.1f} seconds")
            return {
                "status": "complete",
                "validation": validation,
                "prompts_file": str(prompts_file)
            }
        else:
            # Display instructions for manual generation
            self.display_instructions(prompts)
            
            return {
                "status": "awaiting_download",
                "missing_files": validation["missing_files"],
                "prompts_file": str(prompts_file),
                "message": f"Please download {len(validation['missing_files'])} missing music files from Suno"
            }


def generate_music(story_dir: Path) -> Dict[str, any]:
    """
    Main entry point for music generation agent.
    
    Args:
        story_dir: Path to story directory
        
    Returns:
        Execution results dictionary
    """
    generator = MusicGenerator(story_dir)
    return generator.run()
