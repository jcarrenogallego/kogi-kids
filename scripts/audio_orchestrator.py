#!/usr/bin/env python3
"""
Audio Orchestrator - Main CLI for Audio Generation Pipeline.

Orchestrates the complete audio generation workflow:
1. Timing extraction from storyboard markdown files
2. Music prompt generation and validation
3. Voice generation via ElevenLabs API
4. Audio mixing (music + voices + effects)
5. Quality validation and reporting

Usage:
    # Full pipeline (all phases)
    python audio_orchestrator.py --story luna-y-la-estrella-perdida

    # Specific phases only
    python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases timing,voices

    # Resume after failure
    python audio_orchestrator.py --story luna-y-la-estrella-perdida --resume

    # Dry run (show plan without executing)
    python audio_orchestrator.py --story luna-y-la-estrella-perdida --dry-run

    # Force regenerate (ignore existing progress)
    python audio_orchestrator.py --story luna-y-la-estrella-perdida --force
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from typing import List, Optional

# Add agents package to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.shared.config import Config, ConfigError
from agents.shared.state_manager import StateManager, StateError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Phase names and execution order
PHASES = ["timing", "music", "voices", "mix", "validate"]
PHASE_DESCRIPTIONS = {
    "timing": "Extract timing and dialogue from storyboard",
    "music": "Generate music prompts and validate downloads",
    "voices": "Generate character voices via ElevenLabs API",
    "mix": "Mix music, voices, and sound effects",
    "validate": "Validate audio quality and synchronization",
}


class AudioOrchestrator:
    """
    Orchestrates the audio generation pipeline.

    Manages phase execution, state tracking, and error handling.
    """

    def __init__(
        self, config: Config, state_manager: StateManager, dry_run: bool = False
    ):
        """
        Initialize orchestrator.

        Args:
            config: Configuration object
            state_manager: State manager instance
            dry_run: If True, only show what would be executed
        """
        self.config = config
        self.state_manager = state_manager
        self.dry_run = dry_run

    def run(self, phases: List[str]) -> None:
        """
        Execute specified phases.

        Args:
            phases: List of phase names to execute (or ["all"] for all phases)

        Raises:
            ValueError: If phase name is invalid
        """
        # Validate phase names
        if "all" in phases:
            phases = PHASES
        else:
            invalid = [p for p in phases if p not in PHASES]
            if invalid:
                raise ValueError(f"Invalid phases: {invalid}. Valid phases: {PHASES}")

        logger.info(
            f"Starting audio orchestration for story: {self.state_manager.state.story}"
        )
        logger.info(f"Phases to execute: {', '.join(phases)}")

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        # Execute phases in order
        for phase in PHASES:
            if phase not in phases:
                logger.debug(f"Skipping phase: {phase}")
                continue

            # Check if phase is already complete
            current_status = self.state_manager.state.phases.get(phase, "pending")
            if current_status == "complete":
                logger.info(f"Phase '{phase}' already complete, skipping")
                continue

            try:
                self._execute_phase(phase)
            except Exception as e:
                logger.error(f"Phase '{phase}' failed: {e}")
                self.state_manager.update_phase(phase, "failed", error=str(e))
                self.state_manager.save()
                raise

        logger.info("Audio orchestration complete!")
        self._print_summary()

    def _execute_phase(self, phase: str) -> None:
        """
        Execute a single phase.

        Args:
            phase: Phase name
        """
        logger.info(f"Executing phase: {phase} - {PHASE_DESCRIPTIONS[phase]}")

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute {phase} phase")
            return

        # Update state
        self.state_manager.update_phase(phase, "in_progress")
        self.state_manager.save()

        # Execute phase-specific logic
        if phase == "timing":
            self._execute_timing()
        elif phase == "music":
            self._execute_music()
        elif phase == "voices":
            self._execute_voices()
        elif phase == "mix":
            self._execute_mix()
        elif phase == "validate":
            self._execute_validate()

        # Mark complete
        self.state_manager.update_phase(phase, "complete")
        self.state_manager.save()
        logger.info(f"Phase '{phase}' completed successfully")

    def _execute_timing(self) -> None:
        """Execute timing extraction phase."""
        # Import here to avoid circular dependencies
        from agents.timing_extractor.extractor import TimingExtractor

        story = self.state_manager.state.story
        story_path = self.config.stories_path / story

        # Initialize extractor
        extractor = TimingExtractor(story_path)

        # Extract timing data
        logger.info("Parsing storyboard-timing.md...")
        timing_data = extractor.extract_timing()

        # Write output
        output_path = self.config.get_story_audio_path(story) / "timing.json"
        extractor.write_json(timing_data, output_path)

        logger.info(f"Timing data written to {output_path}")
        logger.info(f"  Total scenes: {len(timing_data.scenes)}")
        logger.info(f"  Total duration: {timing_data.total_duration:.1f}s")

    def _execute_music(self) -> None:
        """Execute music generation phase."""
        from agents.music_generator import generate_music

        logger.info("Starting music generation")

        story = self.state_manager.state.story
        story_dir = self.config.stories_path / story

        try:
            result = generate_music(story_dir)

            if result["status"] == "complete":
                logger.info("All music files validated successfully")
                validation = result["validation"]
                logger.info(
                    f"  Files found: {validation['files_found']}/{validation['files_expected']}"
                )
                logger.info(f"  Total duration: {validation['total_duration']:.1f}s")
            elif result["status"] == "awaiting_download":
                logger.warning("Music files not yet downloaded")
                logger.warning(f"  Missing: {len(result['missing_files'])} files")
                logger.info("  Follow instructions above to download from Suno")
                # Don't mark as complete - user needs to download files first
                self.state_manager.update_phase("music", "pending")
                self.state_manager.save()
                raise RuntimeError(
                    f"Please download {len(result['missing_files'])} music files from Suno. "
                    "See instructions above."
                )

        except FileNotFoundError as e:
            logger.error(f"Timing data not found: {e}")
            self.state_manager.update_phase("music", "failed")
            self.state_manager.save()
            raise
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            self.state_manager.update_phase("music", "failed")
            self.state_manager.save()
            raise

    def _execute_voices(self) -> None:
        """Execute voice generation phase."""
        import asyncio
        from agents.voice_generator.generator import (
            ElevenLabsClient,
            VoiceGenerator,
            load_voice_configs,
            extract_clips_from_timing,
        )

        story = self.state_manager.state.story
        audio_path = self.config.get_story_audio_path(story)

        # Load voice configurations
        voice_config_file = (
            Path(__file__).parent / "agents" / "voice_generator" / "voices.json"
        )
        if not voice_config_file.exists():
            raise RuntimeError(f"Voice config not found: {voice_config_file}")

        logger.info(f"Loading voice configurations from {voice_config_file}")
        voice_configs = load_voice_configs(voice_config_file)

        # Load timing data
        timing_file = audio_path / "timing.json"
        if not timing_file.exists():
            raise RuntimeError(
                f"Timing file not found: {timing_file}\nRun 'timing' phase first"
            )

        logger.info(f"Extracting voice clips from {timing_file}")
        clips = extract_clips_from_timing(timing_file, voice_configs, audio_path)

        if not clips:
            logger.info("No voice clips to generate")
            return

        # Calculate cost estimate
        total_chars = sum(clip.char_count for clip in clips)
        estimated_cost = sum(clip.estimated_cost for clip in clips)

        logger.info(f"Voice generation plan:")
        logger.info(f"  Total clips: {len(clips)}")
        logger.info(f"  Total characters: {total_chars:,}")
        logger.info(f"  Estimated cost: ${estimated_cost:.2f}")

        # Check budget
        if estimated_cost > self.config.max_voice_budget:
            raise RuntimeError(
                f"Estimated cost ${estimated_cost:.2f} exceeds budget ${self.config.max_voice_budget:.2f}\n"
                "Adjust MAX_VOICE_BUDGET in .env or reduce dialogue"
            )

        if estimated_cost > self.config.warn_voice_threshold:
            logger.warning(
                f"Estimated cost ${estimated_cost:.2f} exceeds warning threshold ${self.config.warn_voice_threshold:.2f}"
            )

        # Generate voices
        async def run_generation():
            async with ElevenLabsClient(
                api_key=self.config.elevenlabs_api_key,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
                timeout=self.config.request_timeout,
            ) as client:
                generator = VoiceGenerator(
                    client=client,
                    output_dir=audio_path,
                    max_concurrent=self.config.elevenlabs_max_concurrent,
                    progress_file=audio_path / "progress.json",
                )

                success, failed, cost = await generator.generate_batch(
                    clips, skip_existing=True
                )

                # Update state
                self.state_manager.state.total_cost = cost
                self.state_manager.save()

                return success, failed, cost

        # Run async generation
        logger.info("Starting voice generation...")
        success, failed, cost = asyncio.run(run_generation())

        logger.info(f"Voice generation complete:")
        logger.info(f"  Successful: {success}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total cost: ${cost:.2f}")

        if failed > 0:
            logger.warning(f"{failed} clips failed to generate")

    def _execute_mix(self) -> None:
        """Execute audio mixing phase."""
        from agents.audio_mixer.mixer import (
            FFmpegMixer,
            MixConfig,
            load_timing_data,
            create_voice_segments,
        )

        story = self.state_manager.state.story
        audio_path = self.config.get_story_audio_path(story)

        # Load timing data
        timing_file = audio_path / "timing.json"
        if not timing_file.exists():
            raise RuntimeError(
                f"Timing file not found: {timing_file}\nRun 'timing' phase first"
            )

        logger.info(f"Loading timing data from {timing_file}")
        total_duration, shots = load_timing_data(timing_file)

        # Create mixer
        mix_config = MixConfig(
            music_level=self.config.voice_normalization_level,  # Use as music level
            voice_level=-3.0,  # Voice louder than music
            crossfade_duration=self.config.crossfade_duration,
            loudness_target=-14.0,
            sample_rate=self.config.audio_sample_rate,
            bit_rate=self.config.audio_bit_rate,
        )

        mixer = FFmpegMixer(
            ffmpeg_path=self.config.ffmpeg_path, config=mix_config, dry_run=self.dry_run
        )

        # Step 1: Stitch music files (if multiple)
        music_dir = audio_path / "music"
        if not music_dir.exists():
            logger.warning(f"Music directory not found: {music_dir}")
            logger.info("Skipping music - will only process voices")
            background_music = None
        else:
            music_files = sorted(music_dir.glob("*.mp3"))
            if not music_files:
                logger.warning("No music files found")
                background_music = None
            elif len(music_files) == 1:
                background_music = music_files[0]
                logger.info(f"Using single music file: {background_music.name}")
            else:
                logger.info(f"Stitching {len(music_files)} music files")
                background_music = audio_path / "music_stitched.mp3"
                mixer.stitch_music(music_files, background_music)
                logger.info(f"Music stitched to: {background_music}")

        # Step 2: Create voice segments
        logger.info("Loading voice clips")
        voice_segments = create_voice_segments(shots, audio_path)

        if not voice_segments:
            logger.warning("No voice segments found")
            if background_music:
                logger.info("Copying music as final output")
                final_output = audio_path / "final_mix.mp3"
                import shutil

                shutil.copy(background_music, final_output)
                logger.info(f"Final output: {final_output}")
            return

        logger.info(f"Found {len(voice_segments)} voice clips")

        # Step 3: Overlay voices on music
        if background_music:
            logger.info("Overlaying voices on music")
            mixed_output = audio_path / "mixed_raw.mp3"
            mixer.overlay_voices(background_music, voice_segments, mixed_output)
            logger.info(f"Mixed audio: {mixed_output}")
        else:
            # No music, just concatenate voices (simplified)
            logger.info("No music - voices only")
            mixed_output = audio_path / "voices_only.mp3"
            # TODO: Implement voices-only concatenation
            logger.warning("Voices-only mixing not yet fully implemented")
            return

        # Step 4: Normalize loudness
        logger.info("Normalizing loudness")
        final_output = audio_path / "final_mix.mp3"
        mixer.normalize_loudness(mixed_output, final_output)
        logger.info(f"Final output: {final_output}")

        # Step 5: Validate duration
        logger.info("Validating duration")
        is_valid = mixer.validate_duration(final_output, total_duration, tolerance=1.0)

        if not is_valid:
            logger.warning(
                f"Duration validation failed! Expected {total_duration:.1f}s\n"
                "This may indicate timing issues or missing audio"
            )

        logger.info(f"Audio mixing complete: {final_output}")

    def _execute_validate(self) -> None:
        """Execute validation phase."""
        from agents.quality_validator.validator import (
            QualityValidator,
            load_timing_data,
        )

        story = self.state_manager.state.story
        audio_path = self.config.get_story_audio_path(story)

        # Check final mix exists
        final_mix = audio_path / "final_mix.mp3"
        if not final_mix.exists():
            raise RuntimeError(
                f"Final mix not found: {final_mix}\nRun 'mix' phase first"
            )

        # Load expected duration
        timing_file = audio_path / "timing.json"
        if not timing_file.exists():
            raise RuntimeError(
                f"Timing file not found: {timing_file}\nRun 'timing' phase first"
            )

        logger.info(f"Loading expected duration from {timing_file}")
        expected_duration = load_timing_data(timing_file)

        # Initialize validator
        validator = QualityValidator(
            ffmpeg_path=self.config.ffmpeg_path,
            ffprobe_path=self.config.ffprobe_path,
            dry_run=self.dry_run,
        )

        # Run validation suite
        logger.info("Running quality validation suite...")
        report = validator.validate_all(
            audio_path=final_mix,
            expected_duration=expected_duration,
            duration_tolerance=0.5,
            clipping_threshold=0.99,
            max_silence=2.0,
            loudness_target=-14.0,
            loudness_tolerance=1.0,
        )

        # Save report
        report_file = audio_path / "quality_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Quality report saved to {report_file}")

        # Print summary to console
        report.print_summary()

        # Check if validation passed
        if not report.overall_passed:
            logger.warning("Quality validation FAILED")
            logger.warning(f"  Critical issues: {report.critical_issues}")
            logger.warning(f"  Warnings: {report.warnings}")

            if report.critical_issues > 0:
                logger.error("CRITICAL issues detected - audio may need regeneration")
        else:
            logger.info("Quality validation PASSED ✓")

        # Update state with validation results
        self.state_manager.state.metadata = self.state_manager.state.metadata or {}
        self.state_manager.state.metadata["validation"] = {
            "passed": report.overall_passed,
            "critical_issues": report.critical_issues,
            "warnings": report.warnings,
            "report_file": str(report_file),
        }
        self.state_manager.save()

    def _print_summary(self) -> None:
        """Print execution summary."""
        state = self.state_manager.state

        print("\n" + "=" * 60)
        print("AUDIO GENERATION SUMMARY")
        print("=" * 60)
        print(f"Story: {state.story}")
        print(f"Last updated: {state.last_updated}")
        print()
        print("Phase Status:")
        for phase in PHASES:
            status = state.phases.get(phase, "pending")
            symbol = "✓" if status == "complete" else "✗" if status == "failed" else "○"
            print(f"  {symbol} {phase:12} {status}")

        if state.voice_clips:
            completed = len([s for s in state.voice_clips.values() if s == "complete"])
            total = len(state.voice_clips)
            print()
            print(f"Voice clips: {completed}/{total} complete")

        if state.total_cost > 0:
            print()
            print(f"Total cost: ${state.total_cost:.2f}")
            if state.estimated_remaining > 0:
                print(f"Estimated remaining: ${state.estimated_remaining:.2f}")

        print("=" * 60)


def validate_story_exists(story: str, config: Config) -> Path:
    """
    Validate that story directory exists.

    Args:
        story: Story name
        config: Configuration object

    Returns:
        Path to story directory

    Raises:
        ValueError: If story directory doesn't exist
    """
    story_path = config.stories_path / story

    if not story_path.exists():
        raise ValueError(
            f"Story directory not found: {story_path}\n"
            f"Available stories: {[d.name for d in config.stories_path.iterdir() if d.is_dir()]}"
        )

    # Check for required files
    storyboard = story_path / "storyboard-timing.md"
    if not storyboard.exists():
        raise ValueError(
            f"Missing required file: {storyboard}\n"
            "Story must contain storyboard-timing.md"
        )

    return story_path


def setup_logging(config: Config, story: str) -> None:
    """
    Setup file logging for orchestrator.

    Args:
        config: Configuration object
        story: Story name
    """
    log_file = config.get_story_audio_path(story) / "logs" / "orchestrator.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    logging.getLogger().addHandler(file_handler)
    logger.info(f"Logging to {log_file}")


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    parser = argparse.ArgumentParser(
        description="Audio generation orchestrator for children's stories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  %(prog)s --story luna-y-la-estrella-perdida
  
  # Specific phases
  %(prog)s --story luna-y-la-estrella-perdida --phases timing,voices
  
  # Resume after failure
  %(prog)s --story luna-y-la-estrella-perdida --resume
  
  # Dry run
  %(prog)s --story luna-y-la-estrella-perdida --dry-run
        """,
    )

    parser.add_argument(
        "--story", required=True, help="Story name (must exist in stories/ directory)"
    )

    parser.add_argument(
        "--phases",
        default="all",
        help=f"Comma-separated phase names or 'all' (valid: {', '.join(PHASES)})",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing progress.json (skip completed phases)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regenerate all phases (ignore existing progress)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without making changes",
    )

    args = parser.parse_args()

    try:
        # Determine if API key is needed for requested phases
        phases_list = [p.strip() for p in args.phases.split(",")]
        needs_api = (
            any(p in ["voices", "all"] for p in phases_list) and not args.dry_run
        )

        # Load configuration
        config = Config.load(require_api_key=needs_api)
        logger.info("Configuration loaded successfully")

        # Validate story exists
        story_path = validate_story_exists(args.story, config)
        logger.info(f"Story validated: {story_path}")

        # Setup file logging
        setup_logging(config, args.story)

        # Initialize state manager
        audio_path = config.get_story_audio_path(args.story)
        state_file = audio_path / "progress.json"
        state_manager = StateManager(state_file)

        # Load or initialize state
        if args.resume and state_manager.exists() and not args.force:
            state_manager.load()
            logger.info("Resuming from existing progress")
        else:
            if args.force and state_manager.exists():
                logger.warning("Force mode: ignoring existing progress")
            state_manager.initialize(args.story)

        # Parse phases
        phases = [p.strip() for p in args.phases.split(",")]

        # Create orchestrator and run
        orchestrator = AudioOrchestrator(config, state_manager, dry_run=args.dry_run)
        orchestrator.run(phases)

        return 0

    except (ConfigError, StateError, ValueError) as e:
        logger.error(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
