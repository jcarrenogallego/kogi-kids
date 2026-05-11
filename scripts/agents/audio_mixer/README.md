# Audio Mixer Agent

Mixes music, voice clips, and sound effects into final audio output using FFmpeg.

## Features

- **Music Stitching**: Seamless crossfades between music tracks (3s default)
- **Voice Overlay**: Precise timing overlay using adelay filters
- **Loudness Normalization**: EBU R128 standard (-14 LUFS target)
- **Duration Validation**: Ensures final output matches timing.json
- **Dry Run Mode**: Preview commands without execution

## Architecture

```
audio_mixer/
├── mixer.py            # Main implementation
│   ├── FFmpegMixer     # FFmpeg wrapper
│   ├── AudioSegment    # Voice/music segment model
│   └── MixConfig       # Mix configuration
└── README.md
```

## FFmpeg Operations

### 1. Music Stitching

Concatenates multiple music files with crossfades:

```bash
ffmpeg -i music1.mp3 -i music2.mp3 -i music3.mp3 \
  -filter_complex "[0][1]acrossfade=d=3:c1=tri:c2=tri[a1];
                   [a1][2]acrossfade=d=3:c1=tri:c2=tri[a2];
                   [a2]volume=-18dB" \
  -ar 44100 -b:a 192k output.mp3
```

**Crossfade Parameters**:
- `d`: Duration in seconds
- `c1`/`c2`: Curve type (tri=trigonometric, exp=exponential, log=logarithmic)

### 2. Voice Overlay

Overlays voice clips on music with timing:

```bash
ffmpeg -i music.mp3 -i voice1.mp3 -i voice2.mp3 \
  -filter_complex "[1]adelay=0|0,volume=-3dB[v0];
                   [2]adelay=5000|5000,volume=-3dB[v1];
                   [0][v0][v1]amix=inputs=3:duration=longest:weights=1 1 1" \
  -ar 44100 -b:a 192k output.mp3
```

**Key Filters**:
- `adelay`: Delays audio stream (ms)
- `volume`: Adjusts volume (dB)
- `amix`: Mixes multiple streams

### 3. Loudness Normalization

Two-pass loudness normalization:

```bash
ffmpeg -i input.mp3 \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary" \
  -ar 44100 -b:a 192k output.mp3
```

**Parameters**:
- `I`: Integrated loudness target (-14 LUFS)
- `TP`: True peak limit (-1.5 dBFS)
- `LRA`: Loudness range target (11 LU)

## Configuration

### Mix Config (`MixConfig`)

```python
MixConfig(
    music_level=-18.0,      # Music volume (dB)
    voice_level=-3.0,       # Voice volume (dB)
    crossfade_duration=3.0, # Crossfade duration (seconds)
    loudness_target=-14.0,  # Target loudness (LUFS)
    sample_rate=44100,      # Audio sample rate (Hz)
    bit_rate=192            # Audio bit rate (kbps)
)
```

### Environment Variables (`.env`)

```bash
FFMPEG_PATH=ffmpeg
AUDIO_SAMPLE_RATE=44100
AUDIO_BIT_RATE=192
VOICE_NORMALIZATION_LEVEL=-20.0
MUSIC_VOLUME_RATIO=0.3
CROSSFADE_DURATION=1.0
```

## Usage

### Via Orchestrator

```bash
python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases mix
```

### Programmatic

```python
from agents.audio_mixer.mixer import (
    FFmpegMixer,
    MixConfig,
    AudioSegment,
    load_timing_data,
    create_voice_segments
)

# Initialize mixer
config = MixConfig()
mixer = FFmpegMixer(ffmpeg_path="ffmpeg", config=config)

# Stitch music
music_files = [Path("music1.mp3"), Path("music2.mp3")]
mixer.stitch_music(music_files, Path("music_stitched.mp3"))

# Overlay voices
total_duration, shots = load_timing_data(Path("timing.json"))
voice_segments = create_voice_segments(shots, Path("audio"))
mixer.overlay_voices(Path("music_stitched.mp3"), voice_segments, Path("mixed.mp3"))

# Normalize
mixer.normalize_loudness(Path("mixed.mp3"), Path("final.mp3"))

# Validate
is_valid = mixer.validate_duration(Path("final.mp3"), total_duration)
```

## Pipeline Flow

```
Step 1: Music Stitching
  music1.mp3 ──┐
  music2.mp3 ──┼──[acrossfade]──> music_stitched.mp3
  music3.mp3 ──┘

Step 2: Voice Overlay
  music_stitched.mp3 ──┐
  voice1.mp3 ─[delay]──┤
  voice2.mp3 ─[delay]──┼──[amix]──> mixed_raw.mp3
  voice3.mp3 ─[delay]──┘

Step 3: Normalization
  mixed_raw.mp3 ──[loudnorm]──> final_mix.mp3

Step 4: Validation
  final_mix.mp3 ──[duration check]──> ✓ or ✗
```

## Output Structure

```
audio/
├── music/
│   ├── scene1.mp3
│   ├── scene2.mp3
│   └── ...
├── music_stitched.mp3  # Intermediate: stitched music
├── mixed_raw.mp3       # Intermediate: music + voices
└── final_mix.mp3       # Final output: normalized
```

## Error Handling

### FFmpeg Not Found
```
AudioMixerError: FFmpeg not accessible
```
**Solution**: Install FFmpeg
- Windows: https://ffmpeg.org/download.html
- Mac: `brew install ffmpeg`
- Linux: `apt-get install ffmpeg`

### Command Timeout
```
AudioMixerError: FFmpeg command timed out
```
**Solution**: Check file sizes, increase timeout (300s default)

### Duration Mismatch
```
WARNING: Duration validation failed! Expected 189.0s
```
**Solution**: 
- Check for missing voice clips
- Verify music files cover full duration
- Inspect timing.json for errors

## Testing

```bash
pytest tests/test_audio_mixer.py -v
```

**Test Coverage**:
- ✅ Audio segment validation
- ✅ Single file music stitching
- ✅ Multi-file music stitching with crossfade
- ✅ Voice overlay with timing
- ✅ Loudness normalization
- ✅ Duration validation
- ✅ Dry run mode
- ✅ FFmpeg error handling
- ✅ Command timeout handling

## Performance

**Typical Metrics** (3-minute final mix):
- Music stitching: 10-15 seconds
- Voice overlay: 20-30 seconds
- Normalization: 15-20 seconds
- Total: ~1 minute

## Advanced Techniques

### Custom Crossfade Curves

```python
# Exponential crossfade (dramatic transition)
filter_str = "[0][1]acrossfade=d=3:c1=exp:c2=exp"

# Logarithmic crossfade (smooth transition)
filter_str = "[0][1]acrossfade=d=3:c1=log:c2=log"

# Trigonometric crossfade (balanced - default)
filter_str = "[0][1]acrossfade=d=3:c1=tri:c2=tri"
```

### Volume Ducking

Automatically lower music when voices are present:

```python
# Requires advanced filter chain with sidechaining
# TODO: Implement in v2
```

### Multi-Track Mixing

Mix music, voices, and sound effects:

```python
# Add sound effects as additional segments
sfx_segments = [
    AudioSegment(Path("wind.mp3"), start_time=10.0, duration=5.0),
    AudioSegment(Path("magic.mp3"), start_time=25.0, duration=3.0)
]

# Overlay all: music + voices + sfx
# TODO: Implement in v2
```

## Troubleshooting

### Audio Artifacts
- Increase crossfade duration
- Check source audio quality
- Verify sample rates match

### Clipping
- Reduce music_level or voice_level
- Use loudness normalization
- Check true peak (TP) in normalization

### Out of Sync
- Validate timing.json timestamps
- Check voice clip start_time values
- Verify FFmpeg version (4.4+ recommended)

## FFmpeg Version

Requires FFmpeg 4.4 or later with filters:
- `acrossfade`
- `adelay`
- `amix`
- `loudnorm`

Check version:
```bash
ffmpeg -version
```
