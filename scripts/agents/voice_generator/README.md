# Voice Generator Agent

Generates voice clips for narrator and character dialogues using ElevenLabs API.

## Features

- **Async Batch Processing**: Generate multiple clips concurrently (configurable limit)
- **Retry Logic**: Exponential backoff for rate limits (429) and transient errors
- **Progress Tracking**: Resume capability via `progress.json`
- **Cost Estimation**: Real-time cost tracking ($0.30 per 1000 characters)
- **Voice Configuration**: JSON-based voice profiles with fine-tuning parameters

## Architecture

```
voice_generator/
├── generator.py          # Main implementation
│   ├── ElevenLabsClient  # Async API client with retry logic
│   ├── VoiceGenerator    # Batch orchestrator
│   ├── VoiceClip         # Data model for voice clips
│   └── VoiceConfig       # Voice profile configuration
└── voices.json           # Voice profiles for characters
```

## Configuration

### Voice Profiles (`voices.json`)

```json
{
  "voices": [
    {
      "character": "narrator",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "description": "Rachel - Calm narrative voice",
      "stability": 0.5,
      "similarity_boost": 0.75,
      "style": 0.0,
      "use_speaker_boost": true
    }
  ]
}
```

**Parameters**:
- `stability`: 0.0-1.0 (lower = more varied, higher = more consistent)
- `similarity_boost`: 0.0-1.0 (higher = closer to original voice)
- `style`: 0.0-1.0 (higher = more expressive/dramatic)
- `use_speaker_boost`: Enhances clarity and presence

### Environment Variables (`.env`)

```bash
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_MAX_CONCURRENT=5
MAX_VOICE_BUDGET=50.00
WARN_VOICE_THRESHOLD=40.00
MAX_RETRIES=3
RETRY_DELAY=2.0
REQUEST_TIMEOUT=30.0
```

## Usage

### Via Orchestrator

```bash
python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases voices
```

### Programmatic

```python
import asyncio
from agents.voice_generator.generator import (
    ElevenLabsClient,
    VoiceGenerator,
    load_voice_configs,
    extract_clips_from_timing
)

async def generate():
    # Load configurations
    voice_configs = load_voice_configs("voices.json")
    clips = extract_clips_from_timing("timing.json", voice_configs, output_dir)
    
    # Generate voices
    async with ElevenLabsClient(api_key="...") as client:
        generator = VoiceGenerator(client, output_dir, max_concurrent=5)
        success, failed, cost = await generator.generate_batch(clips)
    
    print(f"Generated {success} clips, cost: ${cost:.2f}")

asyncio.run(generate())
```

## Output Structure

```
audio/
├── narration/
│   ├── 1A.mp3
│   ├── 1B.mp3
│   └── ...
├── dialogues/
│   ├── Luna_2A.mp3
│   ├── Estrellita_3B.mp3
│   └── ...
└── progress.json  # Resume state
```

## Error Handling

### Rate Limits (429)
- Automatic exponential backoff: 1s, 2s, 4s, 8s
- Respects ElevenLabs rate limits (free: 2-3 concurrent, paid: 5-10)

### Network Errors
- Retries transient errors up to `MAX_RETRIES`
- Logs errors with shot_id for debugging

### Budget Protection
- Estimates cost before generation
- Fails fast if exceeds `MAX_VOICE_BUDGET`
- Warns at `WARN_VOICE_THRESHOLD`

## Testing

```bash
pytest tests/test_voice_generator.py -v
```

**Test Coverage**:
- ✅ Successful speech generation
- ✅ Retry logic on rate limits
- ✅ Max retries failure
- ✅ API error handling
- ✅ Cost estimation
- ✅ Progress tracking and resume
- ✅ Concurrent request limiting
- ✅ Voice config loading
- ✅ Clip extraction from timing data

## Performance

**Typical Metrics** (26 shots, 2000 chars average):
- Duration: ~5-8 minutes (5 concurrent)
- Cost: ~$15-20 USD
- Success rate: >95% (with retries)

**Concurrency Guidelines**:
- Free tier: 2-3 concurrent
- Starter ($5/mo): 5 concurrent
- Creator ($22/mo): 10 concurrent

## Troubleshooting

### "Rate limit exceeded"
- Reduce `ELEVENLABS_MAX_CONCURRENT`
- Increase `RETRY_DELAY`

### "No voice configured for character: X"
- Add character to `voices.json`
- Get voice IDs from: https://elevenlabs.io/app/voice-library

### "Budget exceeded"
- Increase `MAX_VOICE_BUDGET` in `.env`
- Or reduce dialogue in `timing.json`

### Resume after failure
- Progress is auto-saved to `progress.json`
- Re-run orchestrator - skips completed clips
