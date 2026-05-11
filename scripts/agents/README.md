# Audio Generation Agents Architecture

This directory contains specialized agents for automated audio generation from children's story storyboards.

## 🏗️ Architecture Overview

The audio generation pipeline consists of 5 specialized agents orchestrated by `audio_orchestrator.py`:

```
┌─────────────────────────────────────────────────────────────┐
│                    audio_orchestrator.py                     │
│                   (Main CLI & Orchestration)                 │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
│ timing_extractor │  │music_generator│  │ voice_generator │
│                  │  │               │  │                 │
│ • Parse MD files │  │ • Scene moods │  │ • ElevenLabs API│
│ • Calculate time │  │ • Suno prompts│  │ • Batch process │
│ • Merge dialogue │  │ • Validate DL │  │ • Retry logic   │
└──────────────────┘  └───────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   audio_mixer    │
                    │                  │
                    │ • Mix tracks     │
                    │ • Apply effects  │
                    │ • Scene crossfade│
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │quality_validator │
                    │                  │
                    │ • Validate sync  │
                    │ • Check quality  │
                    │ • Generate report│
                    └──────────────────┘
```

## 📦 Agent Descriptions

### 1. Timing Extractor (`timing_extractor/`)

**Purpose**: Parse storyboard-timing.md and extract scene/shot structure with precise timing.

**Inputs**:
- `stories/{story}/storyboard-timing.md` - Shot timing and narrative
- `stories/{story}/dialogues/dialogues-es.md` - Character dialogue

**Outputs**:
- `stories/{story}/audio/timing.json` - Structured timing data

**Key Functions**:
- Regex-based markdown parsing
- Cumulative timestamp calculation
- Dialogue merging by shot ID
- JSON schema validation

### 2. Music Generator (`music_generator/`)

**Purpose**: Generate scene-based music prompts and validate downloads.

**Inputs**:
- `stories/{story}/audio/timing.json` - Scene structure
- `mood_templates.json` - Emotion → music prompt mappings

**Outputs**:
- `stories/{story}/audio/music_prompts.json` - Suno prompts per scene
- `stories/{story}/audio/music/*.mp3` - Downloaded music (manual step)

**Key Functions**:
- Scene emotion detection via keywords
- Suno prompt generation with human approval gate
- Music file validation (duration, integrity)

### 3. Voice Generator (`voice_generator/`)

**Purpose**: Generate character voices using ElevenLabs API.

**Inputs**:
- `stories/{story}/audio/timing.json` - Dialogue text per shot
- `voices.json` - Character voice configurations

**Outputs**:
- `stories/{story}/audio/voices/*.mp3` - Generated voice clips

**Key Functions**:
- Async batch generation (max 5 concurrent)
- Rate limiting and retry logic
- Progress tracking and resume capability
- Cost estimation and reporting

### 4. Audio Mixer (`audio_mixer/`)

**Purpose**: Mix music, voices, and sound effects into final tracks.

**Inputs**:
- `stories/{story}/audio/timing.json` - Timing data
- `stories/{story}/audio/music/*.mp3` - Music tracks
- `stories/{story}/audio/voices/*.mp3` - Voice clips

**Outputs**:
- `stories/{story}/audio/mixed/*.mp3` - Final mixed audio per scene

**Key Functions**:
- FFmpeg-based mixing
- Scene crossfades (1 second overlap)
- Voice normalization and ducking
- Effects integration

### 5. Quality Validator (`quality_validator/`)

**Purpose**: Validate final audio meets quality standards.

**Inputs**:
- `stories/{story}/audio/mixed/*.mp3` - Final audio
- `stories/{story}/audio/timing.json` - Expected timing

**Outputs**:
- `stories/{story}/audio/validation_report.json` - Quality metrics

**Key Functions**:
- Duration accuracy check (±0.1s)
- Audio level validation (no clipping)
- Silence detection
- Export validation report

## 🔧 Shared Utilities (`shared/`)

### `config.py`
- Environment variable management
- API key validation
- Default settings loader

### `state_manager.py`
- Progress tracking (saves after each successful operation)
- Resume capability (skip completed tasks)
- JSON-based state persistence

## 📝 Usage Example

```bash
# Full pipeline (all phases)
python audio_orchestrator.py --story luna-y-la-estrella-perdida

# Individual phases
python audio_orchestrator.py --story luna-y-la-estrella-perdida --phases timing,voices

# Resume after failure
python audio_orchestrator.py --story luna-y-la-estrella-perdida --resume

# Dry run (show plan without executing)
python audio_orchestrator.py --story luna-y-la-estrella-perdida --dry-run
```

## 🔄 Phase Execution Order

1. **Timing** - Extract timing and structure
2. **Music** - Generate prompts → Manual Suno download → Validate
3. **Voices** - Batch generate via ElevenLabs API
4. **Mix** - Combine music + voices + effects
5. **Validate** - Quality checks and reporting

Each phase saves state to `audio/progress.json` enabling resume after failures.

## 🛠️ Development Guidelines

1. **Type Hints**: All functions must have type annotations
2. **Docstrings**: Google-style docstrings for all public functions
3. **Error Handling**: Raise specific exceptions, log context
4. **Testing**: Unit tests in `tests/test_{agent}.py`
5. **Async**: Use `asyncio` for I/O-bound operations
6. **Logging**: Use structured logging with context

## 📊 Progress Tracking

State stored in `stories/{story}/audio/progress.json`:

```json
{
  "story": "luna-y-la-estrella-perdida",
  "last_updated": "2026-05-03T14:30:00Z",
  "phases": {
    "timing": "complete",
    "music": "complete",
    "voices": "in_progress",
    "mix": "pending",
    "validate": "pending"
  },
  "voice_clips": {
    "narrator_1A.mp3": "complete",
    "luna_3B.mp3": "failed",
    "...": "..."
  },
  "total_cost": 12.45,
  "estimated_remaining": 8.20
}
```

## 🚨 Error Handling

All agents follow consistent error patterns:

- **ConfigError**: Missing/invalid configuration
- **StateError**: State file corruption or lock conflicts
- **APIError**: External API failures (ElevenLabs, Suno)
- **ValidationError**: Data validation failures
- **FFmpegError**: Audio processing failures

Errors are logged with full context and state is saved before raising.
