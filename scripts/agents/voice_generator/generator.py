"""
Voice Generator Agent - ElevenLabs API Integration.

Generates voice clips for narrator and character dialogues using ElevenLabs API.
Features async batch processing, retry logic, progress tracking, and cost estimation.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from elevenlabs import ElevenLabs, VoiceSettings
from tqdm import tqdm


logger = logging.getLogger(__name__)


# ElevenLabs API pricing (as of 2026)
ELEVENLABS_COST_PER_1000_CHARS = 0.30  # USD


class VoiceGeneratorError(Exception):
    """Raised when voice generation fails."""

    pass


@dataclass
class VoiceClip:
    """Represents a voice clip to be generated."""

    shot_id: str
    character: str
    text: str
    voice_id: str
    voice_settings: Dict[str, any]
    output_path: Path
    start_time: float
    duration: float

    @property
    def char_count(self) -> int:
        """Get character count for cost estimation."""
        return len(self.text)

    @property
    def estimated_cost(self) -> float:
        """Estimate cost in USD."""
        return (self.char_count / 1000.0) * ELEVENLABS_COST_PER_1000_CHARS


@dataclass
class VoiceConfig:
    """Voice configuration for a character."""

    character: str
    voice_id: str
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


class ElevenLabsClient:
    """
    Client for ElevenLabs API using official SDK with retry logic.

    Implements exponential backoff for rate limits and transient errors.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "eleven_multilingual_v2",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key
            model: Model ID to use
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds (exponential backoff)
            timeout: Request timeout in seconds
        """
        self.client = ElevenLabs(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    async def generate_speech(
        self, text: str, voice_id: str, voice_settings: Optional[Dict] = None
    ) -> bytes:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            voice_settings: Voice settings (stability, similarity_boost, etc.)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            VoiceGeneratorError: If generation fails after retries
        """
        # Default voice settings
        if voice_settings is None:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            }

        # Create VoiceSettings object
        settings = VoiceSettings(
            stability=voice_settings.get("stability", 0.5),
            similarity_boost=voice_settings.get("similarity_boost", 0.75),
            style=voice_settings.get("style", 0.0),
            use_speaker_boost=voice_settings.get("use_speaker_boost", True),
        )

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Use official SDK - synchronous call wrapped in async
                audio_generator = await asyncio.to_thread(
                    self.client.text_to_speech.convert,
                    text=text,
                    voice_id=voice_id,
                    model_id=self.model,
                    voice_settings=settings,
                    language_code="es",  # Force Spanish pronunciation
                )

                # Collect audio chunks
                audio_data = b""
                for chunk in audio_generator:
                    audio_data += chunk

                return audio_data

            except Exception as e:
                error_str = str(e)

                # Handle rate limit (429)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise VoiceGeneratorError(
                            f"Rate limit exceeded after {self.max_retries} attempts"
                        )

                # Other errors
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(f"API error: {e}, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise VoiceGeneratorError(
                        f"API error after {self.max_retries} attempts: {e}"
                    )

        raise VoiceGeneratorError(f"Failed after {self.max_retries} attempts")


class VoiceGenerator:
    """
    Batch voice generation orchestrator.

    Manages concurrent voice generation, progress tracking, and resume capability.
    """

    def __init__(
        self,
        client: ElevenLabsClient,
        output_dir: Path,
        max_concurrent: int = 5,
        progress_file: Optional[Path] = None,
    ):
        """
        Initialize voice generator.

        Args:
            client: ElevenLabs client instance
            output_dir: Base output directory for voice clips
            max_concurrent: Maximum concurrent API requests
            progress_file: Path to progress tracking file
        """
        self.client = client
        self.output_dir = Path(output_dir)
        self.max_concurrent = max_concurrent
        self.progress_file = progress_file

        # Create output directories
        self.narration_dir = self.output_dir / "narration"
        self.dialogues_dir = self.output_dir / "dialogues"
        self.narration_dir.mkdir(parents=True, exist_ok=True)
        self.dialogues_dir.mkdir(parents=True, exist_ok=True)

        # Progress tracking
        self.completed: Dict[str, str] = {}  # shot_id -> status
        self.failed: Dict[str, str] = {}  # shot_id -> error
        self.total_cost: float = 0.0

        # Load existing progress
        self._load_progress()

    def _load_progress(self) -> None:
        """Load progress from file if exists."""
        if self.progress_file and self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.completed = data.get("voice_clips", {})
                self.total_cost = data.get("total_cost", 0.0)
                logger.info(
                    f"Loaded progress: {len(self.completed)} clips already generated"
                )
            except Exception as e:
                logger.warning(f"Failed to load progress: {e}")

    def _save_progress(self) -> None:
        """Save current progress to file."""
        if not self.progress_file:
            return

        try:
            # Load full progress data
            if self.progress_file.exists():
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}

            # Update voice clips section
            data["voice_clips"] = self.completed
            data["total_cost"] = self.total_cost

            # Write atomically
            temp_file = self.progress_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.progress_file)

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    async def generate_batch(
        self, clips: List[VoiceClip], skip_existing: bool = True
    ) -> Tuple[int, int, float]:
        """
        Generate batch of voice clips with concurrency control.

        Args:
            clips: List of VoiceClip objects to generate
            skip_existing: If True, skip clips that already exist

        Returns:
            Tuple of (successful_count, failed_count, total_cost)
        """
        # Filter clips
        clips_to_generate = []
        for clip in clips:
            # Skip if already exists and skip_existing is True
            if skip_existing and clip.output_path.exists():
                self.completed[clip.shot_id] = "complete"
                logger.debug(f"Skipping existing clip: {clip.shot_id}")
                continue

            # Skip if already in completed list
            if clip.shot_id in self.completed:
                logger.debug(f"Skipping completed clip: {clip.shot_id}")
                continue

            clips_to_generate.append(clip)

        if not clips_to_generate:
            logger.info("No clips to generate (all already exist or complete)")
            return (len(self.completed), 0, self.total_cost)

        logger.info(
            f"Generating {len(clips_to_generate)} voice clips (max {self.max_concurrent} concurrent)"
        )

        # Calculate total cost
        estimated_cost = sum(clip.estimated_cost for clip in clips_to_generate)
        logger.info(f"Estimated cost: ${estimated_cost:.2f}")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Progress bar
        pbar = tqdm(total=len(clips_to_generate), desc="Generating voices", unit="clip")

        # Generate all clips concurrently
        tasks = [
            self._generate_single(clip, semaphore, pbar) for clip in clips_to_generate
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        pbar.close()

        # Save final progress
        self._save_progress()

        success_count = len([s for s in self.completed.values() if s == "complete"])
        failed_count = len(self.failed)

        logger.info(
            f"Generation complete: {success_count} successful, {failed_count} failed"
        )
        logger.info(f"Total cost: ${self.total_cost:.2f}")

        return (success_count, failed_count, self.total_cost)

    async def _generate_single(
        self, clip: VoiceClip, semaphore: asyncio.Semaphore, pbar: tqdm
    ) -> None:
        """
        Generate a single voice clip.

        Args:
            clip: VoiceClip to generate
            semaphore: Semaphore for concurrency control
            pbar: Progress bar
        """
        async with semaphore:
            try:
                # Generate speech
                audio_data = await self.client.generate_speech(
                    text=clip.text,
                    voice_id=clip.voice_id,
                    voice_settings=clip.voice_settings,
                )

                # Save to file
                clip.output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(clip.output_path, "wb") as f:
                    f.write(audio_data)

                # Update progress
                self.completed[clip.shot_id] = "complete"
                self.total_cost += clip.estimated_cost
                self._save_progress()

                logger.debug(
                    f"Generated: {clip.shot_id} ({clip.char_count} chars, ${clip.estimated_cost:.3f})"
                )

            except Exception as e:
                logger.error(f"Failed to generate {clip.shot_id}: {e}")
                self.failed[clip.shot_id] = str(e)

            finally:
                pbar.update(1)


def load_voice_configs(config_file: Path) -> Dict[str, VoiceConfig]:
    """
    Load voice configurations from JSON file.

    Args:
        config_file: Path to voices.json

    Returns:
        Dictionary mapping character name to VoiceConfig

    Raises:
        VoiceGeneratorError: If config file is invalid
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        configs = {}
        for item in data.get("voices", []):
            config = VoiceConfig(
                character=item["character"],
                voice_id=item["voice_id"],
                stability=item.get("stability", 0.5),
                similarity_boost=item.get("similarity_boost", 0.75),
                style=item.get("style", 0.0),
                use_speaker_boost=item.get("use_speaker_boost", True),
            )
            configs[config.character] = config

        return configs

    except Exception as e:
        raise VoiceGeneratorError(f"Failed to load voice configs: {e}")


def extract_clips_from_timing(
    timing_file: Path, voice_configs: Dict[str, VoiceConfig], output_dir: Path
) -> List[VoiceClip]:
    """
    Extract voice clips from timing.json.

    Args:
        timing_file: Path to timing.json
        voice_configs: Dictionary of character -> VoiceConfig
        output_dir: Base output directory

    Returns:
        List of VoiceClip objects

    Raises:
        VoiceGeneratorError: If timing file is invalid or voices not configured
    """
    try:
        with open(timing_file, "r", encoding="utf-8") as f:
            timing_data = json.load(f)

        clips = []

        for scene in timing_data["scenes"]:
            for shot in scene["shots"]:
                # Skip shots without dialogue
                if not shot.get("has_dialogue", False):
                    continue

                character = shot.get("character", "narrator")
                dialogue = shot.get("dialogue", "").strip()

                if not dialogue:
                    continue

                # Get voice config
                if character not in voice_configs:
                    raise VoiceGeneratorError(
                        f"No voice configured for character: {character}. "
                        f"Add to voices.json"
                    )

                voice_config = voice_configs[character]

                # Determine output path
                if character == "narrator":
                    output_path = output_dir / "narration" / f"{shot['shot_id']}.mp3"
                else:
                    output_path = (
                        output_dir / "dialogues" / f"{character}_{shot['shot_id']}.mp3"
                    )

                clip = VoiceClip(
                    shot_id=shot["shot_id"],
                    character=character,
                    text=dialogue,
                    voice_id=voice_config.voice_id,
                    voice_settings={
                        "stability": voice_config.stability,
                        "similarity_boost": voice_config.similarity_boost,
                        "style": voice_config.style,
                        "use_speaker_boost": voice_config.use_speaker_boost,
                    },
                    output_path=output_path,
                    start_time=shot["start_time"],
                    duration=shot["duration"],
                )

                clips.append(clip)

        logger.info(f"Extracted {len(clips)} voice clips from timing data")
        return clips

    except Exception as e:
        raise VoiceGeneratorError(f"Failed to extract clips from timing: {e}")
