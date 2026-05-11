"""
Tests for Audio Mixer Agent.

Tests FFmpeg operations, music stitching, voice overlay, and normalization.
Uses mocked FFmpeg calls to avoid actual audio processing.
"""
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agents.audio_mixer.mixer import (
    FFmpegMixer,
    AudioSegment,
    MixConfig,
    AudioMixerError,
    load_timing_data,
    create_voice_segments
)


# Fixtures

@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg subprocess calls."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "Duration: 00:00:10.00, start: 0.000000"
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def sample_config():
    """Sample mix configuration."""
    return MixConfig(
        music_level=-18.0,
        voice_level=-3.0,
        crossfade_duration=3.0,
        loudness_target=-14.0
    )


@pytest.fixture
def mixer(sample_config):
    """FFmpegMixer instance."""
    return FFmpegMixer(ffmpeg_path="ffmpeg", config=sample_config, dry_run=False)


@pytest.fixture
def sample_audio_files(tmp_path):
    """Create sample audio files."""
    files = []
    for i in range(3):
        file = tmp_path / f"music_{i}.mp3"
        file.write_text(f"mock audio data {i}")
        files.append(file)
    return files


@pytest.fixture
def timing_data():
    """Sample timing data."""
    return {
        "story": "test-story",
        "total_duration": 20.0,
        "scenes": [
            {
                "shots": [
                    {
                        "shot_id": "1A",
                        "character": "narrator",
                        "has_dialogue": True,
                        "start_time": 0.0,
                        "duration": 5.0
                    },
                    {
                        "shot_id": "1B",
                        "character": "Luna",
                        "has_dialogue": True,
                        "start_time": 5.0,
                        "duration": 3.0
                    }
                ]
            }
        ]
    }


# AudioSegment Tests

def test_audio_segment_validation(tmp_path):
    """Test audio segment validation."""
    # Valid segment
    audio_file = tmp_path / "test.mp3"
    audio_file.write_text("mock")
    
    segment = AudioSegment(
        file_path=audio_file,
        start_time=0.0,
        duration=5.0
    )
    
    segment.validate()  # Should not raise
    
    # Invalid: file doesn't exist
    invalid_segment = AudioSegment(
        file_path=tmp_path / "nonexistent.mp3",
        start_time=0.0,
        duration=5.0
    )
    
    with pytest.raises(AudioMixerError, match="Audio file not found"):
        invalid_segment.validate()
    
    # Invalid: negative start time
    invalid_segment = AudioSegment(
        file_path=audio_file,
        start_time=-1.0,
        duration=5.0
    )
    
    with pytest.raises(AudioMixerError, match="Invalid start time"):
        invalid_segment.validate()
    
    # Invalid: zero duration
    invalid_segment = AudioSegment(
        file_path=audio_file,
        start_time=0.0,
        duration=0.0
    )
    
    with pytest.raises(AudioMixerError, match="Invalid duration"):
        invalid_segment.validate()


# FFmpegMixer Tests

def test_mixer_initialization():
    """Test mixer initialization."""
    config = MixConfig()
    mixer = FFmpegMixer(ffmpeg_path="ffmpeg", config=config, dry_run=True)
    
    assert mixer.ffmpeg_path == "ffmpeg"
    assert mixer.config == config
    assert mixer.dry_run is True


def test_mixer_validate_ffmpeg_not_found():
    """Test error when FFmpeg not found."""
    with pytest.raises(AudioMixerError, match="FFmpeg not accessible"):
        FFmpegMixer(ffmpeg_path="nonexistent_ffmpeg", dry_run=False)


def test_mixer_get_duration(mixer, mock_ffmpeg, tmp_path):
    """Test getting audio duration."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_text("mock")
    
    # Mock stderr with duration
    mock_ffmpeg.return_value.stderr = "Duration: 00:03:25.50, start: 0.000000"
    
    duration = mixer.get_duration(audio_file)
    
    assert duration == 205.5  # 3*60 + 25.5
    mock_ffmpeg.assert_called_once()


def test_mixer_stitch_single_file(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test stitching single music file."""
    output = tmp_path / "output.mp3"
    
    mixer.stitch_music([sample_audio_files[0]], output)
    
    # Should call FFmpeg with volume adjustment
    mock_ffmpeg.assert_called_once()
    call_args = mock_ffmpeg.call_args[0][0]
    
    assert str(sample_audio_files[0]) in call_args
    assert "-af" in call_args
    assert "volume=-18.0dB" in call_args


def test_mixer_stitch_multiple_files(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test stitching multiple music files with crossfade."""
    output = tmp_path / "output.mp3"
    
    mixer.stitch_music(sample_audio_files, output, crossfade_duration=3.0)
    
    # Should call FFmpeg with crossfade filter
    mock_ffmpeg.assert_called_once()
    call_args = mock_ffmpeg.call_args[0][0]
    
    assert "-filter_complex" in call_args
    # Find filter_complex argument
    filter_idx = call_args.index("-filter_complex")
    filter_str = call_args[filter_idx + 1]
    
    assert "acrossfade=d=3" in filter_str
    assert "volume=-18.0dB" in filter_str


def test_mixer_stitch_missing_files(mixer, tmp_path):
    """Test error when music files are missing."""
    nonexistent = tmp_path / "nonexistent.mp3"
    output = tmp_path / "output.mp3"
    
    with pytest.raises(AudioMixerError, match="Music file not found"):
        mixer.stitch_music([nonexistent], output)


def test_mixer_overlay_voices_no_voices(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test overlay with no voice segments."""
    output = tmp_path / "output.mp3"
    
    mixer.overlay_voices(sample_audio_files[0], [], output)
    
    # Should just copy music
    mock_ffmpeg.assert_called_once()
    call_args = mock_ffmpeg.call_args[0][0]
    
    assert "-c" in call_args
    assert "copy" in call_args


def test_mixer_overlay_voices_with_segments(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test overlaying voice segments on music."""
    # Create voice files
    voice1 = tmp_path / "voice1.mp3"
    voice2 = tmp_path / "voice2.mp3"
    voice1.write_text("voice 1")
    voice2.write_text("voice 2")
    
    segments = [
        AudioSegment(voice1, start_time=2.0, duration=3.0),
        AudioSegment(voice2, start_time=6.0, duration=4.0)
    ]
    
    output = tmp_path / "output.mp3"
    
    mixer.overlay_voices(sample_audio_files[0], segments, output)
    
    # Should call FFmpeg with complex filter
    mock_ffmpeg.assert_called_once()
    call_args = mock_ffmpeg.call_args[0][0]
    
    assert "-filter_complex" in call_args
    filter_idx = call_args.index("-filter_complex")
    filter_str = call_args[filter_idx + 1]
    
    # Check for adelay filters
    assert "adelay=2000" in filter_str  # 2.0s * 1000
    assert "adelay=6000" in filter_str  # 6.0s * 1000
    assert "amix" in filter_str


def test_mixer_overlay_invalid_segment(mixer, sample_audio_files, tmp_path):
    """Test error when voice segment is invalid."""
    nonexistent = tmp_path / "nonexistent.mp3"
    
    segments = [
        AudioSegment(nonexistent, start_time=0.0, duration=5.0)
    ]
    
    output = tmp_path / "output.mp3"
    
    with pytest.raises(AudioMixerError):
        mixer.overlay_voices(sample_audio_files[0], segments, output)


def test_mixer_normalize_loudness(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test loudness normalization."""
    output = tmp_path / "output.mp3"
    
    mixer.normalize_loudness(sample_audio_files[0], output, target_lufs=-14.0)
    
    # Should call FFmpeg with loudnorm filter
    mock_ffmpeg.assert_called_once()
    call_args = mock_ffmpeg.call_args[0][0]
    
    assert "-af" in call_args
    filter_idx = call_args.index("-af")
    filter_str = call_args[filter_idx + 1]
    
    assert "loudnorm" in filter_str
    assert "I=-14.0" in filter_str


def test_mixer_validate_duration(mixer, mock_ffmpeg, sample_audio_files):
    """Test duration validation."""
    mock_ffmpeg.return_value.stderr = "Duration: 00:00:10.00, start: 0.000000"
    
    # Within tolerance
    result = mixer.validate_duration(sample_audio_files[0], expected_duration=10.0, tolerance=0.5)
    assert result is True
    
    # Outside tolerance
    result = mixer.validate_duration(sample_audio_files[0], expected_duration=15.0, tolerance=0.5)
    assert result is False


def test_mixer_dry_run_mode(sample_config, tmp_path):
    """Test dry run mode doesn't execute commands."""
    mixer = FFmpegMixer(ffmpeg_path="ffmpeg", config=sample_config, dry_run=True)
    
    output = tmp_path / "output.mp3"
    
    # Create mock file
    music = tmp_path / "music.mp3"
    music.write_text("mock")
    
    # Should not raise error (dry run)
    mixer.stitch_music([music], output)
    
    # Output should not exist
    assert not output.exists()


def test_mixer_ffmpeg_command_failure(mixer, mock_ffmpeg, sample_audio_files, tmp_path):
    """Test error handling when FFmpeg command fails."""
    mock_ffmpeg.return_value.returncode = 1
    mock_ffmpeg.return_value.stderr = "FFmpeg error: invalid codec"
    
    output = tmp_path / "output.mp3"
    
    with pytest.raises(AudioMixerError, match="FFmpeg failed with code 1"):
        mixer.stitch_music(sample_audio_files, output)


def test_mixer_ffmpeg_timeout(mixer, sample_audio_files, tmp_path):
    """Test error handling when FFmpeg times out."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 300)):
        output = tmp_path / "output.mp3"
        
        with pytest.raises(AudioMixerError, match="FFmpeg command timed out"):
            mixer.stitch_music(sample_audio_files, output)


# Utility Function Tests

def test_load_timing_data(tmp_path, timing_data):
    """Test loading timing data."""
    timing_file = tmp_path / "timing.json"
    
    import json
    with open(timing_file, "w") as f:
        json.dump(timing_data, f)
    
    total_duration, shots = load_timing_data(timing_file)
    
    assert total_duration == 20.0
    assert len(shots) == 2
    assert shots[0]["shot_id"] == "1A"
    assert shots[1]["shot_id"] == "1B"


def test_create_voice_segments(tmp_path, timing_data):
    """Test creating voice segments from timing data."""
    # Create voice files
    audio_dir = tmp_path
    narration_dir = audio_dir / "narration"
    dialogues_dir = audio_dir / "dialogues"
    narration_dir.mkdir()
    dialogues_dir.mkdir()
    
    (narration_dir / "1A.mp3").write_text("narrator")
    (dialogues_dir / "Luna_1B.mp3").write_text("luna")
    
    shots = []
    for scene in timing_data["scenes"]:
        shots.extend(scene["shots"])
    
    segments = create_voice_segments(shots, audio_dir)
    
    assert len(segments) == 2
    assert segments[0].file_path.name == "1A.mp3"
    assert segments[0].start_time == 0.0
    assert segments[1].file_path.name == "Luna_1B.mp3"
    assert segments[1].start_time == 5.0


def test_create_voice_segments_missing_files(tmp_path, timing_data):
    """Test warning when voice files are missing."""
    shots = []
    for scene in timing_data["scenes"]:
        shots.extend(scene["shots"])
    
    # No voice files created
    segments = create_voice_segments(shots, tmp_path)
    
    # Should return empty list (files don't exist)
    assert len(segments) == 0
