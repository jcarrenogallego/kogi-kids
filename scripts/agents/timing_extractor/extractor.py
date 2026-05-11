"""
Timing Extractor Agent.

Extracts scene, shot, and timing information from storyboard-timing.md.
Merges with dialogue data from dialogues-es.md.
Outputs structured JSON with cumulative timestamps.
"""
import sys
import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


# Regex patterns for markdown parsing
SCENE_PATTERN = re.compile(
    r'###?\s+(?:ESCENA|Scene)\s+(\d+):\s+(.+?)\s*(?:\((\d+)\s*segundos?\))?$',
    re.IGNORECASE
)
SHOT_PATTERN = re.compile(
    r'####?\s+Shot\s+(\w+)\s*(?:-\s*(.+?))?$',
    re.IGNORECASE
)
DURATION_PATTERN = re.compile(
    r'\*\*Duración\*\*:\s*(\d+)\s*segundos?',
    re.IGNORECASE
)
NARRATIVA_PATTERN = re.compile(
    r'\*\*Narrativa\*\*:\s*\n\s*>\s*"?(.+?)"?\s*(?=\n-\s*\*\*|\n\*\*(?!Narrativa)|\n####|\n###|$)',
    re.DOTALL | re.IGNORECASE
)


class DurationMismatchError(Exception):
    """Raised when total duration doesn't match expected value."""
    pass


@dataclass
class Shot:
    """
    Represents a single shot within a scene.
    
    Attributes:
        shot_id: Shot identifier (e.g., "1A", "2B")
        description: Shot description
        duration: Duration in seconds
        start_time: Cumulative start time in seconds
        end_time: Cumulative end time in seconds
        narrative: Narrator text for this shot
        character: Character speaking (narrator, luna, estrellita, oliver)
        dialogue: Character dialogue text (if any)
        has_dialogue: Whether this shot has character dialogue
        render_file: Path to render image file
    """
    shot_id: str
    description: str
    duration: float
    start_time: float = 0.0
    end_time: float = 0.0
    narrative: str = ""
    character: str = "narrator"
    dialogue: str = ""
    has_dialogue: bool = False
    render_file: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Scene:
    """
    Represents a scene containing multiple shots.
    
    Attributes:
        scene_number: Scene number (1, 2, 3, ...)
        title: Scene title
        shots: List of Shot objects
        total_duration: Total duration of all shots in seconds
    """
    scene_number: int
    title: str
    shots: List[Shot] = field(default_factory=list)
    total_duration: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "scene_number": self.scene_number,
            "title": self.title,
            "total_duration": self.total_duration,
            "shots": [shot.to_dict() for shot in self.shots]
        }


@dataclass
class TimingData:
    """
    Complete timing data for a story.
    
    Attributes:
        story: Story name
        total_duration: Total duration in seconds
        scenes: List of Scene objects
    """
    story: str
    total_duration: float
    scenes: List[Scene] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "story": self.story,
            "total_duration": self.total_duration,
            "total_scenes": len(self.scenes),
            "total_shots": sum(len(scene.shots) for scene in self.scenes),
            "scenes": [scene.to_dict() for scene in self.scenes]
        }


class TimingExtractor:
    """
    Extracts timing and dialogue data from markdown files.
    
    Example:
        >>> extractor = TimingExtractor(Path("stories/luna-y-la-estrella-perdida"))
        >>> timing_data = extractor.extract_timing()
        >>> extractor.write_json(timing_data, Path("audio/timing.json"))
    """
    
    def __init__(self, story_path: Path):
        """
        Initialize extractor for a story.
        
        Args:
            story_path: Path to story directory (e.g., stories/luna-y-la-estrella-perdida)
        """
        self.story_path = Path(story_path)
        self.story_name = story_path.name
        self.storyboard_file = story_path / "storyboard-timing.md"
        self.dialogues_file = story_path / "dialogues" / "dialogues-es.md"
        
        # Validate required files exist
        if not self.storyboard_file.exists():
            raise FileNotFoundError(f"Storyboard file not found: {self.storyboard_file}")
    
    def extract_timing(
        self, 
        expected_duration: Optional[float] = None, 
        tolerance: float = 0.5,
        strict: bool = False
    ) -> TimingData:
        """
        Extract complete timing data from storyboard.
        
        Args:
            expected_duration: Expected total duration in seconds (optional)
            tolerance: Allowed deviation in seconds (±)
            strict: If True, raise error on mismatch; if False, only warn
            
        Returns:
            TimingData object with all scenes and shots
            
        Raises:
            DurationMismatchError: If strict=True and duration doesn't match
            
        Example:
            >>> timing = extractor.extract_timing(expected_duration=137.0)
            >>> print(f"Total: {timing.total_duration}s")
        """
        logger.info(f"Extracting timing from {self.storyboard_file}")
        
        # Read storyboard file
        content = self._read_file(self.storyboard_file)
        
        # Parse scenes and shots
        scenes = self._parse_scenes(content)
        
        # Calculate cumulative timestamps
        scenes = self._calculate_timestamps(scenes)
        
        # Merge dialogue data (if available)
        if self.dialogues_file.exists():
            scenes = self._merge_dialogues(scenes)
        else:
            logger.warning(f"Dialogues file not found: {self.dialogues_file}")
        
        # Calculate total duration
        total_duration = scenes[-1].shots[-1].end_time if scenes else 0.0
        
        # Validate duration (if expected duration provided)
        if expected_duration is not None:
            duration_diff = abs(total_duration - expected_duration)
            if duration_diff > tolerance:
                message = (
                    f"Total duration {total_duration:.1f}s doesn't match expected {expected_duration:.1f}s "
                    f"(difference: {duration_diff:.1f}s, tolerance: ±{tolerance}s)"
                )
                if strict:
                    raise DurationMismatchError(message)
                else:
                    logger.warning(message)
                    logger.warning("Continuing with extracted duration (strict mode disabled)")
        
        timing_data = TimingData(
            story=self.story_name,
            total_duration=total_duration,
            scenes=scenes
        )
        
        logger.info(f"Extracted {len(scenes)} scenes, {sum(len(s.shots) for s in scenes)} shots")
        logger.info(f"Total duration: {total_duration:.1f}s")
        
        return timing_data
    
    def _parse_scenes(self, content: str) -> List[Scene]:
        """
        Parse scenes and shots from markdown content.
        
        Args:
            content: Storyboard markdown content
            
        Returns:
            List of Scene objects with shots
        """
        scenes: List[Scene] = []
        current_scene: Optional[Scene] = None
        lines = content.split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for scene header
            scene_match = SCENE_PATTERN.search(line)
            if scene_match:
                scene_number = int(scene_match.group(1))
                scene_title = scene_match.group(2).strip()
                
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = Scene(
                    scene_number=scene_number,
                    title=scene_title
                )
                logger.debug(f"Found scene {scene_number}: {scene_title}")
                i += 1
                continue
            
            # Check for shot header
            shot_match = SHOT_PATTERN.search(line)
            if shot_match and current_scene:
                shot_id = shot_match.group(1).upper()
                description = shot_match.group(2).strip() if shot_match.group(2) else ""
                
                # Look for duration in next lines
                duration = None
                narrative = ""
                render_file = None
                
                j = i + 1
                shot_content = []
                while j < len(lines) and not SHOT_PATTERN.search(lines[j]) and not SCENE_PATTERN.search(lines[j]):
                    shot_content.append(lines[j])
                    j += 1
                
                shot_text = "\n".join(shot_content)
                
                # Extract duration
                duration_match = DURATION_PATTERN.search(shot_text)
                if duration_match:
                    duration = float(duration_match.group(1))
                
                if duration is None:
                    logger.warning(f"Shot {shot_id} missing duration, defaulting to 5.0s")
                    duration = 5.0
                
                # Extract narrative
                narrative_match = NARRATIVA_PATTERN.search(shot_text)
                if narrative_match:
                    narrative = narrative_match.group(1).strip()
                    # Clean up narrative text - remove markdown artifacts
                    narrative = re.sub(r'\s+', ' ', narrative)
                    narrative = narrative.replace('"', '').replace('"', '')
                    # Stop at audio/transition markers
                    narrative = re.split(r'\s*-\s*\*\*(?:Audio|Transición|Efecto)', narrative)[0].strip()
                
                # Extract render file
                render_match = re.search(r'\*\*Archivo\*\*:\s*`(.+?)`', shot_text)
                if render_match:
                    render_file = render_match.group(1)
                
                shot = Shot(
                    shot_id=shot_id,
                    description=description,
                    duration=duration,
                    narrative=narrative,
                    render_file=render_file
                )
                
                current_scene.shots.append(shot)
                logger.debug(f"  Found shot {shot_id}: {duration}s")
                
                i = j
                continue
            
            i += 1
        
        # Add last scene
        if current_scene:
            scenes.append(current_scene)
        
        # Calculate scene durations
        for scene in scenes:
            scene.total_duration = sum(shot.duration for shot in scene.shots)
        
        return scenes
    
    def _calculate_timestamps(self, scenes: List[Scene]) -> List[Scene]:
        """
        Calculate cumulative start_time and end_time for each shot.
        
        Args:
            scenes: List of scenes with shots
            
        Returns:
            Updated scenes with timestamps
        """
        cumulative = 0.0
        
        for scene in scenes:
            for shot in scene.shots:
                shot.start_time = cumulative
                shot.end_time = cumulative + shot.duration
                cumulative = shot.end_time
        
        logger.debug(f"Calculated timestamps: 0.0s to {cumulative:.1f}s")
        
        return scenes
    
    def _merge_dialogues(self, scenes: List[Scene]) -> List[Scene]:
        """
        Merge dialogue data from dialogues-es.md.
        
        For MVP, this is a simplified implementation that:
        1. Uses narrative text as narrator dialogue
        2. Can be extended to parse scene-based dialogues
        
        Args:
            scenes: List of scenes with shots
            
        Returns:
            Updated scenes with dialogue data
        """
        # For MVP, narrative text from storyboard is the narrator dialogue
        # Character-specific dialogue extraction will be added in Phase 4
        
        for scene in scenes:
            for shot in scene.shots:
                if shot.narrative:
                    shot.dialogue = shot.narrative
                    shot.character = "narrator"
                    shot.has_dialogue = True
        
        logger.info("Merged narrative text as narrator dialogue")
        logger.info("Character-specific dialogue parsing will be added in Phase 4")
        
        return scenes
    
    def write_json(self, timing_data: TimingData, output_path: Path) -> None:
        """
        Write timing data to JSON file.
        
        Args:
            timing_data: TimingData object
            output_path: Path to output JSON file
            
        Example:
            >>> extractor.write_json(timing_data, Path("audio/timing.json"))
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timing_data.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote timing data to {output_path}")
    
    @staticmethod
    def _read_file(file_path: Path) -> str:
        """
        Read file content with UTF-8 encoding.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as string
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


def main():
    """CLI entry point for standalone testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract timing data from storyboard")
    parser.add_argument("story", help="Story directory name")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    try:
        # Extract timing (no strict duration validation for MVP)
        story_path = Path("../stories") / args.story
        extractor = TimingExtractor(story_path)
        timing_data = extractor.extract_timing(expected_duration=None)
        
        # Write output
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = story_path / "audio" / "timing.json"
        
        extractor.write_json(timing_data, output_path)
        
        print(f"\n✓ Successfully extracted timing data")
        print(f"  Scenes: {len(timing_data.scenes)}")
        print(f"  Total shots: {sum(len(s.shots) for s in timing_data.scenes)}")
        print(f"  Duration: {timing_data.total_duration:.1f}s")
        print(f"  Output: {output_path}")
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
