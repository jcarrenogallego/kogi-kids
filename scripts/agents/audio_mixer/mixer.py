"""
Audio Mixer Agent - FFmpeg Integration.

Mixes music, voice clips, and sound effects into final audio output.
Features:
- Music stitching with crossfades
- Voice overlay with precise timing
- Loudness normalization
- Duration validation
"""

import subprocess
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class AudioMixerError(Exception):
    """Raised when audio mixing fails."""

    pass


@dataclass
class AudioSegment:
    """Represents an audio segment in the mix."""

    file_path: Path
    start_time: float
    duration: float
    volume: float = 1.0  # Relative volume (0.0 to 1.0)

    def validate(self) -> None:
        """Validate segment data."""
        if not self.file_path.exists():
            raise AudioMixerError(f"Audio file not found: {self.file_path}")
        if self.start_time < 0:
            raise AudioMixerError(f"Invalid start time: {self.start_time}")
        if self.duration <= 0:
            raise AudioMixerError(f"Invalid duration: {self.duration}")


@dataclass
class MixConfig:
    """Configuration for audio mixing."""

    music_level: float = -20.0  # dB (background music level)
    voice_level: float = -6.0  # dB (voice level with headroom)
    crossfade_duration: float = 3.0  # seconds
    loudness_target: float = -14.0  # LUFS
    sample_rate: int = 44100  # Hz
    bit_rate: int = 192  # kbps


class FFmpegMixer:
    """
    FFmpeg-based audio mixing engine.

    Provides high-level interface for complex audio operations.
    """

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        config: Optional[MixConfig] = None,
        dry_run: bool = False,
    ):
        """
        Initialize FFmpeg mixer.

        Args:
            ffmpeg_path: Path to FFmpeg executable
            config: Mix configuration
            dry_run: If True, only print commands without executing
        """
        self.ffmpeg_path = ffmpeg_path
        self.config = config or MixConfig()
        self.dry_run = dry_run

        # Validate FFmpeg installation
        if not dry_run:
            self._validate_ffmpeg()

    def _validate_ffmpeg(self) -> None:
        """Validate FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise AudioMixerError(f"FFmpeg not found: {self.ffmpeg_path}")
            logger.debug(f"FFmpeg version: {result.stdout.splitlines()[0]}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise AudioMixerError(f"FFmpeg not accessible: {e}")

    def _run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run FFmpeg command.

        Args:
            args: Command arguments (without ffmpeg executable)

        Returns:
            CompletedProcess result

        Raises:
            AudioMixerError: If command fails
        """
        cmd = [self.ffmpeg_path] + args

        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        logger.debug(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg stderr: {result.stderr}")
                raise AudioMixerError(f"FFmpeg failed with code {result.returncode}")

            return result

        except subprocess.TimeoutExpired:
            raise AudioMixerError("FFmpeg command timed out")
        except Exception as e:
            raise AudioMixerError(f"FFmpeg execution failed: {e}")

    def get_duration(self, audio_file: Path) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            audio_file: Path to audio file

        Returns:
            Duration in seconds
        """
        args = ["-i", str(audio_file), "-f", "null", "-"]

        result = self._run_command(args)

        # Parse duration from stderr
        for line in result.stderr.splitlines():
            if "Duration:" in line:
                # Format: Duration: 00:03:09.00
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = time_str.split(":")
                duration = int(h) * 3600 + int(m) * 60 + float(s)
                return duration

        raise AudioMixerError(f"Could not determine duration of {audio_file}")

    def stitch_music(
        self,
        music_files: List[Path],
        output_file: Path,
        crossfade_duration: Optional[float] = None,
    ) -> None:
        """
        Stitch multiple music files with crossfades.

        Args:
            music_files: List of music file paths (in order)
            output_file: Output file path
            crossfade_duration: Crossfade duration in seconds (uses config default if None)
        """
        if not music_files:
            raise AudioMixerError("No music files provided")

        # Validate all files exist
        for f in music_files:
            if not f.exists():
                raise AudioMixerError(f"Music file not found: {f}")

        crossfade = crossfade_duration or self.config.crossfade_duration

        logger.info(
            f"Stitching {len(music_files)} music files with {crossfade}s crossfades"
        )

        if len(music_files) == 1:
            # Single file, just copy with normalization
            args = [
                "-i",
                str(music_files[0]),
                "-af",
                f"volume={self.config.music_level}dB",
                "-ar",
                str(self.config.sample_rate),
                "-b:a",
                f"{self.config.bit_rate}k",
                "-y",
                str(output_file),
            ]
            self._run_command(args)
            return

        # Multiple files: build crossfade filter chain
        # Format: [0][1]acrossfade=d=3[a01];[a01][2]acrossfade=d=3[a02];...

        inputs = []
        for f in music_files:
            inputs.extend(["-i", str(f)])

        # Build filter chain
        filter_chain = []
        current_label = "0"

        for i in range(1, len(music_files)):
            next_label = f"a{i}"
            filter_chain.append(
                f"[{current_label}][{i}]acrossfade=d={crossfade}:c1=tri:c2=tri[{next_label}]"
            )
            current_label = next_label

        # Add volume adjustment to final output
        filter_chain.append(f"[{current_label}]volume={self.config.music_level}dB")

        filter_str = ";".join(filter_chain)

        args = inputs + [
            "-filter_complex",
            filter_str,
            "-ar",
            str(self.config.sample_rate),
            "-b:a",
            f"{self.config.bit_rate}k",
            "-y",
            str(output_file),
        ]

        self._run_command(args)
        logger.info(f"Music stitched to: {output_file}")

    def overlay_voices(
        self,
        background_music: Path,
        voice_segments: List[AudioSegment],
        output_file: Path,
    ) -> None:
        """
        Overlay voice clips on background music with timing.

        Args:
            background_music: Path to background music track
            voice_segments: List of voice segments with timing
            output_file: Output file path
        """
        if not background_music.exists():
            raise AudioMixerError(f"Background music not found: {background_music}")

        # Validate all segments
        for segment in voice_segments:
            segment.validate()

        logger.info(f"Overlaying {len(voice_segments)} voice clips on music")

        if not voice_segments:
            # No voices, just copy music
            args = ["-i", str(background_music), "-c", "copy", "-y", str(output_file)]
            self._run_command(args)
            return

        # Build complex filter with adelay for timing
        # Format:
        # [1]adelay=1000|1000,volume=0dB[v0];
        # [2]adelay=5000|5000,volume=0dB[v1];
        # [0][v0][v1]amix=inputs=3:duration=longest:weights=1 0.8 0.8

        inputs = ["-i", str(background_music)]
        for segment in voice_segments:
            inputs.extend(["-i", str(segment.file_path)])

        # Build filter chain
        filter_parts = []

        # Process each voice with trim (to expected duration), delay and volume
        for i, segment in enumerate(voice_segments, start=1):
            delay_ms = int(segment.start_time * 1000)
            duration_sec = segment.duration
            volume_db = self.config.voice_level
            # Trim audio to expected duration, then delay to start position
            filter_parts.append(
                f"[{i}]atrim=0:{duration_sec},adelay={delay_ms}|{delay_ms},volume={volume_db}dB[v{i - 1}]"
            )

        # Mix all streams
        mix_inputs = ["[0]"] + [f"[v{i}]" for i in range(len(voice_segments))]
        num_inputs = len(voice_segments) + 1

        # Build weights: music at 1.0, voices at configured level
        weights = [str(1.0)] + [str(1.0)] * len(voice_segments)

        filter_parts.append(
            f"{''.join(mix_inputs)}amix=inputs={num_inputs}:duration=longest:weights={' '.join(weights)}"
        )

        filter_str = ";".join(filter_parts)

        args = inputs + [
            "-filter_complex",
            filter_str,
            "-ar",
            str(self.config.sample_rate),
            "-b:a",
            f"{self.config.bit_rate}k",
            "-y",
            str(output_file),
        ]

        self._run_command(args)
        logger.info(f"Voices overlaid to: {output_file}")

    def normalize_loudness(
        self, input_file: Path, output_file: Path, target_lufs: Optional[float] = None
    ) -> None:
        """
        Normalize audio loudness to target LUFS.

        Args:
            input_file: Input audio file
            output_file: Output audio file
            target_lufs: Target loudness in LUFS (uses config default if None)
        """
        if not input_file.exists():
            raise AudioMixerError(f"Input file not found: {input_file}")

        target = target_lufs or self.config.loudness_target

        logger.info(f"Normalizing loudness to {target} LUFS")

        # Two-pass loudnorm filter
        args = [
            "-i",
            str(input_file),
            "-af",
            f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=summary",
            "-ar",
            str(self.config.sample_rate),
            "-b:a",
            f"{self.config.bit_rate}k",
            "-y",
            str(output_file),
        ]

        self._run_command(args)
        logger.info(f"Normalized audio saved to: {output_file}")

    def validate_duration(
        self, audio_file: Path, expected_duration: float, tolerance: float = 0.5
    ) -> bool:
        """
        Validate audio duration matches expected value.

        Args:
            audio_file: Audio file to validate
            expected_duration: Expected duration in seconds
            tolerance: Acceptable difference in seconds

        Returns:
            True if duration is within tolerance
        """
        actual_duration = self.get_duration(audio_file)
        difference = abs(actual_duration - expected_duration)

        if difference <= tolerance:
            logger.info(
                f"Duration valid: {actual_duration:.2f}s (expected {expected_duration:.2f}s)"
            )
            return True
        else:
            logger.warning(
                f"Duration mismatch: {actual_duration:.2f}s vs {expected_duration:.2f}s "
                f"(difference: {difference:.2f}s, tolerance: {tolerance}s)"
            )
            return False


def load_timing_data(timing_file: Path) -> Tuple[float, List[Dict]]:
    """
    Load timing data from timing.json.

    Args:
        timing_file: Path to timing.json

    Returns:
        Tuple of (total_duration, shots_list)
    """
    try:
        with open(timing_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        total_duration = data["total_duration"]

        shots = []
        for scene in data["scenes"]:
            shots.extend(scene["shots"])

        return (total_duration, shots)

    except Exception as e:
        raise AudioMixerError(f"Failed to load timing data: {e}")


def create_voice_segments(shots: List[Dict], audio_dir: Path) -> List[AudioSegment]:
    """
    Create AudioSegment objects from timing data.

    Args:
        shots: List of shot dictionaries from timing.json
        audio_dir: Base audio directory

    Returns:
        List of AudioSegment objects for voice clips
    """
    segments = []

    for shot in shots:
        if not shot.get("has_dialogue", False):
            continue

        character = shot.get("character", "narrator")
        shot_id = shot["shot_id"]

        # Determine voice file path
        if character == "narrator":
            voice_file = audio_dir / "narration" / f"{shot_id}.mp3"
        else:
            voice_file = audio_dir / "dialogues" / f"{character}_{shot_id}.mp3"

        # Skip if file doesn't exist (will be caught by validation)
        if not voice_file.exists():
            logger.warning(f"Voice file not found: {voice_file}")
            continue

        segment = AudioSegment(
            file_path=voice_file,
            start_time=shot["start_time"],
            duration=shot["duration"],
        )
        segments.append(segment)

    return segments
