# Agent Instructions - Kogi Kids

High-signal facts for working in this repository.

## Critical Commands

### Testing
```bash
# Run all audio pipeline tests (scripts/ is working dir)
cd scripts
pytest tests/ -v --cov=agents --cov-report=term-missing

# Run specific test file
pytest tests/test_voice_generator.py -v
```

**Important**: All tests mock external APIs (ElevenLabs, FFmpeg). No real API calls = no charges.

### Audio Pipeline
```bash
# Full pipeline (from scripts/ directory)
cd scripts
python audio_orchestrator.py --story luna-y-la-estrella-perdida

# Specific phases only
python audio_orchestrator.py --story {story-name} --phases timing,voices

# Resume after interruption (reads progress.json)
python audio_orchestrator.py --story {story-name} --resume

# Dry run (show plan without executing)
python audio_orchestrator.py --story {story-name} --dry-run
```

**Phase execution order**: timing → music → voices → mix → validate

### Agent Validation
```bash
# Validate all 6 MCP agent schemas from project root
python validate_all_agents.py

# Validate single agent
python validate_agent.py agents/character-agent
```

## Architecture Overview

### Two Pipeline Systems

1. **Audio Pipeline** (production-ready)
   - Location: `scripts/` (separate working directory)
   - Run from: `cd scripts` first, then execute commands
   - State: JSON files in `stories/{story-name}/audio/`
   - Fully implemented with tests

2. **Video Generation Agents** (MCP schema, not connected yet)
   - Location: `agents/` (6 MCP-compliant agents)
   - Format: `agent.json` (schema) + `prompt.md` (system prompt)
   - Status: Schemas validated, LangGraph integration pending

### Key Directories

```
scripts/               # Audio pipeline - ALWAYS cd here first
  agents/             # Audio agents (not MCP protocol)
  tests/              # pytest test suite
  audio_orchestrator.py  # Main CLI entry point

agents/               # MCP video generation agents (not audio)
  {agent-name}/
    agent.json        # MCP 2024-11-05 schema
    prompt.md         # System prompt

stories/{story-name}/
  audio/
    progress.json     # Resume capability - do not delete
    timing.json       # Extracted timings
    voices/           # Generated TTS files
    final_mix.mp3     # Mixed audio output
```

## Critical Gotchas

### Working Directory Confusion
The audio pipeline **must** be run from `scripts/` directory. Commands will fail if run from project root:

```bash
# WRONG (from project root)
python scripts/audio_orchestrator.py --story luna

# CORRECT
cd scripts
python audio_orchestrator.py --story luna
```

### Two Different Agent Systems
- `scripts/agents/` = Audio pipeline agents (not MCP protocol)
- `agents/` = Video generation MCP agents (not implemented yet)

Don't confuse them. They serve different purposes.

### Progress State is Sacred
`stories/{story-name}/audio/progress.json` enables resume capability. If deleted, user loses progress and wastes API credits regenerating already-completed phases.

### Story Names
Story slugs use kebab-case: `luna-y-la-estrella-perdida` (not snake_case, not camelCase).

### UTF-8 Encoding for Spanish Characters
**CRITICAL**: All file operations that read JSON files containing Spanish text MUST use `encoding="utf-8"`.

**Problem**: Windows Python defaults to `cp1252` encoding when opening files without explicit encoding parameter. This mangles UTF-8 characters like "ñ", "á", "é", "í", "ó", "ú" when reading JSON files.

**Symptom**: ElevenLabs TTS receives corrupted text and pronounces Spanish words incorrectly (e.g., "niña" sounds like "ninia").

**Solution**: Always specify encoding parameter when opening text/JSON files:
```python
# WRONG - Uses Windows default cp1252
with open(timing_file, "r") as f:
    data = json.load(f)

# CORRECT - Explicitly uses UTF-8
with open(timing_file, "r", encoding="utf-8") as f:
    data = json.load(f)
```

**Files Fixed**:
- `scripts/agents/voice_generator/generator.py`: Lines 236, 254, 397, 436
- `scripts/agents/audio_mixer/mixer.py`: Line 397
- `scripts/agents/music_generator/generator.py`: Line 114 (already correct)
- `scripts/agents/quality_validator/validator.py`: Line 618 (already correct)

**Note**: Binary file operations (`"wb"`, `"rb"`) do NOT need encoding parameter.

## Testing Infrastructure

- **Framework**: pytest 9.0.3 (installed, working)
- **All external APIs mocked**: No accidental ElevenLabs/Runway charges during tests
- **Async support**: `pytest-asyncio` for async/await test functions
- **Coverage**: Use `--cov=agents` flag

**Test file naming**: `test_{component}.py` matches the component it tests.

## Python Environment

- **Version**: Python 3.13.3 (confirmed installed)
- **FFmpeg**: 8.1 (confirmed installed, required for audio mixing)
- **Dependencies**: `scripts/requirements.txt` (NOT project root)

Install from:
```bash
cd scripts
pip install -r requirements.txt
```

## API Keys

Stored in `scripts/.env` (gitignored):
- `ELEVENLABS_API_KEY` - Required for voice generation
- `RUNWAY_API_KEY` - Required for animation (future)

Example file: `scripts/.env.example`

## Custom Commands (opencode.json)

Use slash commands to delegate to specialized agents:

- `/audio-pipeline` - Full audio generation workflow
- `/generate-voices` - Phase 3 only (ElevenLabs TTS)
- `/mix-audio` - Phase 4 only (FFmpeg mixing)
- `/extract-timing` - Phase 1 only (storyboard parsing)
- `/test-audio` - Run pytest test suite
- `/validate-agents` - Check MCP schema compliance
- `/animate` - Runway Gen-3 animation (future)

These commands auto-delegate to appropriate subagents (audio-engineer, video-orchestrator, agent-validator).

## Code Patterns

### Async Concurrency
Voice generation uses async/await with semaphore limits:
```python
async with asyncio.Semaphore(5):  # Max 5 concurrent requests
    await generate_voice()
```

### State Persistence
Always use StateManager for progress tracking:
```python
from agents.shared.state_manager import StateManager
state_manager.mark_phase_complete("voices")
state_manager.save()  # Atomic write: temp file → rename
```

Never write to `progress.json` directly.

### Error Handling
Audio pipeline uses custom exceptions:
- `VoiceGeneratorError` - ElevenLabs API failures
- `StateError` - Progress tracking issues
- `ConfigError` - Missing .env or invalid config

### Pydantic Validation
All data models use Pydantic v2:
```python
from pydantic import BaseModel, Field
```

## MCP Agent Development

### Schema Requirements (agent.json)
Must include:
- `"runtime": "mcp"`
- `"protocol_version": "2024-11-05"`
- `capabilities`, `inputs`, `outputs`, `dependencies`

Run `python validate_all_agents.py` after changes.

### Prompt Guidelines (prompt.md)
Structure:
1. Role description
2. Input parameter details
3. Output format with examples
4. Numbered rules (10-20 typical)
5. Skills applied from registry
6. Pre-return validation checklist

### Dependencies
Declare skill dependencies in `agent.json`:
```json
"dependencies": {
  "skills": ["character-design-sheet", "kids-book-writer"]
}
```

Skills registry: `.atl/skill-registry.md`

## Things That Don't Exist Yet

- LangGraph workflow orchestration (planned)
- FastAPI REST API (planned)
- PostgreSQL persistence (planned, currently using JSON files)
- Automated MidJourney execution (currently manual)
- Full video assembly (currently separate pipeline)

Don't assume these exist when reading code references.

## References

Comprehensive context: `.atl/sdd-init-context.md` (576 lines)
Agent structure docs: `agents/README.md` (482 lines)
OpenCode config: `opencode.json` (agent definitions, custom commands)
