---
name: video-generator-orchestrator
description: Orchestrate 6 specialized agents to transform children's stories into MidJourney video prompts. Sequential workflow with human approval gates. Trigger when user asks to generate video from story, create MidJourney prompts from narrative, or says "genera video para esta historia".
---

# Video Generator Orchestrator

Transform children's stories (ages 2-10) into structured MidJourney video prompts through a 7-phase agent workflow with human validation at each step.

## Workflow Overview

```
Story Input → Initialize Structure (Phase -1) → Style Selection (Phase 0) → [Human Review] →
Character Agent (Phase 1) → [Human Review] → Dialogue Agent (Phase 2) → [Human Review] →
Scenography Agent (Phase 3) → [Human Review] → Cinematography Agent (Phase 4) → [Human Review] →
Scriptwriter Agent (Phase 5) → [Human Review] → Prompt Engineer Agent (Phase 6) → [Human Review] →
Generate README (Phase 7) → [Optional: Video Animation (Phase 8)] → Complete
```

**Core Principle**: STOP after each phase and WAIT for explicit human approval before proceeding to next phase.

**Triple Persistence**: All phases saved to:
- **Engram**: Topic keys `video-gen/{story-slug}/phase-{N}` for session recovery
- **Workflow Files**: `specs/workflows/{story-slug}/{NN}-{phase-name}.md` for Git versioning
- **Story Deliverables**: `stories/{story-slug}/{subdirectory}/{deliverable}.md` for direct MidJourney usage

## Orchestrator Instructions

### Initialization

When user provides a story:

1. **Validate story suitability**:
   - Target age range mentioned or inferable (2-10 years)
   - Has narrative structure (characters, setting, conflict/resolution)
   - Appropriate content for children (no violence, mature themes)
   
2. **Create identifiers**:
   - Engram topic key: `video-gen/{story-slug}/{timestamp}`
   - File path: `specs/workflows/{story-slug}/`

3. **Extract story slug**:
   - If story has a title, sanitize it: lowercase + replace spaces with hyphens + remove special chars
   - Example: "Luna y la Estrella Perdida" → "luna-y-la-estrella-perdida"
   - Sanitization pattern:
     ```python
     import re
     story_slug = story_title.lower()
     story_slug = re.sub(r'[^a-z0-9-]', '-', story_slug)
     story_slug = re.sub(r'-+', '-', story_slug)  # Collapse multiple hyphens
     story_slug = story_slug.strip('-')  # Remove leading/trailing hyphens
     ```

4. **Show workflow preview with style selection**:
   ```
   Voy a procesar tu historia en 9 fases (incluye inicialización de estructura + opcional video animation):
   
   -1. Initialize Structure → Creo directorios para todos los entregables
   0. Style Selection → Elegís el estilo visual general
   1. Character Agent → Descripciones de personajes (archivo + chat)
   2. Dialogue Agent → Diálogos apropiados para edad (archivo + chat)
   3. Scenography Agent → Escenografías y locaciones (archivo + chat)
   4. Cinematography Agent → Ángulos de cámara y composición (archivo + chat)
   5. Scriptwriter Agent → Guion completo ensamblado (archivo + chat)
   6. Prompt Engineer Agent → Prompts MidJourney listos (archivo + chat)
   7. Generate README → Guía paso a paso para usar prompts en MidJourney
   8. Video Animation (Opcional) → Generar videos animados con Runway Gen-3 API
   
   Después de cada fase te pido aprobación antes de continuar.
   
   Arrancamos con Style Selection: ¿Qué estilo visual preferís para este video?
   
   **Opciones**:
   1. **Disney 3D** — Render realista, personajes expresivos, iluminación cálida (ej: Frozen, Moana)
   2. **Pixar 3D Animation** — Stylized, colores vibrantes, texturas suaves (ej: Coco, Inside Out)
   3. **Studio Ghibli / Anime** — Dibujo a mano, detalles delicados, fondos pintados (ej: Totoro, Spirited Away)
   4. **2D Traditional Animation** — Disney clásico, líneas limpias, cel shading (ej: Lion King, Aladdin)
   5. **Stop Motion / Clay Animation** — Texturas táctiles, look artesanal (ej: Coraline, Kubo)
   6. **Children's Book Illustration** — Acuarela o gouache, estilo pictórico (ej: The Gruffalo)
   7. **Otro** — Describí el estilo que tenés en mente
   
   Elegí un número (1-7) o describí tu estilo preferido.
   ```

5. **Wait for style selection** — do NOT proceed until user selects style

## Phase -1: Initialize Story Structure

**Execution**: BEFORE Phase 0 (first step in workflow)

**Purpose**: Create physical directory structure for all story deliverables.

### Instructions

1. **Collect story slug** (from step 3 of Initialization)

2. **Create directory structure**:
   ```python
   from pathlib import Path
   
   base_dir = Path("stories") / story_slug
   subdirs = ["characters", "dialogues", "scenography", "cinematography", 
              "scripts", "prompts", "moodboard"]
   
   try:
       for subdir in subdirs:
           (base_dir / subdir).mkdir(parents=True, exist_ok=True)
       print(f"✅ Directory structure created at: stories/{story_slug}/")
       story_root = base_dir
   except Exception as e:
       print(f"❌ CRITICAL: Failed to create directory structure: {e}")
       print("⚠️ HALTING WORKFLOW - Cannot proceed without directory structure")
       raise  # HALT workflow
   ```

3. **Store `story_root` and `story_slug` in workflow state** for use in all subsequent phases

4. **Idempotent behavior**: Safe to re-run — existing directories preserved, `exist_ok=True` prevents errors

5. **Error handling**:
   - Directory creation failure → **CRITICAL** → **HALT entire workflow**
   - User notification: "No puedo crear los directorios. Verificá permisos de escritura."
   - Do NOT proceed to Phase 0 if this fails

6. **User confirmation**:
   ```
   ✅ Estructura de directorios creada en: stories/{story-slug}/
   
   Subdirectorios creados:
   - characters/ (descripciones de personajes)
   - dialogues/ (guiones de diálogo)
   - scenography/ (descripciones de escenografías)
   - cinematography/ (lista de tomas)
   - scripts/ (guion completo)
   - prompts/ (prompts MidJourney)
   - moodboard/ (referencias visuales que vos generarás)
   
   Ahora sí, arrancamos con Style Selection.
   ```

## File Writing Pattern (All Phases)

**Dual-Output Strategy**: All agent phases (1-6) write deliverables to BOTH file AND chat.

### Write Helper Pattern

```python
from pathlib import Path

def write_deliverable(content: str, story_slug: str, subdirectory: str, filename: str) -> dict:
    """
    Write deliverable with dual-output strategy.
    
    Args:
        content: Markdown content to write
        story_slug: Sanitized story slug (e.g., "luna-y-la-estrella-perdida")
        subdirectory: One of: characters, dialogues, scenography, cinematography, scripts, prompts
        filename: e.g., "characters.md"
    
    Returns:
        dict with status (success/fallback), path, content
    """
    try:
        # Construct path (cross-platform)
        output_path = Path("stories") / story_slug / subdirectory / filename
        
        # Create parent directory if needed (idempotent)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file (overwrite if exists)
        output_path.write_text(content, encoding="utf-8")
        
        print(f"✅ Written to: {output_path}")
        return {"status": "success", "path": str(output_path), "content": content}
    
    except Exception as e:
        print(f"⚠️ WARNING: File write failed: {e}")
        print(f"⚠️ Falling back to chat-only output")
        return {"status": "fallback", "error": str(e), "content": content}
```

### Usage in Phase Instructions

For **each phase** (1-6), after receiving agent output:

1. **Write to file**:
   ```python
   result = write_deliverable(
       content=agent_output_markdown,
       story_slug=story_slug,
       subdirectory="characters",  # or dialogues, scenography, etc.
       filename="characters.md"     # or dialogues.md, scenography.md, etc.
   )
   ```

2. **Write SPANISH version** (user-readable):
   ```python
   output_path_es = story_root / subdirectory / filename.replace(".md", "-es.md")
   
   create_file(
       filePath=str(output_path_es),
       content=agent_output_translated_to_spanish
   )
   ```

3. **Display in chat** (ALWAYS, even if file write succeeds):
   ```
   ## Fase {N}: {Agent Name} — Resultados
   
   ✅ Escrito en:
   - English: stories/{story-slug}/{subdirectory}/{filename}.md
   - Spanish: stories/{story-slug}/{subdirectory}/{filename}-es.md
   
   {agent_output_formatted_in_spanish}
   
   ¿Aprobás este resultado o querés cambios?
   ```

4. **Error handling**: File write failure is **NON-BLOCKING** for both files
   - Log WARNING
   - Continue workflow with chat-only output
   - Ensure user sees content regardless of file write status

### Dual-Language Output Strategy

**Why Two Languages**:
- **English version** (`{filename}.md`): Technical reference, MidJourney prompts work better in English
- **Spanish version** (`{filename}-es.md`): User-readable, easy review without translation friction

**Language Rules**:
- English file: All technical content, JSON structures, MidJourney prompts with parameters
- Spanish file: Same structure, translated descriptions/explanations, MidJourney prompts stay in English (for direct Discord copy-paste)
- Both files: Written sequentially by each agent

**Applies to**:
- Phase 1: `characters.md` / `characters-es.md`
- Phase 2: `dialogues.md` / `dialogues-es.md`
- Phase 3: `scenography.md` / `scenography-es.md`
- Phase 4: `cinematography.md` / `cinematography-es.md`
- Phase 5: `script.md` / `script-es.md`
- Phase 6: `prompts.md` / `prompts-es.md`

### Phase Execution Pattern

For EACH of the 7 phases (0-6):

1. **Launch sub-agent** (or present options for Phase 0) with:
   - Phase-specific instructions (see Agent Definitions below)
   - Relevant skills injected (compact rules from registry)
   - Previous phase outputs as context
   - **Selected style** (from Phase 0) as context for all subsequent phases
   - Story input

2. **Present results**:
   ```
   ## Fase {N}: {Agent Name} — Resultados
   
   {Agent output formatted clearly}
   
   ¿Aprobás este resultado o querés cambios?
   - "apruebo" / "sí" / "continúa" → procedo a siguiente fase
   - Feedback específico → re-ejecuto este agente con tus ajustes
   ```

3. **Save to dual persistence** (after approval):
   
   **A) Engram** (session recovery):
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
   
   **B) File system** (Git versioning):
   ```python
   create_file(
       filePath=f"specs/workflows/{story-slug}/{N:02d}-{phase-name}.md",
       content=f"""
       # Fase {N}: {Agent Name} — {Story Title}
       
       **Workflow**: video-generator-orchestrator
       **Story**: {story_title}
       **Target Age**: {age_range}
       **Date**: {current_date}
       **Status**: ✅ Approved
       
       ---
       
       {agent_output_formatted_as_markdown}
       
       ---
       
       ## User Feedback
       
       **User Response**: "{user_response}"
       **Changes Requested**: {changes_if_any}
       **Date Approved**: {current_date}
       
       ---
       
       ## Next Phase
       
       ✅ {Phase Name} approved → Proceed to **Phase {N+1}: {Next Agent Name}**
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

### 0. Style Selection (No sub-agent needed)

**Goal**: Define visual style direction for entire video before generating any content

**Orchestrator Action**: Present style options directly to user (no sub-agent launch needed)

**Options to Present**:

1. **Disney 3D** 
   - Realistic render, expressive characters, warm lighting
   - Examples: Frozen, Moana, Encanto
   - MidJourney style tags: `disney 3d render, pixar quality, warm lighting, detailed textures`
   - Best for: Stories with emotional depth, magical realism

2. **Pixar 3D Animation** 
   - Stylized, vibrant colors, soft textures, exaggerated proportions
   - Examples: Coco, Inside Out, Toy Story
   - MidJourney style tags: `pixar animation style, vibrant colors, soft lighting, stylized characters`
   - Best for: Whimsical stories, character-driven narratives

3. **Studio Ghibli / Anime** 
   - Hand-drawn look, delicate details, painted backgrounds, watercolor feel
   - Examples: My Neighbor Totoro, Spirited Away, Ponyo
   - MidJourney style tags: `studio ghibli style, hand drawn animation, watercolor backgrounds, anime`
   - Best for: Nature-focused stories, gentle pacing, emotional journeys

4. **2D Traditional Animation** 
   - Disney classic, clean lines, cel shading, bold colors
   - Examples: The Lion King, Aladdin, Mulan
   - MidJourney style tags: `traditional 2d animation, disney classic style, cel shading, clean lines`
   - Best for: Epic adventures, classic storytelling

5. **Stop Motion / Clay Animation** 
   - Tactile textures, handcrafted look, imperfect charm
   - Examples: Coraline, Kubo and the Two Strings, Wallace & Gromit
   - MidJourney style tags: `stop motion animation, clay animation, textured surfaces, handcrafted look`
   - Best for: Quirky stories, tactile worlds, unique aesthetics

6. **Children's Book Illustration** 
   - Watercolor or gouache, painterly, soft edges, storybook feel
   - Examples: The Gruffalo, Where the Wild Things Are, The Very Hungry Caterpillar
   - MidJourney style tags: `children's book illustration, watercolor painting, gouache, soft edges, storybook art`
   - Best for: Gentle stories, bedtime tales, educational content

7. **Other / Custom**
   - User describes their preferred style
   - Orchestrator translates to MidJourney style tags

**User Selection Process**:
```
¿Qué estilo visual preferís para este video?

1. Disney 3D (Frozen, Moana)
2. Pixar 3D (Coco, Inside Out)
3. Studio Ghibli / Anime (Totoro, Spirited Away)
4. 2D Traditional Animation (Lion King, Aladdin)
5. Stop Motion / Clay (Coraline, Kubo)
6. Children's Book Illustration (The Gruffalo)
7. Otro (describí tu estilo)

Elegí un número (1-7) o describí el estilo.
```

**Output Format**:
```json
{
  "style_choice": "Pixar 3D Animation",
  "midjourney_style_tags": "pixar animation style, vibrant colors, soft lighting, stylized characters",
  "art_direction_notes": "Focus on exaggerated expressions, round shapes, warm color palette. Characters should have large expressive eyes and simplified but appealing designs.",
  "reference_films": ["Coco", "Inside Out", "Toy Story"],
  "color_palette_guidance": "Vibrant but not oversaturated, warm tones preferred, magical lighting"
}
```

**Save to File**: `specs/workflows/{story-slug}/00-style-selection.md`

**Pass to All Subsequent Agents**: Style selection context MUST be included in prompts for Character, Scenography, Cinematography, and Prompt Engineer agents.

---

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

**Output file**: Pass `output_path` parameter to character-agent:
```python
output_path = story_root / "characters" / "characters.md"  # Absolute path
```

**Expected output**: JSON array of 2-8 character descriptions written to file AND displayed in chat

---

### 2. Dialogue Agent

**Goal**: Write age-appropriate dialogue with pacing suitable for video

**Sub-agent prompt**:
```
Given these character descriptions:

{character_descriptions}

And this story:

{story_input}

**Selected Style**: {selected_style}
**Target Age**: {target_age}

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

Apply kids-book-writer skill for vocabulary and storytelling skill for pacing. Pacing should match {selected_style} conventions (Disney 3D: cinematic pacing, Ghibli: gentle pacing, etc.)
```

**Skills to inject**: `kids-book-writer`, `storytelling`

**Output file**: Pass `output_path` parameter to dialogue-agent:
```python
output_path = story_root / "dialogues" / "dialogues.md"  # Absolute path
```

**Expected output**: JSON array of scenes with dialogue objects written to file AND displayed in chat

---

### 3. Scenography Agent

**Goal**: Describe settings, locations, and atmosphere for each scene

**Sub-agent prompt**:
```
Given this dialogue script:

{dialogue_script}

And these characters:

{character_descriptions}

**Selected Style**: {selected_style}

Generate scenography descriptions for each scene matching {selected_style} visual conventions:

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

**Output file**: Pass `output_path` parameter to scenography-agent:
```python
output_path = story_root / "scenography" / "scenography.md"  # Absolute path
```

**Metadata extraction**: Count scene descriptions for README (store as `scene_count` in workflow state)

**Expected output**: JSON array of scene descriptions (1 per dialogue scene) written to file AND displayed in chat

---

### 4. Cinematography Agent

**Goal**: Define camera angles, framing, and shot composition

**Sub-agent prompt**:
```
Given:
- Dialogue script: {dialogue_script}
- Scene descriptions: {scene_descriptions}
- Target age: {target_age}
- Selected style: {selected_style}

Generate shot list for each scene matching {selected_style} cinematography conventions:

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

**Output file**: Pass `output_path` parameter to cinematography-agent:
```python
output_path = story_root / "cinematography" / "cinematography.md"  # Absolute path
```

**Expected output**: JSON array of 20-50 shots total (depends on story length) written to file AND displayed in chat

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
- Selected style: {selected_style}

Generate unified script in professional format for {selected_style} production:

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

**Output file**: Pass `output_path` parameter to scriptwriter-agent:
```python
output_path = story_root / "scripts" / "script.md"  # Absolute path
```

**Expected output**: Full text script (plain text or Markdown formatted) written to file AND displayed in chat

---

### 6. Prompt Engineer Agent

**Goal**: Transform script into MidJourney V7 prompts ready for generation

**Sub-agent prompt**:
```
Given this complete script:

{full_script}

**Selected Style**: {selected_style}

Generate MidJourney V7 prompts for EACH shot using {selected_style} tags consistently:

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

**Output file**: Pass `output_path` parameter to prompt-engineer-agent:
```python
output_path = story_root / "prompts" / "prompts.md"  # Absolute path
```

**Metadata extraction**: Extract `character_count` from character descriptions for README (store in workflow state)

**Expected output**: JSON object with 20-50 prompts (1 per shot) + metadata written to file AND displayed in chat

---

## Phase 7: Generate README

**Execution**: AFTER Phase 6 (Prompt Engineer Agent) completes and user approves

**Purpose**: Auto-generate README.md with step-by-step MidJourney workflow instructions for the user.

### Instructions

1. **Collect metadata from workflow state**:
   - `story_title` (human-readable title)
   - `story_slug` (sanitized slug)
   - `selected_style` (from Phase 0)
   - `character_count` (extracted from Phase 1 output — count character sections)
   - `scene_count` (extracted from Phase 3 output — count scene descriptions)
   - `story_root` (from Phase -1)

2. **Populate README template** (see template below)

3. **Write README to file**:
   ```python
   readme_path = story_root / "README.md"
   try:
       readme_path.write_text(readme_content, encoding="utf-8")
       print(f"✅ README.md created at: {readme_path}")
   except Exception as e:
       print(f"⚠️ WARNING: README generation failed: {e}")
       # Non-blocking — continue workflow
   ```

4. **Display confirmation**:
   ```
   ✅ README.md generado en: stories/{story-slug}/README.md
   
   Este archivo contiene:
   - Resumen del proyecto
   - Instrucciones paso a paso para MidJourney
   - Referencias a todos los archivos generados
   
   Ya podés empezar a generar imágenes siguiendo el README!
   ```

### README Template

```markdown
# {story_title} — Video Generation Workflow

**Style**: {selected_style}  
**Characters**: {character_count}  
**Scenes**: {scene_count}  
**Generated**: {current_date}

---

## Overview

This directory contains all deliverables for generating the "{story_title}" video using MidJourney V7. Follow the step-by-step workflow below to transform these prompts into a complete video.

## Prerequisites

- MidJourney V7 subscription (Standard or Pro recommended)
- GitHub account (for hosting moodboard reference images)
- Video editing software (CapCut, Adobe Premiere, DaVinci Resolve, or iMovie)
- Audio recording setup for voice-over (optional but recommended)

## File Reference

| File | Description |
|------|-------------|
| [characters/characters.md](characters/characters.md) | Character descriptions with consistency tags |
| [dialogues/dialogues.md](dialogues/dialogues.md) | Scene-by-scene dialogue script |
| [scenography/scenography.md](scenography/scenography.md) | Environment and setting descriptions |
| [cinematography/cinematography.md](cinematography/cinematography.md) | Camera angles and shot list |
| [scripts/script.md](scripts/script.md) | Complete unified production script |
| [prompts/prompts.md](prompts/prompts.md) | **MidJourney prompts (START HERE)** |
| moodboard/ | Generated character references (you'll create these) |

---

## Step-by-Step Workflow

### Step 1: Generate Character References (Moodboard-First Approach)

**Why**: Character consistency across all scenes requires reference images. Generate these FIRST before scene images.

1. Open [prompts/prompts.md](prompts/prompts.md)
2. Find the "Character Reference Prompts" section (if included) OR use character descriptions from [characters/characters.md](characters/characters.md) to create simple turnaround prompts:
   ```
   {Character Name}, {physical description from characters.md}, neutral pose, white background, character turnaround sheet, front view, side view, back view, {selected_style} --ar 16:9 --v 7
   ```
3. Generate in MidJourney (Discord bot or web app)
4. Select best generation for EACH character
5. Download images with high resolution (upscale if needed)
6. Save to `moodboard/` directory:
   - `moodboard/{character-name}-reference.png`
   - Example: `moodboard/luna-reference.png`

**Result**: You now have 1 reference image per character.

### Step 2: Upload Moodboard to GitHub (for --oref URLs)

**Why**: MidJourney's `--oref` parameter requires publicly accessible image URLs. GitHub provides free hosting.

1. Commit `moodboard/` directory to this Git repository:
   ```bash
   git add moodboard/
   git commit -m "Add character reference images for {story_title}"
   git push origin main
   ```
2. Get GitHub raw URLs for each image:
   - Navigate to GitHub repo in browser
   - Open `moodboard/{character-name}-reference.png`
   - Click "Raw" button
   - Copy URL (format: `https://raw.githubusercontent.com/{user}/{repo}/main/stories/{story-slug}/moodboard/{character}-reference.png`)

3. **Update prompts file**: Replace placeholders in `prompts/prompts.md`:
   - Find: `{luna_moodboard_url}` (or similar placeholder)
   - Replace with: actual GitHub raw URL
   - Repeat for all characters

**Result**: All prompts now have working `--oref` URLs for character consistency.

### Step 3: Generate Style Reference (Optional but Recommended)

**Why**: `--sref` ensures consistent art style across all shots (lighting, color grading, texture).

1. Create a simple style reference prompt:
   ```
   {selected_style} style reference, color palette sample, lighting and mood example, no characters, environment only --ar 16:9 --v 7
   ```
2. Generate in MidJourney
3. Select best result that captures the desired style
4. Download and save to `moodboard/style-reference.png`
5. Upload to GitHub (repeat Step 2 process)
6. Get GitHub raw URL
7. **Update prompts file**: Add `--sref {style_url}` to ALL prompts in `prompts/prompts.md`

**Result**: Consistent style across all generated scenes.

### Step 4: Generate Scene Images

**Now you're ready for the main generation!**

1. Open [prompts/prompts.md](prompts/prompts.md)
2. Copy prompts in ORDER (Shot 1.1, 1.2, 1.3, etc.)
3. Paste each prompt into MidJourney
4. For EACH prompt:
   - Wait for 4 variations to generate
   - Select the best one (look for: correct character appearance, matching style, good composition)
   - Upscale if needed
   - Download with original filename pattern: `shot-1-1.png`, `shot-1-2.png`, etc.
5. Save all images to a new folder: `generated-images/`

**Tip**: Use MidJourney's `/describe` command on your moodboard images to verify character consistency if a shot looks off.

**Estimated time**: {scene_count * 3} minutes (assuming ~3 min per shot including selection)

### Step 5: Review and Iterate

1. Lay out all generated images in order (use a slideshow or grid view)
2. Check for:
   - ✅ Character consistency (same hair, clothing, features across shots)
   - ✅ Style consistency (lighting, colors, art style match)
   - ✅ Scene continuity (props, locations, time of day match script)
3. **If any shot is off**:
   - Go back to that prompt
   - Adjust parameters (increase `--ow` for more character weight, or tweak description)
   - Regenerate that specific shot
4. Replace the image in `generated-images/`

**Goal**: All {scene_count} shots look like they belong to the SAME video.

### Step 6: Assemble Video

1. **Import images** to video editor in shot order
2. **Set durations**: Match duration estimates from [cinematography/cinematography.md](cinematography/cinematography.md)
   - Typical: 3-5 seconds per shot for ages 2-5, 4-7 seconds for ages 6-10
3. **Add transitions**: Cuts (most common), fades, or dissolves between scenes
4. **Record voice-over**: Use dialogue from [dialogues/dialogues.md](dialogues/dialogues.md)
   - Record each character's lines separately (or hire voice actors)
   - Import audio tracks
   - Sync dialogue to corresponding shots
5. **Add background music**: Choose age-appropriate instrumental tracks
6. **Add sound effects** (optional): Footsteps, magic sparkles, door creaks, etc.
7. **Color grading** (optional): Slight adjustments for mood consistency
8. **Export video**:
   - Format: MP4 (H.264)
   - Resolution: 1920x1080 (1080p) or 3840x2160 (4K)
   - Frame rate: 24fps (cinematic) or 30fps (standard)

**Result**: Complete video ready for sharing!

---

## Troubleshooting

### Character doesn't look consistent across shots

**Solution**: 
- Increase `--ow` parameter (character weight) from 200 to 300 or 400
- Ensure `--oref` URL is correct and accessible (test in browser)
- Regenerate moodboard reference with more detailed description

### Style is inconsistent between shots

**Solution**:
- Add `--sref` parameter with style reference URL (see Step 3)
- Use SAME `--style` code across all prompts
- Check that `--v 7` is included in every prompt

### Prompt is too long (over 350 words)

**Solution**:
- Remove redundant descriptors
- Focus on: character, action, setting, camera angle, lighting
- MidJourney V7 is intelligent — avoid over-prompting

### Image doesn't match the script description

**Solution**:
- Re-read the shot description in [cinematography/cinematography.md](cinematography/cinematography.md)
- Adjust prompt to emphasize the KEY element (character emotion, specific prop, camera angle)
- Regenerate with adjusted prompt

---

## Credits

**Workflow generated by**: video-generator-orchestrator (kogi-kids project)  
**MidJourney Version**: V7  
**Story**: {story_title}  
**Date**: {current_date}

---

## Next Steps After Video Completion

1. Upload to YouTube, Vimeo, or social media
2. Share with target audience (parents, educators, kids)
3. Gather feedback for future stories
4. Archive project files for reference

**🎉 Enjoy your video creation journey!**
```

---

## Phase 8: Video Animation (Optional)

**Execution**: AFTER Phase 7 (README) completes  
**Condition**: User has Runway API key + budget, and storyboard has HIGH priority shots

**Purpose**: Generate actual animated videos from HIGH priority static renders using Runway Gen-3 API automation.

### Pre-Requisites Check

Before offering Phase 8, verify:

1. **Runway API key configured**: Check if `scripts/.env` exists and contains valid `RUNWAY_API_KEY`
   - If missing: Inform user they need API key from https://runwayml.com
   - Show setup instructions: "Copy `scripts/.env.example` to `scripts/.env` and add your API key"

2. **HIGH priority shots exist**: Check if `stories/{story-slug}/storyboard-timing.md` has shots marked with:
   - ⭐ SPECTACLE
   - 💖 EMOTIONAL CORE  
   - 🦸‍♀️ HERO MOMENT
   - 💫 MONEY SHOT
   - Or explicit `priority: HIGH` comments

3. **Render files exist**: Verify that render files referenced in HIGH priority shots exist in `stories/{story-slug}/renders/`

If any prerequisite fails, skip Phase 8 and show reason: "Phase 8 omitida: {reason}"

### Workflow

1. **Discover HIGH Priority Shots**
   
   Run discovery via Python script (DO NOT run as subprocess — use inline Python):
   ```python
   import sys
   sys.path.append("scripts")
   from runway_animate import discover_shots, load_config, estimate_cost
   
   try:
       config = load_config()
       shots = discover_shots(story_slug, config)
       
       if not shots:
           print("⚠️ No HIGH priority shots found. Skipping Phase 8.")
           return None  # Skip Phase 8
       
       shot_ids = [s['shot_id'] for s in shots]
       min_cost, max_cost = estimate_cost(shots, config['default_model'], 
                                          config['default_duration'])
       
       print(f"📋 Found {len(shots)} HIGH priority shots:")
       for shot in shots:
           marker = f" {shot['spectacle_marker']}" if shot['spectacle_marker'] else ""
           print(f"   • {shot['shot_id']}: {shot['title']}{marker}")
       print(f"\n💰 Estimated cost: ${min_cost} - ${max_cost} USD")
       print(f"   Model: {config['default_model']} (${MODEL_COSTS[config['default_model']]}/sec)")
       
   except FileNotFoundError as e:
       print(f"⚠️ Storyboard not found: {e}")
       return None  # Skip Phase 8
   except ValueError as e:
       print(f"⚠️ Configuration error: {e}")
       return None  # Skip Phase 8
   ```

2. **Present Approval Gate**
   
   Show discovered shots + cost estimate and ASK for approval:
   
   ```
   🎬 Phase 8: Video Animation (Opcional)
   
   Encontré {N} shots de ALTA prioridad para animar con Runway Gen-3:
   
   {list of shot_ids with titles and markers}
   
   💰 Costo estimado: ${min_cost} - ${max_cost} USD
   Modelo: {model} (${cost_per_sec}/segundo)
   Duración por video: {duration}s
   
   Runway generará videos animados a partir de tus renders estáticos.
   
   ¿Querés generar estos videos?
   
   Opciones:
   - "apruebo" / "sí" / "continúa" → Generar todos los videos
   - "solo 2B,7C" → Generar solo shots específicos (lista separada por comas)
   - "no" / "omitir" / "skip" → Saltar Phase 8
   ```
   
   **WAIT for user response** — do NOT proceed without explicit approval.

3. **Invoke Runway Script**
   
   Based on user response:
   
   - **User approves all shots**:
     ```python
     import subprocess
     result = subprocess.run([
         "python", "scripts/runway_animate.py",
         "--story", story_slug,
         "--model", config['default_model']
     ], capture_output=True, text=True, cwd=project_root)
     
     if result.returncode != 0:
         print(f"❌ Runway script failed:\n{result.stderr}")
         # Show error but don't halt workflow
     else:
         print(result.stdout)
     ```
   
   - **User specifies shot IDs** (e.g., "solo 2B,7C"):
     Extract shot IDs from response, then:
     ```python
     selected_ids = extract_shot_ids_from_response(user_response)  # e.g., ['2B', '7C']
     
     result = subprocess.run([
         "python", "scripts/runway_animate.py",
         "--story", story_slug,
         "--shots", ",".join(selected_ids),
         "--model", config['default_model']
     ], capture_output=True, text=True, cwd=project_root)
     ```
   
   - **User declines**:
     ```
     ✅ Phase 8 omitida por el usuario.
     ```
     Save status to Engram and proceed to workflow completion.

4. **Parse Results**
   
   After script completes, read `stories/{story-slug}/animations/progress.json`:
   
   ```python
   import json
   from pathlib import Path
   
   progress_path = Path(f"stories/{story_slug}/animations/progress.json")
   
   if progress_path.exists():
       with open(progress_path) as f:
           progress = json.load(f)
       
       results = progress['results']
       successful = [r for r in results if r['success']]
       failed = [r for r in results if not r['success']]
       total_credits = progress['total_credits_used']
       
       print(f"\n🏁 Runway Generation Complete")
       print(f"{'='*60}")
       print(f"✅ Successful: {len(successful)}/{len(results)} videos")
       print(f"❌ Failed: {len(failed)}/{len(results)} videos")
       print(f"💰 Credits used: ${total_credits:.2f}")
       
       if successful:
           print(f"\n✅ Generated videos saved to:")
           for r in successful:
               print(f"   • {r['output_path']}")
       
       if failed:
           print(f"\n❌ Failed shots:")
           for r in failed:
               print(f"   • {r['shot_id']}: {r['error']}")
   else:
       print("⚠️ Progress file not found — check script output for errors")
   ```

5. **Update README with Animation Status**
   
   Append Phase 8 section to existing README.md:
   
   ```markdown
   
   ---
   
   ## Phase 8: Generated Videos (Runway Gen-3)
   
   **Status**: {len(successful)}/{len(results)} videos generated  
   **Model**: {config['default_model']}  
   **Total Cost**: ${total_credits:.2f} USD  
   **Date**: {datetime.now().strftime('%Y-%m-%d')}  
   
   ### Generated Videos
   
   {for each successful result:}
   - **Shot {shot_id}**: [{title}]({output_path}) — {duration}s, ${credits_used:.2f}
   
   {if failed:}
   ### Failed Shots
   
   {for each failed result:}
   - **Shot {shot_id}**: {error}
   
   ### Resume Incomplete Generation
   
   If some shots failed, you can resume generation:
   
   ```bash
   python scripts/runway_animate.py --story {story-slug} --resume
   ```
   
   This will skip already-completed shots and retry failed ones.
   ```
   
   Write updated README back to file.

6. **Persist to Engram**
   
   Save Phase 8 result to Engram:
   
   ```python
   mcp_engram_mem_save(
       title=f"Phase 8: Video Animation — {story_title}",
       content=f"""
       **What**: Generated {len(successful)}/{len(results)} animated videos using Runway Gen-3
       **Why**: Transform HIGH priority static renders into animated video clips
       **Where**: stories/{story_slug}/animations/
       **Learned**: 
       - Successful shots: {', '.join([r['shot_id'] for r in successful])}
       - Failed shots: {', '.join([r['shot_id'] for r in failed]) if failed else 'None'}
       - Total cost: ${total_credits:.2f}
       - Model: {config['default_model']}
       """,
       type="architecture",
       topic_key=f"video-gen/{story_slug}/phase-8",
       project="kogi-kids"
   )
   ```

### Error Handling

- **Script exit code 1**: Report error, show logs from stderr, workflow continues (Phase 8 non-blocking)
- **Budget exceeded**: Show warning with breakdown:
  ```
  ⚠️ Estimated cost (${max_cost}) exceeds budget limit (${config['max_budget']}).
  
  Opciones:
  1. Reducir cantidad de shots (especificar IDs con --shots)
  2. Aumentar RUNWAY_MAX_BUDGET en scripts/.env
  3. Omitir Phase 8
  ```
- **No HIGH priority shots**: Skip Phase 8 automatically with message:
  ```
  ℹ️ No HIGH priority shots found in storyboard. Skipping Phase 8.
  
  Para agregar shots de alta prioridad, agregá marcadores en storyboard-timing.md:
  - ⭐ SPECTACLE
  - 💖 EMOTIONAL CORE
  - 🦸‍♀️ HERO MOMENT
  - 💫 MONEY SHOT
  ```
- **Missing API key**: Show setup instructions, skip Phase 8
- **API rate limit**: Script will retry with exponential backoff automatically (handled in runway_animate.py)
- **Content moderation failure**: Individual shot fails but others proceed (partial success)

### Compact Rules for Phase 8

```
# Phase 8: Video Animation (video-generator-orchestrator)

1. Check prerequisites: Runway API key in scripts/.env, HIGH priority shots exist, render files exist
2. Discover HIGH priority shots from storyboard-timing.md (markers: ⭐ SPECTACLE, 💖 EMOTIONAL, 🦸 HERO, 💫 MONEY)
3. Present approval gate: show shot list + cost estimate, WAIT for user approval
4. If approved: invoke scripts/runway_animate.py with --story {story-slug} [--shots {ids}]
5. Parse results from stories/{story-slug}/animations/progress.json
6. Report: "{successful}/{total} videos, ${credits} used, {failed} failed"
7. Update README.md with Phase 8 section (generated videos + resume instructions)
8. Save to Engram: video-gen/{story-slug}/phase-8
9. Non-blocking: errors in Phase 8 don't halt workflow, user can retry manually
10. Resume support: --resume flag skips completed shots, retries failed ones
```

---

## Final Deliverable

After Phase 7 (and optionally Phase 8) approved:

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

1. Orchestrate 7 sequential phases: Style Selection → Character → Dialogue → Scenography → Cinematography → Scriptwriter → Prompt Engineer
2. Phase 0 (Style Selection): Present 6 visual style options (Disney 3D, Pixar, Ghibli/Anime, 2D Traditional, Stop Motion, Book Illustration), wait for user choice
3. STOP after each phase, show results, WAIT for explicit approval ("apruebo", "sí", "continúa") before proceeding
4. Dual persistence: Save to Engram (topic_key = "video-gen/{story-slug}/phase-{N}") AND file (specs/workflows/{story-slug}/{NN}-{phase}.md)
5. Pass selected style context to ALL subsequent agents (Phase 1-6) as art direction constraint
6. If user gives feedback → re-run current agent with constraints, don't proceed to next
7. Character Agent: JSON array of characters with physical traits + MidJourney consistency tags matching selected style (use character-design-sheet skill)
8. Dialogue Agent: JSON array of scenes with dialogue, duration, age-appropriate vocabulary (use kids-book-writer skill for word limits)
9. Scenography Agent: JSON array of scene descriptions with location, mood, color palette, props matching selected style (use storytelling skill)
10. Cinematography Agent: JSON array of shots with type, angle, movement, duration adapted to selected animation style
11. Scriptwriter Agent: Unified text script synchronizing all elements (use mockumentary-screenplay for structure)
12. Prompt Engineer Agent: MidJourney V7 prompts per shot with --ar 16:9, selected style tags, character consistency tags (use midjourney-prompt-engineering skill)
13. Recovery: Search Engram "video-gen/{story-slug}" OR read specs/workflows/{story-slug}/*.md, find latest phase, offer to resume
14. Final output: Markdown document with all prompts + character consistency tags + style notes + Engram/file archive references
```

---

## MCP Agent Discovery (NEW — Migration to MCP Protocol)

### Feature Flag

The orchestrator supports TWO execution modes controlled by `USE_MCP_AGENTS` environment variable:

- **`USE_MCP_AGENTS=true`**: Load agents from `agents/` directory via MCP protocol (NEW)
- **`USE_MCP_AGENTS=false`** (default): Use legacy inline agent definitions from SKILL.md.legacy

**Graceful Degradation**: If MCP mode fails for ANY reason (missing agent, corrupt schema, filesystem error), orchestrator logs warning and falls back to legacy mode. Workflow NEVER breaks due to MCP issues.

### Discovery Algorithm

When `USE_MCP_AGENTS=true`, orchestrator discovers agents at workflow initialization:

```python
def discover_agents(agents_dir: Path = Path("agents")) -> dict[str, AgentConfig]:
    """
    Scan agents/ directory for MCP-compliant agents.
    
    Returns:
        dict mapping phase names to AgentConfig objects
        Example: {"character-agent": AgentConfig(...), "dialogue-agent": AgentConfig(...)}
    
    Raises:
        NoAgentsFoundError: If agents/ directory empty or no valid agents
        InvalidMCPSchemaError: If any agent.json fails validation (fail-fast)
    """
    agents = {}
    
    # Scan agents/*/agent.json files
    for agent_path in agents_dir.glob("*/agent.json"):
        try:
            config = json.loads(agent_path.read_text(encoding='utf-8'))
            
            # Validate MCP schema (fail-fast on first error)
            validate_mcp_schema(config, agent_path)
            
            # Build agent config
            agent_name = config["name"]
            agents[agent_name] = AgentConfig(
                name=agent_name,
                config=config,
                prompt_path=agent_path.parent / "prompt.md"
            )
            
        except Exception as e:
            # Fail-fast: don't partially load agents
            raise InvalidAgentError(
                f"Agent {agent_path.parent.name} invalid: {e}\n"
                f"Path: {agent_path}"
            )
    
    if not agents:
        raise NoAgentsFoundError(
            f"No valid MCP agents found in {agents_dir}\n"
            f"Ensure agents/ directory contains subdirectories with agent.json files"
        )
    
    logger.info(f"✅ Discovered {len(agents)} MCP agents: {list(agents.keys())}")
    return agents
```

### Schema Validation

```python
def validate_mcp_schema(config: dict, path: Path):
    """
    Validate MCP 2024-11-05 schema compliance.
    
    Raises:
        InvalidMCPSchemaError: If required fields missing or invalid
    """
    # Required top-level fields
    required_fields = ["name", "version", "runtime", "protocol_version", "capabilities", 
                       "inputs", "outputs", "dependencies"]
    missing = [field for field in required_fields if field not in config]
    
    if missing:
        raise InvalidMCPSchemaError(
            f"Missing required fields: {missing}\n"
            f"Path: {path}\n"
            f"Required: {required_fields}"
        )
    
    # Validate protocol version
    if config["protocol_version"] != "2024-11-05":
        raise InvalidMCPSchemaError(
            f"Unsupported protocol version: {config['protocol_version']}\n"
            f"Expected: 2024-11-05\n"
            f"Path: {path}"
        )
    
    # Validate runtime
    if config["runtime"] != "mcp":
        raise InvalidMCPSchemaError(
            f"Invalid runtime: {config['runtime']}\n"
            f"Expected: 'mcp'\n"
            f"Path: {path}"
        )
    
    # Validate capabilities structure
    if not isinstance(config["capabilities"], dict):
        raise InvalidMCPSchemaError(
            f"capabilities must be object with 'tools', 'resources', 'prompts' arrays\n"
            f"Path: {path}"
        )
    
    # Validate dependencies.skills exists (required for skill injection)
    if "skills" not in config.get("dependencies", {}):
        raise InvalidMCPSchemaError(
            f"dependencies.skills array required (can be empty [])\n"
            f"Path: {path}"
        )
```

### Load MCP Agent (with Skill Injection)

```python
def load_mcp_agent(phase_name: str, agents_registry: dict) -> AgentPrompt:
    """
    Load MCP agent for given phase, inject skill compact rules.
    
    Args:
        phase_name: "character-agent", "dialogue-agent", etc.
        agents_registry: Output from discover_agents()
    
    Returns:
        AgentPrompt with system prompt + injected skill rules
    
    Raises:
        AgentNotFoundError: If phase_name not in registry
        FileNotFoundError: If prompt.md missing
    """
    # Check agent exists
    if phase_name not in agents_registry:
        available = list(agents_registry.keys())
        raise AgentNotFoundError(
            f"Agent '{phase_name}' not found in agents/\n"
            f"Available agents: {available}\n"
            f"Expected path: agents/{phase_name}/agent.json"
        )
    
    agent_config = agents_registry[phase_name]
    
    # Read prompt.md
    if not agent_config.prompt_path.exists():
        raise FileNotFoundError(
            f"prompt.md not found for {phase_name}\n"
            f"Expected path: {agent_config.prompt_path}"
        )
    
    base_prompt = agent_config.prompt_path.read_text(encoding='utf-8')
    
    # Resolve skill compact rules from dependencies
    skill_names = agent_config.config["dependencies"]["skills"]
    compact_rules = resolve_compact_rules_from_registry(skill_names)
    
    # Inject rules into prompt
    prompt_with_context = f"""{base_prompt}

---

## Project Standards (auto-resolved from skill-registry)

{compact_rules}
"""
    
    return AgentPrompt(
        name=phase_name,
        config=agent_config.config,
        prompt=prompt_with_context
    )
```

### Skill Resolution Injection

**Purpose**: Each agent declares skill dependencies in `agent.json` → orchestrator reads skill-registry.md → injects compact rules BEFORE launching agent.

**Workflow**:
1. Agent declares: `"dependencies": {"skills": ["character-design-sheet", "kids-book-writer"]}`
2. Orchestrator reads: `mem_search(query="skill-registry", project="kogi-kids")` → `mem_get_observation(id)`
3. Orchestrator extracts compact rules for those 2 skills from registry
4. Orchestrator injects rules as `## Project Standards (auto-resolved)` section in agent prompt
5. Agent receives full context WITHOUT needing to read registry itself

**Implementation**:
```python
def resolve_compact_rules_from_registry(skill_names: list[str]) -> str:
    """
    Read skill-registry.md, extract compact rules for specified skills.
    
    Returns:
        Markdown text with compact rules for requested skills
    """
    # Try Engram first
    try:
        search_result = mcp_engram_mem_search(
            query="skill-registry", 
            project="kogi-kids"
        )
        if search_result:
            registry_content = mcp_engram_mem_get_observation(id=search_result[0].id)
        else:
            # Fallback: read from file
            registry_content = Path(".atl/skill-registry.md").read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Skill registry not found: {e}. Proceeding without project-specific standards.")
        return ""
    
    # Parse compact rules section
    compact_rules = []
    in_compact_section = False
    current_skill = None
    
    for line in registry_content.split('\n'):
        if line.startswith("## Compact Rules"):
            in_compact_section = True
            continue
        
        if in_compact_section:
            if line.startswith("### "):
                current_skill = line[4:].strip()
            elif current_skill in skill_names and line.strip().startswith("-"):
                compact_rules.append(f"**{current_skill}**: {line.strip()}")
    
    return "\n".join(compact_rules)
```

### Error Types

**AgentNotFoundError**:
```python
class AgentNotFoundError(Exception):
    """Raised when requested agent not in agents/ directory."""
    pass
```

**InvalidMCPSchemaError**:
```python
class InvalidMCPSchemaError(Exception):
    """Raised when agent.json fails MCP 2024-11-05 validation."""
    pass
```

**NoAgentsFoundError**:
```python
class NoAgentsFoundError(Exception):
    """Raised when agents/ directory empty or no valid agents."""
    pass
```

### Execution Flow (MCP Mode)

```
User: "genera video para esta historia"
  ↓
Orchestrator: Check USE_MCP_AGENTS flag
  ├── TRUE → discover_agents("agents/") 
  │   ├── Scan agents/*/agent.json
  │   ├── Validate schemas (fail-fast if any invalid)
  │   └── Build registry: {phase_name: AgentConfig}
  │
  ├── Phase 1: load_mcp_agent("character-agent", registry)
  │   ├── Check agent exists in registry
  │   ├── Read agents/character-agent/prompt.md
  │   ├── Resolve skills: ["character-design-sheet", "kids-book-writer"]
  │   ├── Inject compact rules from skill-registry
  │   └── Launch sub-agent with full context
  │
  ├── Phase 2-6: Repeat for remaining agents
  │
  └── Complete: All artifacts persisted (Engram + files)
```

### Fallback Flow (MCP Error or Legacy Mode)

```
Orchestrator: Check USE_MCP_AGENTS flag
  ├── FALSE → load_legacy_agent("SKILL.md.legacy", phase)
  │   └── Use inline agent definitions (original behavior)
  │
  ├── TRUE but MCP discovery fails → 
  │   ├── Log warning: "MCP discovery failed: {error}. Falling back to legacy mode."
  │   └── load_legacy_agent("SKILL.md.legacy", phase)
  │
  └── Complete: Workflow continues without interruption
```

### Rollback Procedure

If issues arise with MCP mode:

1. Set `USE_MCP_AGENTS=false` (environment variable or config)
2. Restart orchestrator (or reload skill)
3. Orchestrator uses `SKILL.md.legacy` inline definitions
4. No file deletion needed — `agents/` coexists with legacy
5. **Rollback time**: < 30 seconds

---

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

---

## Manual Validation Checklist

After implementing the file output workflow, validate manually (automated tests disabled):

### Test 1: Directory Creation
- [ ] Start workflow with test story "Test Luna Story"
- [ ] Verify directory created: `stories/test-luna-story/`
- [ ] Verify 7 subdirectories exist: characters/, dialogues/, scenography/, cinematography/, scripts/, prompts/, moodboard/
- [ ] Re-run workflow (same story) — verify no errors (idempotent)

### Test 2: Character Agent File Output
- [ ] Run Character Agent for test story
- [ ] Verify file exists: `stories/test-luna-story/characters/characters.md`
- [ ] Verify file content matches chat output (identical JSON)
- [ ] Verify file is UTF-8 encoded (check with editor)

### Test 3: README Generation
- [ ] Complete full workflow (Phases -1 through 6)
- [ ] Verify README created: `stories/test-luna-story/README.md`
- [ ] Verify placeholders replaced: {story-slug}, {selected-style}, {character-count}, {scene-count}
- [ ] Verify README includes all required sections (Overview, Prerequisites, Step-by-Step, File Reference, Tips, Troubleshooting)

### Test 4: Error Scenarios
- [ ] Invalid slug (e.g., "Story!@#$%") → verify sanitized to "story"
- [ ] Test file write permission error (readonly directory) → verify WARNING + chat fallback
- [ ] Test directory creation permission error → verify CRITICAL + workflow halt

### Test 5: Feature Flag Rollback
- [ ] Set `$env:WRITE_DELIVERABLES_TO_FILES="false"`
- [ ] Run workflow → verify NO files created
- [ ] Verify all deliverables appear in chat
- [ ] Set `$env:WRITE_DELIVERABLES_TO_FILES="true"` → verify files created again

### Test 6: Cross-Platform Paths
- [ ] On Windows: verify paths use backslashes (e.g., `stories\test-luna-story\characters\`)
- [ ] Git commit → verify Git uses forward slashes (OS-agnostic)
- [ ] Verify UTF-8 encoding preserved (test with emoji in story title)

### Test 7: MJ Parameter Completeness
- [ ] Run Prompt Engineer Agent
- [ ] Verify ALL prompts include: `--ar`, `--v 7`, `--oref {url}`, `--ow 200`
- [ ] Verify placeholders present: `{character_name_moodboard_url}`
- [ ] Copy-paste one prompt to verify format is MidJourney-ready

### Test 8: Dual-Output Strategy
- [ ] Complete workflow with file write enabled
- [ ] Verify each deliverable appears in chat AND file
- [ ] Simulate file write failure (readonly directory) → verify deliverable still in chat

### Test 9: Idempotency
- [ ] Run workflow twice for same story
- [ ] Verify second run overwrites files (no errors)
- [ ] Verify directory creation doesn't fail on second run

### Test 10: End-to-End Workflow
- [ ] Use real story (e.g., "Luna y la Estrella Perdida")
- [ ] Execute all phases with human approval
- [ ] Generate character images in MidJourney (Step 1 of README)
- [ ] Upload to Git, get URLs (Step 2 of README)
- [ ] Replace placeholders in prompts.md
- [ ] Generate 1-2 test scenes (Step 3 of README)
- [ ] Verify character consistency with `--oref` works

**Validation Status**: Complete these tests before marking the change as production-ready.
