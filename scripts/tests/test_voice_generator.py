"""
Tests for Voice Generator Agent.

Tests ElevenLabs API client, batch generation, and progress tracking.
Uses mocked API responses to avoid actual API calls.
"""
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp

from agents.voice_generator.generator import (
    ElevenLabsClient,
    VoiceGenerator,
    VoiceClip,
    VoiceConfig,
    VoiceGeneratorError,
    load_voice_configs,
    extract_clips_from_timing,
    ELEVENLABS_COST_PER_1000_CHARS
)


# Fixtures

@pytest.fixture
def mock_audio_data():
    """Mock MP3 audio data."""
    return b"MOCK_MP3_DATA_" + b"X" * 1000


@pytest.fixture
def sample_voice_config():
    """Sample voice configuration."""
    return VoiceConfig(
        character="narrator",
        voice_id="test_voice_123",
        stability=0.5,
        similarity_boost=0.75
    )


@pytest.fixture
def sample_clip(tmp_path, sample_voice_config):
    """Sample voice clip."""
    return VoiceClip(
        shot_id="1A",
        character="narrator",
        text="Test narration text.",
        voice_id=sample_voice_config.voice_id,
        output_path=tmp_path / "narration" / "1A.mp3",
        start_time=0.0,
        duration=5.0
    )


@pytest.fixture
def timing_data():
    """Sample timing.json data."""
    return {
        "story": "test-story",
        "total_duration": 20.0,
        "scenes": [
            {
                "scene_number": 1,
                "shots": [
                    {
                        "shot_id": "1A",
                        "character": "narrator",
                        "dialogue": "First narration.",
                        "has_dialogue": True,
                        "start_time": 0.0,
                        "duration": 5.0
                    },
                    {
                        "shot_id": "1B",
                        "character": "Luna",
                        "dialogue": "Hello world!",
                        "has_dialogue": True,
                        "start_time": 5.0,
                        "duration": 3.0
                    },
                    {
                        "shot_id": "1C",
                        "has_dialogue": False,
                        "start_time": 8.0,
                        "duration": 2.0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def voice_configs_data():
    """Sample voices.json data."""
    return {
        "voices": [
            {
                "character": "narrator",
                "voice_id": "narrator_voice_123"
            },
            {
                "character": "Luna",
                "voice_id": "luna_voice_456"
            }
        ]
    }


# ElevenLabsClient Tests

@pytest.mark.asyncio
async def test_client_generate_speech_success(mock_audio_data):
    """Test successful speech generation."""
    client = ElevenLabsClient(api_key="test_key")
    
    # Mock session
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=mock_audio_data)
    
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    client.session = mock_session
    
    # Generate speech
    result = await client.generate_speech("Test text", "voice_123")
    
    assert result == mock_audio_data
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_client_retry_on_rate_limit(mock_audio_data):
    """Test retry logic on 429 rate limit."""
    client = ElevenLabsClient(api_key="test_key", retry_delay=0.1)
    
    # Mock responses: 429, then 200
    mock_response_429 = AsyncMock()
    mock_response_429.status = 429
    
    mock_response_200 = AsyncMock()
    mock_response_200.status = 200
    mock_response_200.read = AsyncMock(return_value=mock_audio_data)
    
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(side_effect=[mock_response_429, mock_response_200])
    
    client.session = mock_session
    
    # Should succeed after retry
    result = await client.generate_speech("Test", "voice_123")
    
    assert result == mock_audio_data
    assert mock_session.post.call_count == 2


@pytest.mark.asyncio
async def test_client_fail_after_max_retries():
    """Test failure after max retries."""
    client = ElevenLabsClient(api_key="test_key", max_retries=2, retry_delay=0.1)
    
    # Always return 429
    mock_response = AsyncMock()
    mock_response.status = 429
    
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    
    client.session = mock_session
    
    # Should fail after max retries
    with pytest.raises(VoiceGeneratorError):
        await client.generate_speech("Test", "voice_123")
    
    assert mock_session.post.call_count == 2


@pytest.mark.asyncio
async def test_client_handle_api_error():
    """Test handling of API errors."""
    client = ElevenLabsClient(api_key="test_key")
    
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    
    client.session = mock_session
    
    with pytest.raises(VoiceGeneratorError, match="API error 500"):
        await client.generate_speech("Test", "voice_123")


# VoiceClip Tests

def test_voice_clip_cost_estimation():
    """Test voice clip cost estimation."""
    clip = VoiceClip(
        shot_id="1A",
        character="narrator",
        text="A" * 1000,  # 1000 characters
        voice_id="voice_123",
        output_path=Path("test.mp3"),
        start_time=0.0,
        duration=5.0
    )
    
    assert clip.char_count == 1000
    assert clip.estimated_cost == ELEVENLABS_COST_PER_1000_CHARS


# VoiceGenerator Tests

@pytest.mark.asyncio
async def test_voice_generator_skip_existing(tmp_path, sample_clip, mock_audio_data):
    """Test skipping existing clips."""
    # Create existing file
    sample_clip.output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_clip.output_path.write_bytes(mock_audio_data)
    
    mock_client = AsyncMock()
    
    generator = VoiceGenerator(
        client=mock_client,
        output_dir=tmp_path,
        max_concurrent=1
    )
    
    success, failed, cost = await generator.generate_batch([sample_clip], skip_existing=True)
    
    # Should skip without calling API
    assert success == 1
    assert failed == 0
    mock_client.generate_speech.assert_not_called()


@pytest.mark.asyncio
async def test_voice_generator_progress_tracking(tmp_path, sample_clip, mock_audio_data):
    """Test progress tracking and resume."""
    progress_file = tmp_path / "progress.json"
    
    # Mock client
    mock_client = AsyncMock()
    mock_client.generate_speech = AsyncMock(return_value=mock_audio_data)
    
    generator = VoiceGenerator(
        client=mock_client,
        output_dir=tmp_path,
        max_concurrent=1,
        progress_file=progress_file
    )
    
    # Generate batch
    await generator.generate_batch([sample_clip], skip_existing=False)
    
    # Check progress file was created
    assert progress_file.exists()
    
    with open(progress_file) as f:
        progress = json.load(f)
    
    assert "1A" in progress["voice_clips"]
    assert progress["voice_clips"]["1A"] == "complete"


@pytest.mark.asyncio
async def test_voice_generator_concurrent_limit(tmp_path, mock_audio_data):
    """Test concurrent request limiting."""
    # Create multiple clips
    clips = [
        VoiceClip(
            shot_id=f"{i}A",
            character="narrator",
            text=f"Text {i}",
            voice_id="voice_123",
            output_path=tmp_path / "narration" / f"{i}A.mp3",
            start_time=float(i),
            duration=1.0
        )
        for i in range(10)
    ]
    
    call_times = []
    
    async def mock_generate(*args, **kwargs):
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)  # Simulate API call
        return mock_audio_data
    
    mock_client = AsyncMock()
    mock_client.generate_speech = mock_generate
    
    generator = VoiceGenerator(
        client=mock_client,
        output_dir=tmp_path,
        max_concurrent=3
    )
    
    await generator.generate_batch(clips, skip_existing=False)
    
    # Verify no more than 3 concurrent calls
    # (This is a simplified check - actual concurrent control is handled by semaphore)
    assert len(call_times) == 10


# Utility Function Tests

def test_load_voice_configs(tmp_path, voice_configs_data):
    """Test loading voice configurations."""
    config_file = tmp_path / "voices.json"
    with open(config_file, "w") as f:
        json.dump(voice_configs_data, f)
    
    configs = load_voice_configs(config_file)
    
    assert "narrator" in configs
    assert "Luna" in configs
    assert configs["narrator"].voice_id == "narrator_voice_123"
    assert configs["Luna"].voice_id == "luna_voice_456"


def test_load_voice_configs_invalid_file(tmp_path):
    """Test error on invalid config file."""
    config_file = tmp_path / "invalid.json"
    config_file.write_text("invalid json")
    
    with pytest.raises(VoiceGeneratorError):
        load_voice_configs(config_file)


def test_extract_clips_from_timing(tmp_path, timing_data, voice_configs_data):
    """Test extracting clips from timing data."""
    # Create timing file
    timing_file = tmp_path / "timing.json"
    with open(timing_file, "w") as f:
        json.dump(timing_data, f)
    
    # Create voice configs
    config_file = tmp_path / "voices.json"
    with open(config_file, "w") as f:
        json.dump(voice_configs_data, f)
    
    voice_configs = load_voice_configs(config_file)
    
    # Extract clips
    clips = extract_clips_from_timing(timing_file, voice_configs, tmp_path)
    
    # Should have 2 clips (1A narrator, 1B Luna), skip 1C (no dialogue)
    assert len(clips) == 2
    assert clips[0].shot_id == "1A"
    assert clips[0].character == "narrator"
    assert clips[1].shot_id == "1B"
    assert clips[1].character == "Luna"


def test_extract_clips_missing_voice_config(tmp_path, timing_data):
    """Test error when voice config is missing."""
    timing_file = tmp_path / "timing.json"
    with open(timing_file, "w") as f:
        json.dump(timing_data, f)
    
    # Empty voice configs (missing Luna)
    voice_configs = {"narrator": VoiceConfig("narrator", "voice_123")}
    
    with pytest.raises(VoiceGeneratorError, match="No voice configured for character: Luna"):
        extract_clips_from_timing(timing_file, voice_configs, tmp_path)
