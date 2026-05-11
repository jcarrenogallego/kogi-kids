# Quality Validator Agent

**Phase**: 6 - Quality Validation  
**Purpose**: Automated quality checks for generated audio  
**Dependencies**: FFmpeg, FFprobe

## Overview

The Quality Validator performs 4 automated checks on the final audio mix to ensure production-ready quality:

1. **Duration Validator** — Verifies the final mix matches expected timing (±0.5s tolerance)
2. **Clipping Detector** — Checks for audio clipping/distortion (max amplitude <0.99)
3. **Silence Gap Checker** — Detects unwanted silence gaps (>2s duration)
4. **Loudness Validator** — Verifies loudness normalization (-14 LUFS ±1 LUFS)

## Architecture

```
QualityValidator
├── validate_duration()     → ValidationResult
├── detect_clipping()       → ValidationResult
├── check_silence_gaps()    → ValidationResult
├── validate_loudness()     → ValidationResult
└── validate_all()          → ValidationReport
```

**ValidationResult** dataclass:
- `passed`: bool
- `severity`: "PASS" | "WARNING" | "CRITICAL"
- `message`: str
- `details`: Dict[str, Any]

**ValidationReport** dataclass:
- `audio_file`: str
- `timestamp`: str
- `checks`: Dict[str, ValidationResult]
- `overall_passed`: bool
- `critical_issues`: int
- `warnings`: int

## FFmpeg Commands Used

### 1. Duration Validator

```bash
ffprobe -v error \
  -show_entries format=duration \
  -of json \
  audio.mp3
```

Parses JSON output to extract duration in seconds.

### 2. Clipping Detector

```bash
ffmpeg -i audio.mp3 \
  -af astats=metadata=1:reset=1 \
  -f null -
```

Parses stderr for peak level stats. Falls back to `volumedetect` if needed:

```bash
ffmpeg -i audio.mp3 \
  -af volumedetect \
  -f null -
```

Converts dB to linear scale: `linear = 10^(dB/20)`

### 3. Silence Gap Checker

```bash
ffmpeg -i audio.mp3 \
  -af silencedetect=n=-30dB:d=2.0 \
  -f null -
```

Parses stderr for `silence_start` and `silence_end` markers.

### 4. Loudness Validator

```bash
ffmpeg -i audio.mp3 \
  -af loudnorm=print_format=json \
  -f null -
```

Parses JSON block from stderr, extracts `input_i` (integrated loudness in LUFS).

## Usage

### Standalone

```python
from pathlib import Path
from agents.quality_validator.validator import QualityValidator, load_timing_data

# Initialize validator
validator = QualityValidator(
    ffmpeg_path="ffmpeg",
    ffprobe_path="ffprobe",
    dry_run=False
)

# Load expected duration
timing_file = Path("stories/luna-y-la-estrella-perdida/audio/timing.json")
expected_duration = load_timing_data(timing_file)

# Run all checks
audio_file = Path("stories/luna-y-la-estrella-perdida/audio/final_mix.mp3")
report = validator.validate_all(
    audio_path=audio_file,
    expected_duration=expected_duration,
    duration_tolerance=0.5,
    clipping_threshold=0.99,
    max_silence=2.0,
    loudness_target=-14.0,
    loudness_tolerance=1.0
)

# Print results
report.print_summary()

# Save JSON report
output_path = Path("stories/luna-y-la-estrella-perdida/audio/quality_report.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report.to_dict(), f, indent=2)
```

### Via Orchestrator

```bash
# Run validation phase only
python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases validate

# Run full pipeline (timing → voices → mix → validate)
python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases timing,voices,mix,validate
```

## Severity Levels

### PASS
All checks passed, no issues detected.

### WARNING
Minor issues that don't prevent usage:
- Duration deviation ≤1s
- Peak level 0.99-1.0 (near clipping but not critical)
- 1-2 silence gaps >2s
- Loudness deviation ≤2 LUFS

### CRITICAL
Serious issues requiring attention:
- Duration deviation >1s
- Peak level ≥1.0 (confirmed clipping)
- >2 silence gaps
- Loudness deviation >2 LUFS

## Output Format

### Console (Human-Readable)

```
======================================================================
AUDIO QUALITY VALIDATION REPORT
======================================================================
File: stories/luna-y-la-estrella-perdida/audio/final_mix.mp3
Timestamp: 2026-05-03T14:30:00.123456
Overall Status: ✓ PASSED
Critical Issues: 0
Warnings: 1

Detailed Results:
----------------------------------------------------------------------
✓ duration                 [PASS]       Duration matches expected (120.34s vs 120.00s)
    expected_duration: 120.00s
    actual_duration: 120.34s
    deviation: 0.34s
    tolerance: 0.50s

✓ clipping                 [PASS]       No clipping detected (peak: 0.850)
    max_level: 0.850
    threshold: 0.990
    max_level_db: -1.41dB

✗ silence_gaps             [WARNING]    Found 1 silence gap(s) > 2.0s
    max_silence_threshold: 2.0s
    silence_threshold_db: -30.0dB
    gaps_found: 1
    silence_gaps: [
      {"start": "45.23s", "end": "48.10s", "duration": "2.87s"}
    ]

✓ loudness                 [PASS]       Loudness within target (-14.3 LUFS vs -14.0 LUFS)
    target_loudness: -14.0 LUFS
    actual_loudness: -14.3 LUFS
    deviation: 0.3 LUFS
    tolerance: 1.0 LUFS
======================================================================
```

### JSON Report (`quality_report.json`)

```json
{
  "audio_file": "stories/luna-y-la-estrella-perdida/audio/final_mix.mp3",
  "timestamp": "2026-05-03T14:30:00.123456",
  "overall_passed": true,
  "critical_issues": 0,
  "warnings": 1,
  "checks": {
    "duration": {
      "passed": true,
      "severity": "PASS",
      "message": "Duration matches expected (120.34s vs 120.00s)",
      "details": {
        "expected_duration": "120.00s",
        "actual_duration": "120.34s",
        "deviation": "0.34s",
        "tolerance": "0.50s"
      }
    },
    "clipping": {
      "passed": true,
      "severity": "PASS",
      "message": "No clipping detected (peak: 0.850)",
      "details": {
        "max_level": "0.850",
        "threshold": "0.990",
        "max_level_db": "-1.41dB"
      }
    },
    "silence_gaps": {
      "passed": false,
      "severity": "WARNING",
      "message": "Found 1 silence gap(s) > 2.0s",
      "details": {
        "max_silence_threshold": "2.0s",
        "silence_threshold_db": "-30.0dB",
        "gaps_found": 1,
        "silence_gaps": [
          {
            "start": "45.23s",
            "end": "48.10s",
            "duration": "2.87s"
          }
        ]
      }
    },
    "loudness": {
      "passed": true,
      "severity": "PASS",
      "message": "Loudness within target (-14.3 LUFS vs -14.0 LUFS)",
      "details": {
        "target_loudness": "-14.0 LUFS",
        "actual_loudness": "-14.3 LUFS",
        "deviation": "0.3 LUFS",
        "tolerance": "1.0 LUFS"
      }
    }
  }
}
```

## Error Handling

### File Not Found
Returns `CRITICAL` result with error message, continues other checks.

### FFmpeg Parsing Errors
Returns `CRITICAL` result with stderr details for debugging.

### FFmpeg Timeout
Raises `ValidationError` after 60s (ffprobe) or 120s (ffmpeg).

### Missing Tools
Raises `ValidationError` during initialization if FFmpeg/FFprobe not found.

## Testing

```bash
# Run unit tests
pytest scripts/tests/test_quality_validator.py -v

# Run with coverage
pytest scripts/tests/test_quality_validator.py --cov=agents.quality_validator --cov-report=term-missing
```

## Configuration

Default values (can be overridden):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration_tolerance` | 0.5s | Max acceptable duration deviation |
| `clipping_threshold` | 0.99 | Peak level threshold (0-1) |
| `max_silence` | 2.0s | Max acceptable silence gap |
| `silence_threshold` | -30.0dB | Silence detection threshold |
| `loudness_target` | -14.0 LUFS | Target loudness (streaming standard) |
| `loudness_tolerance` | 1.0 LUFS | Max acceptable loudness deviation |

## Future Enhancements

- [ ] Spectral analysis (frequency balance check)
- [ ] Stereo phase correlation check
- [ ] Voice clarity metrics (speech intelligibility)
- [ ] Music ducking validation (voice should be louder than music)
- [ ] Format validation (sample rate, bit rate, codec)
- [ ] Reference audio comparison (if golden master exists)

## References

- [FFmpeg Filters Documentation](https://ffmpeg.org/ffmpeg-filters.html)
- [EBU R 128 Loudness Recommendation](https://tech.ebu.ch/docs/r/r128.pdf)
- [Streaming Loudness Standards (-14 LUFS)](https://en.wikipedia.org/wiki/Audio_normalization#Loudness_normalization)
