---
name: video-generator-orchestrator
description: Orchestrate 6 specialized agents to transform children's stories into MidJourney video prompts. Sequential workflow with human approval gates. Trigger when user asks to generate video from story, create MidJourney prompts from narrative, or says "genera video para esta historia".
---

# Video Generator Orchestrator

Transform children's stories (ages 2-10) into structured MidJourney video prompts through a 6-phase agent workflow with human validation at each step.

## Workflow Overview

```
Story Input → Character Agent → [Human Review] → Dialogue Agent → [Human Review] →
Scenography Agent → [Human Review] → Cinematography Agent → [Human Review] →
Scriptwriter Agent → [Human Review] → Prompt Engineer Agent → [Human Review] →
MidJourney Prompts (Final Output)
```

**Core Principle**: STOP after each agent and WAIT for explicit human approval before proceeding to next phase.

## Orchestrator Instructions

### Initialization

When user provides a story:

1. **Validate story suitability**:
   - Target age range mentioned or inferable (2-10 years)
   - Has narrative structure (characters, setting, conflict/resolution)
   - Appropriate content for children (no violence, mature themes)
   
2. **Create Engram topic key**: `video-gen/{story-slug}/{timestamp}`

3. **Show workflow preview**:
   ```
   Voy a procesar tu historia en 6 fases:
   
   1. Character Agent → Descripciones de personajes
   2. Dialogue Agent → Diálogos apropiados para edad
   3. Scenography Agent → Escenografías y locaciones
   4. Cinematography Agent → Ángulos de cámara y composición
   5. Scriptwriter Agent → Guion completo ensamblado
   6. Prompt Engineer Agent → Prompts MidJourney listos
   
   Después de cada fase te pido aprobación antes de continuar.
   ¿Arrancamos con Character Agent?
   ```

### Phase Execution Pattern

For EACH of the 6 phases:

1. **Launch sub-agent** with:
   - Phase-specific instructions (see Agent Definitions below)
   - Relevant skills injected (compact rules from registry)
   - Previous phase outputs as context
   - Story input

2. **Present results**:
   ```
   ## Fase {N}: {Agent Name} — Resultados
   
   {Agent output formatted clearly}
   
   ¿Aprobás este resultado o querés cambios?
   - "apruebo" / "sí" / "continúa" → procedo a siguiente fase
   - Feedback específico → re-ejecuto este agente con tus ajustes
   ```

3. **Save to Engram** (after approval):
   ```python
   mcp_engram_mem_save(
       title=f"video-gen/{story-slug}/phase-{N}-{agent-name}",
       topic_key=f"video-gen/{story-slug}/phase-{N}",
       type="decision",
       project="kogi-kids",
       content=f"""
       ## Phase {N}: {Agent Name}
       
       **Story**: {story_title}
       **Status**: Approved
       **Output**: {agent_output}
       **User Feedback**: {feedback if any}
       """
   )
   ```

4. **Wait for approval** — do NOT proceed to next phase until user explicitly approves

### Recovery from Interruption

If conversation is compacted or user returns later:

1. Search Engram: `mcp_engram_mem_search(query="video-gen/{story-slug}", project="kogi-kids")`
2. Find latest completed phase
3. Offer to resume: "Veo que llegamos hasta {phase N}. ¿Continuamos con {phase N+1}?"

## Agent Definitions

### 1. Character Agent

**Goal**: Extract and describe all characters with visual consistency for MidJourney

**Sub-agent prompt**:
```
Analyze this children's story and generate character descriptions suitable for MidJourney image generation (ages {age_range}):

{story_input}

For EACH character, provide:

1. **Name & Role**: Main character, sidekick, antagonist, etc.
2. **Age**: Specific age or age range
3. **Physical Traits**: 
   - Ethnicity / skin tone (use neutral descriptive terms)
   - Hair (color, style, length)
   - Body type (slim, chubby, tall, short)
   - Distinguishing features (freckles, glasses, dimples)
4. **Wardrobe**: Typical outfit they wear throughout the story (color palette, style)
5. **Personality Archetype**: Brave, curious, shy, mischievous (affects facial expressions)
6. **MidJourney Consistency Tags**: Suggest style tags for visual consistency (e.g., "pixar style", "Studio Ghibli", "watercolor illustration")

**Output Format**: JSON array per character

Apply character-design-sheet skill patterns for turnaround consistency.
```

**Skills to inject**: `character-design-sheet`, `kids-book-writer` (age-appropriate traits)

**Expected output**: JSON array of 2-8 character descriptions

---

### 2. Dialogue Agent

**Goal**: Write age-appropriate dialogue with pacing suitable for video

**Sub-agent prompt**:
```
Given these character descriptions:

{character_descriptions}

And this story:

{story_input}

Generate dialogue script with:

1. **Scene breakdown**: Divide story into 5-10 scenes (each = 15-30 seconds for ages 2-4, 30-60 seconds for ages 5-10)
2. **Dialogue per scene**:
   - Character name
   - Spoken line (age-appropriate vocabulary — see kids-book-writer skill for word counts)
   - Emotion/tone (excited, worried, curious)
   - Duration estimate (seconds)
3. **Narration** (if needed): Voice-over text for scene transitions or exposition
4. **Pacing notes**: Identify moments that need visual focus (no dialogue, just action/music)

**Constraints**:
- Ages 2-3: Max 50 words total per scene, simple sentences (3-5 words)
- Ages 4-5: Max 100 words per scene, compound sentences OK
- Ages 6-7: Max 150 words per scene, some complex sentences
- Ages 8-10: Max 200 words per scene, narrative complexity allowed

Apply kids-book-writer skill for vocabulary and storytelling skill for pacing.
```

**Skills to inject**: `kids-book-writer`, `storytelling`

**Expected output**: JSON array of scenes with dialogue objects

---

### 3. Scenography Agent

**Goal**: Describe settings, locations, and atmosphere for each scene

**Sub-agent prompt**:
```
Given this dialogue script:

{dialogue_script}

And these characters:

{character_descriptions}

Generate scenography descriptions for each scene:

1. **Location**: Beach, forest, bedroom, spaceship, etc.
2. **Time of Day**: Morning, afternoon, sunset, night
3. **Weather/Atmosphere**: Sunny, rainy, foggy, magical glow
4. **Key Props**: Objects important to the scene (treasure chest, magic wand, bicycle)
5. **Color Palette**: Dominant colors for mood (warm pastels, cool blues, vibrant primary)
6. **Mood/Tone**: Cozy, adventurous, mysterious, playful
7. **MidJourney Scene Tags**: Environment descriptors (e.g., "whimsical forest --ar 16:9", "cozy bedroom interior")

**Output Format**: JSON array per scene matching dialogue script

Apply storytelling skill for SCAR framework (setup scenes vs conflict scenes).
```

**Skills to inject**: `storytelling`, `character-design-sheet` (color palette consistency)

**Expected output**: JSON array of scene descriptions (1 per dialogue scene)

---

### 4. Cinematography Agent

**Goal**: Define camera angles, framing, and shot composition

**Sub-agent prompt**:
```
Given:
- Dialogue script: {dialogue_script}
- Scene descriptions: {scene_descriptions}
- Target age: {age_range}

Generate shot list for each scene:

1. **Shot Number**: Sequential (e.g., Shot 1.1, 1.2 for scene 1)
2. **Shot Type**:
   - Establishing shot (wide, shows full location)
   - Medium shot (character from waist up)
   - Close-up (face, shows emotion)
   - Over-the-shoulder (dialogue between characters)
   - POV (point of view shot)
   - Detail shot (prop, object focus)
3. **Camera Angle**: Eye-level, low angle (heroic), high angle (vulnerable), dutch tilt
4. **Camera Movement**: Static, pan, zoom in/out, tracking
5. **Duration**: Seconds per shot (shorter for younger ages — 2-3 sec ages 2-4, 4-6 sec ages 5-10)
6. **Framing Notes**: Rule of thirds, centered, symmetrical
7. **Transition**: Cut, fade, dissolve to next shot

**Age Guidelines**:
- Ages 2-4: Prefer static medium/close shots, minimal camera movement, bright clear framing
- Ages 5-7: Mix of shot types OK, some movement, dynamic angles for excitement
- Ages 8-10: Full cinematic range, faster cuts, complex compositions

**Output Format**: JSON array of shots per scene

Apply cinematography principles: 3-point lighting assumptions, rule of thirds, eye-line match for dialogue.
```

**Skills to inject**: `storytelling` (visual pacing), `prompt-engineering-patterns` (structured output)

**Expected output**: JSON array of 20-50 shots total (depends on story length)

---

### 5. Scriptwriter Agent

**Goal**: Assemble complete script with all elements synchronized

**Sub-agent prompt**:
```
Given:
- Characters: {character_descriptions}
- Dialogue: {dialogue_script}
- Scenography: {scene_descriptions}
- Shot list: {shot_list}

Generate unified script in professional format:

For EACH scene:

```
SCENE {N}: {LOCATION} - {TIME OF DAY}

SCENOGRAPHY:
{Atmosphere, color palette, key props}

[SHOT {N}.1 - {SHOT TYPE} - {ANGLE} - {DURATION}sec]

CHARACTER NAME (emotion)
Dialogue line here.

NARRATION (if applicable):
Voice-over text.

ACTION:
[Visual action description: Character does X while Y happens]

[SHOT {N}.2 - {SHOT TYPE} - {ANGLE} - {DURATION}sec]
...
```

**Synchronization checks**:
- Every dialogue line has corresponding shot
- Shot durations match dialogue duration estimates
- Scene transitions are clear
- Character descriptions consistent across scenes
- Props mentioned in dialogue appear in scenography

Apply mockumentary-screenplay skill for Fountain-like formatting (adapted for animation).
```

**Skills to inject**: `mockumentary-screenplay` (script structure), `storytelling` (narrative flow)

**Expected output**: Full text script (plain text or Markdown formatted)

---

### 6. Prompt Engineer Agent

**Goal**: Transform script into MidJourney V7 prompts ready for generation

**Sub-agent prompt**:
```
Given this complete script:

{full_script}

Generate MidJourney V7 prompts for EACH shot:

**Prompt Structure**:
```
[Shot {N}] {Character descriptions} in {location}, {action}, {shot type}, {camera angle}, {lighting}, {color palette}, {art style} --ar 16:9 --style {style_code} --v 7
```

**Requirements**:
1. **Character Consistency**: Use SAME character descriptors across all shots (from Character Agent output)
2. **Art Style Consistency**: Choose ONE style for entire video:
   - Pixar 3D animation
   - Studio Ghibli watercolor
   - Disney 2D animation classic
   - Childrens book illustration (gouache)
   - Clay animation (stop motion)
3. **Shot-specific details**:
   - Camera angle (low angle shot, birds eye view, close up on face)
   - Action/emotion (character jumping with joy, character looking worried)
   - Lighting (soft morning light, dramatic sunset, magical glow)
4. **Parameters**:
   - `--ar 16:9` (video aspect ratio) for all shots
   - `--style raw` or custom style code for consistency
   - `--v 7` (MidJourney version 7)
   - Optional: `--chaos {0-50}` for variety (lower = more consistent)

5. **Quality scoring**: For each prompt, provide 7-dimension score (see midjourney-prompt-engineering skill)

**Output Format**:
```json
{
  "style_choice": "Pixar 3D animation",
  "consistency_tags": ["red-haired girl with freckles", "blue overalls", "curious expression"],
  "prompts": [
    {
      "shot_number": "1.1",
      "prompt": "full MidJourney prompt here",
      "parameters": "--ar 16:9 --style raw --v 7",
      "estimated_quality_score": {7-dimension object},
      "notes": "Establishing shot, introduces main character"
    },
    ...
  ]
}
```

Apply midjourney-prompt-engineering skill patterns for V7 syntax, style refs, and scoring.
```

**Skills to inject**: `midjourney-prompt-engineering`, `prompt-engineering-patterns` (few-shot examples), `character-design-sheet` (consistency tags)

**Expected output**: JSON object with 20-50 prompts (1 per shot) + metadata

---

## Final Deliverable

After Phase 6 approved:

```markdown
# Video Generation Complete — {Story Title}

## Prompts Listos para MidJourney

**Style**: {chosen_style}  
**Total Shots**: {N}  
**Estimated Duration**: {X} minutes  

### Character Consistency Tags (use in ALL prompts)
- {tag1}
- {tag2}
- ...

### Shot Prompts

**Scene 1: {Location}**

1. Shot 1.1 ({duration}sec)
   ```
   {full MidJourney prompt}
   ```
   
2. Shot 1.2 ({duration}sec)
   ```
   {full MidJourney prompt}
   ```

...

## Next Steps

1. Copy prompts to MidJourney (Discord bot or web app)
2. Generate images for each shot
3. Download all images
4. Assemble in video editor (order by shot number)
5. Add dialogue voice-over + music
6. Export final video

## Engram Archive

All phases saved to: `video-gen/{story-slug}/*`
- Phase 1: Character descriptions
- Phase 2: Dialogue script
- Phase 3: Scene descriptions
- Phase 4: Shot list
- Phase 5: Full script
- Phase 6: MidJourney prompts

Retrieve with: `mem_search(query="video-gen/{story-slug}", project="kogi-kids")`
```

Save final deliverable to Engram as `video-gen/{story-slug}/final-output`.

## Error Handling

### User Requests Changes Mid-Phase

- **Scenario**: User approves Phase 1-3, but wants to change character hair color in Phase 4
- **Action**: 
  1. Note the change request
  2. Re-run Character Agent with updated constraints
  3. Propagate changes to subsequent phases (Dialogue likely unchanged, Scenography may need color palette update, Cinematography unchanged, Scriptwriter needs character description update, Prompt Engineer needs consistency tags update)
  4. Ask user: "El cambio afecta {N} fases. ¿Re-ejecuto desde Character Agent o solo actualizo Prompt Engineer?"

### User Abandons Mid-Workflow

- **Scenario**: User stops responding after Phase 3
- **Action**: Save current state to Engram with status "paused"
- **Recovery**: Next session, search Engram, offer to resume

### Agent Fails (LLM error, timeout, etc.)

- **Scenario**: Sub-agent returns error or malformed output
- **Action**:
  1. Show error to user: "Phase {N} falló: {error message}"
  2. Offer options:
     - Retry same phase
     - Skip phase (proceed with placeholder)
     - Abort workflow
  3. Log error to Engram for debugging

## Compact Rules (for Registry Injection)

```
# video-generator-orchestrator compact rules

1. Orchestrate 6 sequential agents: Character → Dialogue → Scenography → Cinematography → Scriptwriter → Prompt Engineer
2. STOP after each agent, show results, WAIT for explicit approval ("apruebo", "sí", "continúa") before proceeding
3. Save each phase to Engram: topic_key = "video-gen/{story-slug}/phase-{N}", type = "decision"
4. If user gives feedback → re-run current agent with constraints, don't proceed to next
5. Character Agent: JSON array of characters with physical traits + MidJourney consistency tags (use character-design-sheet skill)
6. Dialogue Agent: JSON array of scenes with dialogue, duration, age-appropriate vocabulary (use kids-book-writer skill for word limits)
7. Scenography Agent: JSON array of scene descriptions with location, mood, color palette, props (use storytelling skill)
8. Cinematography Agent: JSON array of shots with type, angle, movement, duration (shorter for younger ages)
9. Scriptwriter Agent: Unified text script synchronizing all elements (use mockumentary-screenplay for structure)
10. Prompt Engineer Agent: MidJourney V7 prompts per shot with --ar 16:9, style consistency, character tags (use midjourney-prompt-engineering skill)
11. Recovery: Search Engram "video-gen/{story-slug}", find latest phase, offer to resume
12. Final output: Markdown document with all prompts + character consistency tags + Engram archive references
```

## Trigger Phrases

Activate this skill when user says:
- "genera video para esta historia"
- "crea prompts de MidJourney para este cuento"
- "transforma esta narrativa en video"
- "generate video from this story"
- "create MidJourney prompts for children's story"
- "video generation workflow"
- "orchestrate agents for video"

Also activate when user explicitly mentions `/video-gen` command.
