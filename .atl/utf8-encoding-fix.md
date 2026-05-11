# UTF-8 Encoding Fix for Spanish Characters

**Date**: 2026-05-11
**Impact**: Critical - Affects pronunciation quality of all Spanish audio narration
**Status**: ✅ Resolved

## Problem

Spanish characters (ñ, á, é, í, ó, ú) were being mispronounced by ElevenLabs TTS API in the generated audio narration.

### Symptoms
- Word "niña" pronounced as "ninia" (incorrect)
- Accented vowels mispronounced
- Issue persisted despite:
  - Using native Spanish voice (Alonso - Mexican Spanish)
  - Setting `language_code="es"` parameter
  - Correct UTF-8 text in source timing.json files

### Investigation Timeline
1. Initially suspected voice selection issue → Switched from Cristina to Alonso
2. Suspected API parameter issue → Verified all parameters correct
3. Created isolated test scripts → Reproduced CORRECT pronunciation with same parameters
4. Compared test script vs production pipeline → Found encoding difference

## Root Cause

**Windows Python defaults to `cp1252` encoding** when `open()` is called without explicit `encoding` parameter.

When reading `timing.json` (which contains UTF-8 Spanish text), missing `encoding="utf-8"` caused:
```
UTF-8 "niña" → cp1252 corrupted bytes → ElevenLabs API → wrong pronunciation
```

### Key Insight
Test scripts worked because they either:
- Used hardcoded strings (already in memory as Unicode)
- Explicitly specified `encoding="utf-8"`

Production pipeline failed because `generator.py` line 430 read `timing.json` without encoding:
```python
# BROKEN
with open(timing_file, "r") as f:  # Defaults to cp1252 on Windows!
    timing_data = json.load(f)
```

## Solution

Added explicit `encoding="utf-8"` parameter to ALL file read operations in audio pipeline:

### Files Modified
1. **`scripts/agents/voice_generator/generator.py`**
   - Line 236: `_load_progress()` - Load existing progress
   - Line 254: `_save_progress()` - Read before update
   - Line 397: `load_voice_configs()` - Load voice configurations
   - Line 436: `extract_clips_from_timing()` - **CRITICAL** - Load timing data

2. **`scripts/agents/audio_mixer/mixer.py`**
   - Line 397: `_extract_timing_info()` - Load timing for audio mixing

3. **Already correct** (no changes needed):
   - `scripts/agents/music_generator/generator.py`: Line 114
   - `scripts/agents/quality_validator/validator.py`: Line 618

### Code Pattern
```python
# Always use this pattern for JSON files with Spanish text
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)
```

### Binary Files (No Change Needed)
```python
# Binary operations don't need encoding parameter
with open(audio_file, "wb") as f:  # Correct
    f.write(audio_bytes)
```

## Verification

1. ✅ Test single file (1A.mp3) - Correct pronunciation
2. ✅ Regenerated all 21 audio clips - All correct
3. ✅ Cost: $0.50 (21 clips × $0.024/clip average)

## Prevention

### For Future Development
1. **Always** specify `encoding="utf-8"` when opening text/JSON files
2. Add to code review checklist
3. Consider adding linter rule to catch missing encoding parameter
4. Document in `AGENTS.md` (completed)

### Testing Pattern
When working with Spanish text:
```python
# Test in isolation first
test_text = "La niña perdió su muñeca"
audio = generate_voice(test_text)
# Verify pronunciation manually

# Then test with file I/O
with open("test.json", "w", encoding="utf-8") as f:
    json.dump({"text": test_text}, f, ensure_ascii=False)

with open("test.json", "r", encoding="utf-8") as f:  # Critical!
    data = json.load(f)
audio = generate_voice(data["text"])
# Verify pronunciation still correct
```

## Lessons Learned

1. **Platform-specific encoding defaults are dangerous**
   - Windows: cp1252
   - Linux/Mac: UTF-8
   - Always be explicit!

2. **Unicode corruption is silent**
   - No errors thrown
   - Data "looks fine" when printed
   - Only manifests in API behavior (pronunciation)

3. **Test end-to-end file I/O paths**
   - Isolated tests with in-memory strings can pass
   - File operations can fail silently with encoding issues

4. **Cost of assumptions**
   - Regenerating 21 clips cost $0.50 in API credits
   - Could have been prevented with proper encoding from start

## References

- Python docs: [open() encoding parameter](https://docs.python.org/3/library/functions.html#open)
- PEP 597: [Add optional EncodingWarning](https://peps.python.org/pep-0597/)
- Related: UTF-8 BOM handling, JSON ensure_ascii=False for Spanish text

---

**Tags**: #encoding #utf8 #spanish #elevenlabs #audio-pipeline #bugfix #windows #python
