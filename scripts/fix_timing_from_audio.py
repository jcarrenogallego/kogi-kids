#!/usr/bin/env python3
"""
Fix timing.json timestamps based on actual audio file durations.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List


def get_audio_duration(audio_file: Path) -> float:
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_file),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {audio_file}: {e}")
        return 0.0


def fix_timing_from_audio(timing_file: Path, audio_dir: Path, min_gap: float = 0.5):
    """
    Adjust timing.json based on actual audio durations.

    Args:
        timing_file: Path to timing.json
        audio_dir: Path to audio directory containing narration files
        min_gap: Minimum gap between shots without dialogue (seconds)
    """
    # Load timing data
    with open(timing_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded timing data for story: {data['story']}")
    print(f"Original total duration: {data['total_duration']}s")
    print(f"Total scenes: {data['total_scenes']}")
    print(f"Total shots: {data['total_shots']}")
    print()

    # Track cumulative time
    current_time = 0.0

    # Process each scene
    for scene_idx, scene in enumerate(data["scenes"]):
        scene_start = current_time
        print(f"\nScene {scene['scene_number']}: {scene['title']}")

        # Process each shot
        for shot_idx, shot in enumerate(scene["shots"]):
            shot_id = shot["shot_id"]
            has_dialogue = shot.get("has_dialogue", False)

            if has_dialogue:
                # Get actual audio duration
                narration_file = audio_dir / "narration" / f"{shot_id}.mp3"

                if narration_file.exists():
                    actual_duration = get_audio_duration(narration_file)
                    old_duration = shot["duration"]

                    # Update shot timing
                    shot["start_time"] = current_time
                    shot["duration"] = actual_duration
                    shot["end_time"] = current_time + actual_duration

                    print(
                        f"  {shot_id}: {old_duration:.2f}s -> {actual_duration:.2f}s (diff: {actual_duration - old_duration:+.2f}s)"
                    )

                    current_time += actual_duration
                else:
                    print(
                        f"  {shot_id}: Audio file not found, keeping original {shot['duration']:.2f}s"
                    )
                    shot["start_time"] = current_time
                    shot["end_time"] = current_time + shot["duration"]
                    current_time += shot["duration"]
            else:
                # No dialogue - keep original duration with minimum gap
                duration = max(shot["duration"], min_gap)
                shot["start_time"] = current_time
                shot["end_time"] = current_time + duration
                shot["duration"] = duration

                print(f"  {shot_id}: Visual only, keeping {duration:.2f}s")
                current_time += duration

        # Update scene total duration
        scene_duration = current_time - scene_start
        scene["total_duration"] = scene_duration
        print(f"  Scene total: {scene_duration:.2f}s")

    # Update overall total duration
    data["total_duration"] = current_time

    print(f"\n{'=' * 60}")
    print(f"New total duration: {current_time:.2f}s")
    print(f"Difference: {current_time - 189.0:+.2f}s from original")
    print(f"{'=' * 60}\n")

    # Backup original
    backup_file = timing_file.parent / "timing_backup_original.json"
    if not backup_file.exists():
        import shutil

        shutil.copy2(timing_file, backup_file)
        print(f"[OK] Original backed up to: {backup_file}")

    # Save updated timing
    with open(timing_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Updated timing saved to: {timing_file}")
    print(f"\nNext step: Regenerate audio mix with corrected timing")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_timing_from_audio.py <story-name>")
        sys.exit(1)

    story_name = sys.argv[1]

    # Paths
    project_root = Path(__file__).parent.parent
    audio_dir = project_root / "stories" / story_name / "audio"
    timing_file = audio_dir / "timing.json"

    if not timing_file.exists():
        print(f"Error: timing.json not found at {timing_file}")
        sys.exit(1)

    if not audio_dir.exists():
        print(f"Error: audio directory not found at {audio_dir}")
        sys.exit(1)

    # Fix timing
    fix_timing_from_audio(timing_file, audio_dir, min_gap=0.5)
