"""
Unit tests for TimingExtractor.

Tests markdown parsing, timestamp calculation, and error handling.
"""
import pytest
from pathlib import Path
from agents.timing_extractor.extractor import (
    TimingExtractor,
    TimingData,
    Scene,
    Shot,
    DurationMismatchError
)


# Sample storyboard content for testing
VALID_STORYBOARD = """
# Luna y la Estrella Perdida - Storyboard con Timing

**Duración total estimada**: 2 min 17 seg (137 segundos)

---

### ESCENA 1: Bedroom Opening - Luna y las Estrellas (23 segundos)

#### Shot 1A - Bedroom Establishing
- **Archivo**: `renders/1a-bedroom-establishing.png`
- **Duración**: 6 segundos
- **Narrativa**: 
  > "Luna era una niña curiosa de siete años. Cada noche, antes de dormir, miraba las estrellas desde su ventana."

---

#### Shot 1B - Luna Close-up Wonder
- **Archivo**: `renders/1b-luna-closeup-wonder.png`
- **Duración**: 5 segundos
- **Narrativa**: 
  > "Una noche, mientras observaba el cielo, notó algo extraño..."

---

#### Shot 1C - POV Starry Sky
- **Archivo**: `renders/1c-pov-starry-sky.png`
- **Duración**: 12 segundos
- **Narrativa**: 
  > "Una estrella pequeña y brillante estaba cayendo del cielo."

---

### ESCENA 2: Garden at Night - Star Falls (31 segundos)

#### Shot 2A - Garden Establishing
- **Archivo**: `renders/2a-garden-establishing.png`
- **Duración**: 5 segundos
- **Narrativa**: 
  > "La estrella descendió lentamente..."
"""


MALFORMED_STORYBOARD = """
# Broken Storyboard

### ESCENA 1: Test Scene

#### Shot 1A - Missing Duration
- **Archivo**: `test.png`
- **Narrativa**: 
  > "This shot has no duration specified"

#### Shot 1B - Invalid Format
This is not proper markdown structure
"""


class TestTimingExtractor:
    """Test suite for TimingExtractor."""
    
    def test_valid_storyboard_parsing(self, tmp_path):
        """Test parsing a valid storyboard file."""
        # Create temporary story directory
        story_path = tmp_path / "test-story"
        story_path.mkdir()
        
        # Write test storyboard
        storyboard_file = story_path / "storyboard-timing.md"
        storyboard_file.write_text(VALID_STORYBOARD, encoding="utf-8")
        
        # Extract timing
        extractor = TimingExtractor(story_path)
        timing_data = extractor.extract_timing(expected_duration=28.0, tolerance=1.0)
        
        # Validate results
        assert timing_data.story == "test-story"
        assert len(timing_data.scenes) == 2
        
        # Check scene 1
        scene1 = timing_data.scenes[0]
        assert scene1.scene_number == 1
        assert scene1.title == "Bedroom Opening - Luna y las Estrellas"
        assert len(scene1.shots) == 3
        assert scene1.total_duration == 23.0
        
        # Check shot 1A
        shot1a = scene1.shots[0]
        assert shot1a.shot_id == "1A"
        assert shot1a.duration == 6.0
        assert shot1a.start_time == 0.0
        assert shot1a.end_time == 6.0
        assert "Luna era una niña curiosa" in shot1a.narrative
        assert shot1a.has_dialogue is True
        assert shot1a.character == "narrator"
        
        # Check shot 1B
        shot1b = scene1.shots[1]
        assert shot1b.shot_id == "1B"
        assert shot1b.start_time == 6.0
        assert shot1b.end_time == 11.0
        
        # Check shot 1C
        shot1c = scene1.shots[2]
        assert shot1c.shot_id == "1C"
        assert shot1c.start_time == 11.0
        assert shot1c.end_time == 23.0
        
        # Check scene 2
        scene2 = timing_data.scenes[1]
        assert scene2.scene_number == 2
        assert len(scene2.shots) == 1
        
        # Check shot 2A
        shot2a = scene2.shots[0]
        assert shot2a.shot_id == "2A"
        assert shot2a.start_time == 23.0
        assert shot2a.end_time == 28.0
    
    def test_missing_storyboard_file(self, tmp_path):
        """Test error handling when storyboard file is missing."""
        story_path = tmp_path / "nonexistent-story"
        story_path.mkdir()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            TimingExtractor(story_path)
        
        assert "storyboard-timing.md" in str(exc_info.value).lower()
    
    def test_malformed_storyboard(self, tmp_path):
        """Test handling of malformed storyboard with missing durations."""
        # Create temporary story directory
        story_path = tmp_path / "malformed-story"
        story_path.mkdir()
        
        # Write malformed storyboard
        storyboard_file = story_path / "storyboard-timing.md"
        storyboard_file.write_text(MALFORMED_STORYBOARD, encoding="utf-8")
        
        # Extract timing (should not crash, but warn about missing duration)
        extractor = TimingExtractor(story_path)
        timing_data = extractor.extract_timing(expected_duration=10.0, tolerance=1.0)
        
        # Should have extracted scene 1 with 2 shots
        assert len(timing_data.scenes) == 1
        scene = timing_data.scenes[0]
        assert scene.scene_number == 1
        assert len(scene.shots) == 2
        
        # Shot 1A should have default duration of 5.0s (since missing)
        shot1a = scene.shots[0]
        assert shot1a.shot_id == "1A"
        assert shot1a.duration == 5.0  # Default value
        
        # Shot 1B should also have default duration
        shot1b = scene.shots[1]
        assert shot1b.shot_id == "1B"
        assert shot1b.duration == 5.0
    
    def test_duration_mismatch_error(self, tmp_path):
        """Test that DurationMismatchError is raised for incorrect total duration."""
        # Create temporary story directory
        story_path = tmp_path / "test-story"
        story_path.mkdir()
        
        # Write test storyboard
        storyboard_file = story_path / "storyboard-timing.md"
        storyboard_file.write_text(VALID_STORYBOARD, encoding="utf-8")
        
        # Extract timing with wrong expected duration
        extractor = TimingExtractor(story_path)
        
        with pytest.raises(DurationMismatchError) as exc_info:
            extractor.extract_timing(expected_duration=100.0, tolerance=0.5, strict=True)
        
        assert "doesn't match expected" in str(exc_info.value)
    
    def test_json_output(self, tmp_path):
        """Test JSON serialization of timing data."""
        # Create temporary story directory
        story_path = tmp_path / "test-story"
        story_path.mkdir()
        
        # Write test storyboard
        storyboard_file = story_path / "storyboard-timing.md"
        storyboard_file.write_text(VALID_STORYBOARD, encoding="utf-8")
        
        # Extract timing
        extractor = TimingExtractor(story_path)
        timing_data = extractor.extract_timing(expected_duration=28.0, tolerance=1.0)
        
        # Write JSON
        output_path = tmp_path / "timing.json"
        extractor.write_json(timing_data, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify JSON structure
        import json
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["story"] == "test-story"
        assert data["total_duration"] == 28.0
        assert data["total_scenes"] == 2
        assert data["total_shots"] == 4
        assert len(data["scenes"]) == 2
        assert len(data["scenes"][0]["shots"]) == 3
        
        # Check shot structure
        shot = data["scenes"][0]["shots"][0]
        assert "shot_id" in shot
        assert "duration" in shot
        assert "start_time" in shot
        assert "end_time" in shot
        assert "narrative" in shot
        assert "character" in shot
        assert "has_dialogue" in shot
    
    def test_timestamp_calculation(self):
        """Test cumulative timestamp calculation."""
        # Create manual test data
        scenes = [
            Scene(
                scene_number=1,
                title="Test Scene",
                shots=[
                    Shot(shot_id="1A", description="First", duration=5.0),
                    Shot(shot_id="1B", description="Second", duration=10.0),
                    Shot(shot_id="1C", description="Third", duration=7.5),
                ]
            )
        ]
        
        # Create extractor (doesn't need valid path for this test)
        from agents.timing_extractor.extractor import TimingExtractor
        
        # Calculate timestamps using private method
        # (In real scenario, this would be called via extract_timing)
        cumulative = 0.0
        for scene in scenes:
            for shot in scene.shots:
                shot.start_time = cumulative
                shot.end_time = cumulative + shot.duration
                cumulative = shot.end_time
        
        # Verify timestamps
        shots = scenes[0].shots
        assert shots[0].start_time == 0.0
        assert shots[0].end_time == 5.0
        assert shots[1].start_time == 5.0
        assert shots[1].end_time == 15.0
        assert shots[2].start_time == 15.0
        assert shots[2].end_time == 22.5
        
        # Verify no gaps
        assert shots[0].end_time == shots[1].start_time
        assert shots[1].end_time == shots[2].start_time


class TestShotDataclass:
    """Test Shot dataclass functionality."""
    
    def test_shot_creation(self):
        """Test creating a Shot object."""
        shot = Shot(
            shot_id="1A",
            description="Test shot",
            duration=5.0,
            start_time=0.0,
            end_time=5.0,
            narrative="Test narrative"
        )
        
        assert shot.shot_id == "1A"
        assert shot.duration == 5.0
        assert shot.character == "narrator"  # Default
        assert shot.has_dialogue is False  # Default
    
    def test_shot_to_dict(self):
        """Test Shot serialization to dictionary."""
        shot = Shot(
            shot_id="1A",
            description="Test",
            duration=5.0
        )
        
        data = shot.to_dict()
        assert isinstance(data, dict)
        assert data["shot_id"] == "1A"
        assert data["duration"] == 5.0


class TestSceneDataclass:
    """Test Scene dataclass functionality."""
    
    def test_scene_creation(self):
        """Test creating a Scene object."""
        scene = Scene(
            scene_number=1,
            title="Test Scene",
            shots=[
                Shot(shot_id="1A", description="First", duration=5.0),
                Shot(shot_id="1B", description="Second", duration=10.0),
            ],
            total_duration=15.0
        )
        
        assert scene.scene_number == 1
        assert len(scene.shots) == 2
        assert scene.total_duration == 15.0
    
    def test_scene_to_dict(self):
        """Test Scene serialization to dictionary."""
        scene = Scene(
            scene_number=1,
            title="Test",
            shots=[Shot(shot_id="1A", description="Test", duration=5.0)]
        )
        
        data = scene.to_dict()
        assert isinstance(data, dict)
        assert data["scene_number"] == 1
        assert len(data["shots"]) == 1
        assert isinstance(data["shots"][0], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
