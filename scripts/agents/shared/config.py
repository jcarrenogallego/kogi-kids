"""
Configuration management for audio generation agents.

Loads and validates environment variables from .env file.
Provides typed configuration objects with sensible defaults.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


@dataclass
class Config:
    """
    Audio generation configuration.
    
    Attributes:
        elevenlabs_api_key: ElevenLabs API key (required)
        elevenlabs_max_concurrent: Max concurrent API requests
        suno_api_key: Suno API key (optional, for Q3 2026)
        ffmpeg_path: Path to FFmpeg executable
        audio_sample_rate: Target audio sample rate in Hz
        audio_bit_rate: Target audio bit rate in kbps
        voice_normalization_level: Voice volume normalization level in dB
        music_volume_ratio: Music volume relative to voice (0.0-1.0)
        crossfade_duration: Crossfade duration between scenes in seconds
        max_voice_budget: Maximum budget for voice generation in USD
        warn_voice_threshold: Warning threshold in USD
        max_retries: Maximum retry attempts for failed API calls
        retry_delay: Initial retry delay in seconds (exponential backoff)
        request_timeout: Request timeout in seconds
        stories_path: Path to stories directory
        audio_output_path: Audio output subdirectory name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path
    """
    elevenlabs_api_key: str
    elevenlabs_max_concurrent: int = 5
    suno_api_key: Optional[str] = None
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    audio_sample_rate: int = 44100
    audio_bit_rate: int = 192
    voice_normalization_level: float = -20.0
    music_volume_ratio: float = 0.3
    crossfade_duration: float = 1.0
    max_voice_budget: float = 50.00
    warn_voice_threshold: float = 40.00
    max_retries: int = 3
    retry_delay: float = 2.0
    request_timeout: float = 30.0
    stories_path: Path = field(default_factory=lambda: Path("../stories"))
    audio_output_path: str = "audio"
    log_level: str = "INFO"
    log_file: str = "audio/logs/orchestrator.log"

    @classmethod
    def load(cls, env_file: Optional[Path] = None, require_api_key: bool = True) -> "Config":
        """
        Load configuration from .env file.
        
        Args:
            env_file: Path to .env file. If None, looks for .env in scripts directory.
            require_api_key: If True, raises error if API key missing. Set False for phases that don't need it.
            
        Returns:
            Config object with validated settings.
            
        Raises:
            ConfigError: If required settings are missing or invalid.
            
        Example:
            >>> config = Config.load()
            >>> print(config.elevenlabs_api_key)
        """
        # Determine .env file path
        if env_file is None:
            # Assume we're running from scripts/ directory
            env_file = Path(__file__).parent.parent.parent / ".env"
        
        # Load environment variables
        if env_file.exists():
            load_dotenv(env_file)
        else:
            # Try loading from current directory
            load_dotenv()
        
        # Validate required API key (only if required for this phase)
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        if require_api_key and (not api_key or api_key == "your_key_here"):
            raise ConfigError(
                "ELEVENLABS_API_KEY not configured. "
                "Copy scripts/.env.template to scripts/.env and add your API key."
            )
        
        # Build configuration object
        try:
            # Resolve paths relative to project root
            # config.py is in scripts/agents/shared/, so go up 3 levels
            project_root = Path(__file__).parent.parent.parent.parent
            stories_path_str = os.getenv("STORIES_PATH", "stories")
            stories_path = project_root / stories_path_str if not Path(stories_path_str).is_absolute() else Path(stories_path_str)
            
            config = cls(
                elevenlabs_api_key=api_key,
                elevenlabs_max_concurrent=int(os.getenv("ELEVENLABS_MAX_CONCURRENT", "5")),
                suno_api_key=os.getenv("SUNO_API_KEY") or None,
                ffmpeg_path=os.getenv("FFMPEG_PATH", "ffmpeg"),
                ffprobe_path=os.getenv("FFPROBE_PATH", "ffprobe"),
                audio_sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "44100")),
                audio_bit_rate=int(os.getenv("AUDIO_BIT_RATE", "192")),
                voice_normalization_level=float(os.getenv("VOICE_NORMALIZATION_LEVEL", "-20.0")),
                music_volume_ratio=float(os.getenv("MUSIC_VOLUME_RATIO", "0.3")),
                crossfade_duration=float(os.getenv("CROSSFADE_DURATION", "1.0")),
                max_voice_budget=float(os.getenv("MAX_VOICE_BUDGET", "50.00")),
                warn_voice_threshold=float(os.getenv("WARN_VOICE_THRESHOLD", "40.00")),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_delay=float(os.getenv("RETRY_DELAY", "2.0")),
                request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30.0")),
                stories_path=stories_path,
                audio_output_path=os.getenv("AUDIO_OUTPUT_PATH", "audio"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "audio/logs/orchestrator.log"),
            )
        except (ValueError, TypeError) as e:
            raise ConfigError(f"Invalid configuration value: {e}")
        
        # Validate configuration
        config.validate()
        
        return config
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ConfigError: If any configuration value is invalid.
        """
        # Validate concurrent limit
        if self.elevenlabs_max_concurrent < 1 or self.elevenlabs_max_concurrent > 20:
            raise ConfigError(
                f"ELEVENLABS_MAX_CONCURRENT must be between 1 and 20, got {self.elevenlabs_max_concurrent}"
            )
        
        # Validate audio settings
        if self.audio_sample_rate not in [22050, 44100, 48000]:
            raise ConfigError(
                f"AUDIO_SAMPLE_RATE must be 22050, 44100, or 48000, got {self.audio_sample_rate}"
            )
        
        if self.audio_bit_rate < 64 or self.audio_bit_rate > 320:
            raise ConfigError(
                f"AUDIO_BIT_RATE must be between 64 and 320, got {self.audio_bit_rate}"
            )
        
        # Validate volume settings
        if self.music_volume_ratio < 0.0 or self.music_volume_ratio > 1.0:
            raise ConfigError(
                f"MUSIC_VOLUME_RATIO must be between 0.0 and 1.0, got {self.music_volume_ratio}"
            )
        
        # Validate retry settings
        if self.max_retries < 0 or self.max_retries > 10:
            raise ConfigError(
                f"MAX_RETRIES must be between 0 and 10, got {self.max_retries}"
            )
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ConfigError(
                f"LOG_LEVEL must be one of {valid_levels}, got {self.log_level}"
            )
    
    def get_story_audio_path(self, story: str) -> Path:
        """
        Get audio output path for a specific story.
        
        Args:
            story: Story name (e.g., "luna-y-la-estrella-perdida")
            
        Returns:
            Path to story's audio directory.
            
        Example:
            >>> config = Config.load()
            >>> path = config.get_story_audio_path("luna-y-la-estrella-perdida")
            >>> print(path)  # ../stories/luna-y-la-estrella-perdida/audio
        """
        return self.stories_path / story / self.audio_output_path
