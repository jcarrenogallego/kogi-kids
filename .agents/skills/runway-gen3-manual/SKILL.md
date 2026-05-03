---
name: runway-gen3-manual
description: Generate animated videos from static images using Runway Gen-3 Alpha manual UI workflow. Covers image upload, motion prompt engineering, camera controls, duration/ratio settings, motion strength tuning, and iterative refinement. Use when user needs to animate images, create videos from renders, add motion to stills, or mentions Runway, Gen-3, image-to-video, video animation.
triggers: runway, gen-3, gen3, image to video, animate image, video from image, runway gen3, gen-3 alpha, motion prompt, video generation, animate render, add motion
---

## Purpose

Generate high-quality animated videos from static images using Runway Gen-3 Alpha through the manual web UI workflow. This skill covers the complete end-to-end process: account setup, credit purchase, image upload strategies, motion prompt engineering patterns, camera control techniques, parameter tuning (duration, ratio, motion strength), quality assessment, and iterative refinement.

**Key capability**: Transform static MidJourney/Stable Diffusion renders into Disney-quality animated shorts without coding.

---

## When to Use This Skill

Trigger this skill when the user:
- Mentions "Runway", "Gen-3", "Gen-3 Alpha", "animate", "video from image"
- Has static renders/images and wants to add motion
- Asks how to create videos from images
- Mentions specific shots needing animation (e.g., "animate the star descent shot")
- Requests guidance on motion prompts or camera controls
- Needs to iterate on video quality (motion too fast/slow, wrong direction, etc.)

**Project context**: Use when working with MidJourney renders for children's stories, product demos, architectural walkthroughs, or any image-based animation workflow.

---

## Prerequisites

### Technical Requirements
- **Browser**: Chrome, Firefox, or Edge (latest versions)
- **Internet**: Stable connection (uploads 2-4MB images + streams video previews)
- **Image specs**: 
  - Format: PNG, JPG, WebP
  - Size: 2-16MB (optimal: 2-4MB)
  - Resolution: 1280×720 (landscape), 720×1280 (portrait), 960×960 (square)
  - Aspect ratio: 0.5 to 2.358 (width ÷ height)

### Account & Credits
- **Runway account**: Create at https://runwayml.com (free signup)
- **Credits**: $5 minimum purchase (500 credits)
  - Gen-3 Alpha Turbo: 5 credits/sec (economical)
  - Gen-4.5: 12 credits/sec (highest quality)
- **Free tier**: 125 credits = 25 sec Gen-3 Turbo or 10 sec Gen-4.5

### Image Preparation
Before Runway:
1. Ensure image is high-quality (sharp, well-lit, clear subject)
2. Check aspect ratio (use Image Magick: `identify image.png`)
3. If needed, crop/resize to supported ratios (1280:720, 720:1280, 960:960)
4. Compress if >4MB (use TinyPNG, ImageOptim, or Squoosh)

---

## Core Concepts

### Models Available (Image-to-Video)

| Model | Cost/Sec | Quality | Duration | Use Case |
|-------|----------|---------|----------|----------|
| **Gen-4.5** | 12 credits ($0.12) | ⭐⭐⭐⭐⭐ Best | 5 or 10 sec | Highest detail, smooth motion |
| **Gen-4 Turbo** | 5 credits ($0.05) | ⭐⭐⭐⭐ Great | 5 or 10 sec | Fast, economical, good quality |
| **Gen-3 Alpha Turbo** | 5 credits ($0.05) | ⭐⭐⭐ Good | 5 or 10 sec | Legacy, stable |
| **Act-Two** | 5 credits ($0.05) | ⭐⭐⭐⭐ | 5 or 10 sec | Character performance (requires reference) |

**Recommendation**: Start with Gen-3 Alpha Turbo (cheap) for testing, upgrade to Gen-4.5 for final renders.

### Motion Strength Scale (0-10)

| Value | Effect | Use Case |
|-------|--------|----------|
| **1-3** | Subtle motion | Breathing, gentle swaying, ambient movement |
| **4-6** | Moderate motion | Walking, floating, natural actions |
| **7-9** | Strong motion | Running, flying, dramatic actions |
| **10** | Extreme motion | Chaotic, fast, unpredictable (risky) |

**Rule of thumb**: Start at 5, adjust ±2 based on result.

### Camera Controls

**Available moves** (specify in motion prompt):
- **Static**: Camera doesn't move (subject moves only)
- **Pan**: Horizontal left/right
- **Tilt**: Vertical up/down
- **Zoom in/out**: Slow dolly effect
- **Crane up/down**: Vertical camera rise/descend
- **Orbit**: Circular around subject
- **Dolly in/out**: Push in or pull back

**Syntax**: "camera static, subject moves" OR "slow zoom in following subject"

### Duration & Ratio Limitations

**Durations**: Only **5 seconds** or **10 seconds** (no custom values like 8, 9, 12)

**Aspect Ratios**:
- **Landscape**: 1280:720 (16:9), 1584:672 (ultra-wide), 1104:832
- **Portrait**: 720:1280 (9:16), 832:1104, 672:1584
- **Square**: 960:960 (1:1)

**If your storyboard needs 8 or 12 seconds**: Generate 10 sec, trim in video editor later.

---

## Step-by-Step Process

### Phase 1: Account Setup & Credit Purchase

#### 1.1 Create Account
1. Go to https://runwayml.com
2. Click **Sign Up** (top-right)
3. Choose: Email + password OR Google/GitHub OAuth
4. Verify email (check inbox/spam)
5. Complete profile (optional: name, use case)

#### 1.2 Purchase Credits
1. After login → click **Profile icon** (top-right) → **Billing**
2. Navigate to **Credits** section
3. Choose package:
   - **$5 = 500 credits** (minimum, good for testing)
   - **$20 = 2000 credits** (better value, ~4% discount)
   - **$50 = 5000 credits** (~10% discount)
4. Enter payment (credit card, PayPal)
5. Confirm purchase → credits appear instantly

**Budget planning**:
- 4 shots × 10 sec × 5 credits (Gen-3 Turbo) = 200 credits = $2
- 4 shots × 10 sec × 12 credits (Gen-4.5) = 480 credits = $4.80

---

### Phase 2: Navigate to Gen-3 Interface

#### 2.1 Access Model
1. From dashboard → left sidebar → **Video** section
2. Click **Gen-3 Alpha Turbo** (or **Gen-4.5** if purchased credits)
3. Interface loads with 3 sections:
   - Left: Input controls (image upload, prompt, settings)
   - Center: Preview canvas
   - Right: Generated videos queue

#### 2.2 Interface Overview
- **Upload Image** button: Click or drag-drop
- **Prompt Text** field: Motion description (max 500 characters)
- **Duration** dropdown: 5 sec / 10 sec
- **Ratio** dropdown: Aspect ratio selector
- **Motion Strength** slider: 0-10 scale
- **Generate** button: Starts task (deducts credits)

---

### Phase 3: Image Upload & Prompt Engineering

#### 3.1 Upload Image
1. Click **+ Image** or **Upload Image** button
2. Browse to file (e.g., `renders/2b-star-descent.png`)
3. Image appears in left panel with thumbnail preview
4. Check aspect ratio indicator (if red = unsupported, need to crop)

**Alternative**: Drag-drop image directly onto canvas

#### 3.2 Write Motion Prompt

**Prompt structure** (5-part template):
```
[Subject] [Action/Motion] [Direction/Path], 
[Speed/Style], 
[Camera Instruction], 
[Visual Effects/Atmosphere], 
[Style Constraint]
```

**Example 1 - Star Descent** (Shot 2B):
```
Golden star descending vertically through dark night sky, 
leaving shimmering golden particle trail behind, 
slow graceful motion, 
camera static following descent, 
Disney 3D animation style, 
magical atmosphere, 
smooth continuous downward movement
```

**Example 2 - Firefly Transformation** (Shot 6D):
```
Magical fireflies appearing progressively one by one in dark forest, 
emerging from darkness with soft golden light trails, 
synchronized gentle pulsing patterns, 
camera slowly orbiting scene, 
Disney animation style, 
enchanted forest atmosphere, 
smooth gradual reveal
```

**Example 3 - Star Ascent** (Shot 7C - Money Shot):
```
Small golden star ascending vertically upward toward sky, 
leaving continuous golden particle trail connecting to girl's raised hands below, 
slow majestic rise, 
sunrise gradient background brightening gradually, 
camera static low angle, 
Disney epic climax moment, 
emotional triumphant atmosphere, 
smooth continuous upward motion
```

**Example 4 - Constellation Reunion** (Shot 7D):
```
Single point of light traveling gracefully to complete geometric constellation pattern, 
stars pulsing in synchronized golden rhythm when complete, 
cosmic space vista, 
camera static satellite perspective, 
minimalist celestial atmosphere, 
smooth light point journey, 
gentle synchronized pulse at end
```

#### 3.3 Motion Prompt Best Practices

**DO** ✅:
- Be specific about direction ("vertically upward", "horizontally left to right")
- Specify speed ("slow", "gradual", "gentle", "rapid")
- Describe the motion path ("descending arc", "straight line", "spiral")
- Include visual effects ("particle trail", "light streaks", "glow pulsing")
- Add style constraint ("Disney style", "smooth animation", "continuous motion")
- Keep it under 300 words (optimal: 150-200 words)

**DON'T** ❌:
- Describe the static image (Runway already sees it)
- Use vague terms ("moves nicely", "looks good")
- Contradict the image (if star is top-right, don't say "star in center")
- Over-complicate with multiple conflicting motions
- Use negative prompts ("do NOT show", "avoid") — ineffective

**Advanced patterns**:
- **Slow motion**: Add "slow motion", "graceful", "gentle", "unhurried"
- **Speed up**: Add "rapid", "fast", "swift", "quick motion"
- **Loopable**: Add "returns to starting position", "cyclic motion"
- **Synchronized**: Add "synchronized", "rhythmic", "pulsing together"

---

### Phase 4: Configure Parameters

#### 4.1 Duration Selection
- Click **Duration** dropdown
- Choose: **5 seconds** or **10 seconds**
- **Tip**: If storyboard needs 8 sec, generate 10 sec and trim later in editor

#### 4.2 Aspect Ratio Selection
- Click **Ratio** dropdown
- Choose based on your composition:
  - **1280:720** (landscape 16:9) — standard horizontal video
  - **720:1280** (portrait 9:16) — Instagram Stories, TikTok
  - **960:960** (square 1:1) — Instagram feed
  - **1584:672** (ultra-wide) — cinematic landscape
- **Tip**: Use same ratio as your input image to avoid auto-cropping

**Check auto-crop behavior**: If input aspect ratio doesn't match selected ratio, Runway crops from center. Verify preview before generating.

#### 4.3 Motion Strength Tuning

**Initial recommendation**: Start at **5** (moderate motion)

**Adjust based on shot type**:
- **Ambient/subtle** (breathing, swaying): **2-3**
- **Natural actions** (walking, floating): **4-6**
- **Dramatic actions** (flying, running): **7-8**
- **Extreme motion** (explosions, chaos): **9-10** (risky, may glitch)

**Iteration strategy**:
1. First attempt: Motion strength **5**
2. If too slow → retry at **7**
3. If too fast → retry at **3**
4. Fine-tune ±1 until satisfied

---

### Phase 5: Generate & Wait

#### 5.1 Start Generation
1. Review all settings (image, prompt, duration, ratio, motion strength)
2. Click **Generate** button (bottom-right)
3. Credits deducted immediately (e.g., 10 sec × 5 credits = 50 credits)
4. Task added to queue (right panel shows status)

#### 5.2 Monitor Progress
- **Status indicators**:
  - ⏳ **Pending**: In queue, waiting for GPU
  - 🔄 **Processing**: Generating (1-3 min)
  - ✅ **Complete**: Video ready
  - ❌ **Failed**: Error (credits refunded)

**Generation time**:
- Gen-3 Alpha Turbo: 1-2 min
- Gen-4.5: 2-3 min
- Gen-4 Turbo: 1-2 min

**Parallel generations**: Can submit multiple tasks simultaneously (queue processes them)

#### 5.3 View Result
1. When status shows ✅ **Complete** → click thumbnail in queue
2. Video plays in center canvas
3. Controls: Play/Pause, Scrub timeline, Loop toggle, Volume

---

### Phase 6: Quality Assessment & Iteration

#### 6.1 Evaluate Result

**Quality checklist**:
- ✅ **Motion direction correct?** (e.g., star descends, not ascends)
- ✅ **Motion speed appropriate?** (not too fast/slow)
- ✅ **Smooth animation?** (no glitches, warping, artifacts)
- ✅ **Trail/effects visible?** (particle trails, light streaks)
- ✅ **Camera behaves correctly?** (static if requested, or moves as prompted)
- ✅ **Style consistent?** (matches Disney 3D aesthetic)
- ✅ **Subject integrity?** (character doesn't morph, details preserved)

#### 6.2 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Motion too slow | Motion strength too low | Increase to 6-8 |
| Motion too fast | Motion strength too high | Decrease to 3-4 |
| Wrong direction | Ambiguous prompt | Be more specific: "vertically downward from top to bottom" |
| Subject warping | Motion strength too high | Lower to 4-5, simplify prompt |
| No visible motion | Motion strength too low OR vague prompt | Increase to 6, add specific action verbs |
| Camera moves when shouldn't | Didn't specify "camera static" | Add "camera static" to prompt |
| Glitchy artifacts | Overcomplicating OR extreme motion | Simplify prompt, lower motion strength |
| Inconsistent with image | Prompt contradicts visual | Rewrite prompt to match what's in image |

#### 6.3 Iteration Strategy

**When to iterate**:
- Motion direction wrong → fix prompt specificity
- Motion speed off → adjust motion strength ±2
- Visual artifacts → lower motion strength, simplify prompt
- Style inconsistency → strengthen style constraint in prompt

**When to accept**:
- Motion direction correct
- Speed is 80%+ right (can adjust in video editor with speed ramping)
- No major glitches (minor artifacts acceptable if shot is <2 sec in final video)
- Captures the emotional beat of the shot

**Budget management**:
- Allow 2 attempts per shot maximum (to stay within budget)
- If 2nd attempt still not perfect, accept "good enough" and fix in post

---

### Phase 7: Download & Archive

#### 7.1 Download Video
1. Click **Download** button (or **⬇** icon) on completed video in queue
2. Video saves as MP4 (H.264 codec, 1280×720 or selected ratio)
3. File naming: `runway_XXXXXX.mp4` (random ID)

#### 7.2 Rename & Organize
```bash
# Recommended naming convention
mv runway_abc123.mp4 animations/2b-star-descent-runway.mp4
mv runway_def456.mp4 animations/6d-firefly-transformation-runway.mp4
mv runway_ghi789.mp4 animations/7c-star-ascent-runway.mp4
mv runway_jkl012.mp4 animations/7d-constellation-reunion-runway.mp4
```

#### 7.3 Archive Settings
Create metadata file for reproducibility:
```json
// animations/metadata.json
{
  "2b-star-descent": {
    "model": "gen3_alpha_turbo",
    "duration": 10,
    "ratio": "1280:720",
    "motion_strength": 5,
    "prompt": "Golden star descending vertically through dark night sky...",
    "credits_used": 50,
    "generation_date": "2026-05-03",
    "iterations": 1,
    "notes": "Perfect on first try, slow graceful descent"
  }
}
```

---

## Best Practices

### Prompt Engineering

1. **Front-load key motion**: Put main action in first 10 words
   - ✅ "Golden star descending vertically..."
   - ❌ "In the dark night sky there is a golden star that begins to descend..."

2. **One primary motion per shot**: Don't ask for 5 simultaneous actions
   - ✅ "Star ascending with trail"
   - ❌ "Star ascending while rotating and pulsing and leaving trail and camera orbits"

3. **Direction specificity**: Use compass/axis terms
   - ✅ "vertically downward from top to bottom"
   - ❌ "moves down"

4. **Speed modifiers**: Always include pacing
   - "slow", "gradual", "gentle" = subtle motion
   - "rapid", "swift", "quick" = fast motion
   - "graceful", "majestic" = moderate with elegance

5. **Style anchors**: Reinforce aesthetic
   - "Disney 3D animation style" = prevents realism
   - "smooth continuous motion" = prevents jitter
   - "magical atmosphere" = adds ethereal quality

### Technical Optimization

1. **Test with Gen-3 Turbo first**: Save credits, validate prompt before expensive Gen-4.5
2. **Use 5 sec for testing**: Half the cost, faster generation
3. **Batch similar shots**: Generate all "ascending" shots together with similar settings
4. **Monitor credit balance**: Check after each generation to avoid surprise depletion
5. **Cache successful prompts**: Save working prompts for future reference

### Workflow Efficiency

1. **Prepare all images beforehand**: Don't upload during generation wait time
2. **Write all prompts in advance**: Copy from storyboard, paste when ready
3. **Use browser tabs**: Open multiple Runway tabs for parallel generations (if credits allow)
4. **Download immediately**: Videos expire after 24 hours if not downloaded

### Quality Control

1. **View at 0.25× speed**: Catch subtle glitches not visible at full speed
2. **Check first/last frames**: Ensure no warping at start/end
3. **Test in context**: Place in video timeline to see if it flows with adjacent shots
4. **Accept "good enough"**: Perfection is expensive; 80% quality often sufficient for 5-sec shot

---

## Common Patterns & Templates

### Pattern 1: Vertical Motion (Ascending/Descending)

**Use case**: Stars rising, objects falling, characters jumping

**Template**:
```
[Subject] [ascending/descending] [vertically/diagonally] [from X to Y],
[speed modifier] motion,
camera static [angle],
[trail/effect] following path,
[style constraint]
```

**Example**:
```
Glowing orb ascending vertically from ground toward sky,
slow majestic motion,
camera static low angle,
golden particle trail following path,
Disney magical style
```

### Pattern 2: Horizontal Motion (Panning)

**Use case**: Characters walking, clouds drifting, vehicles moving

**Template**:
```
[Subject] moving [left/right] across [environment],
[speed modifier] [gait/style],
camera [static/panning with subject],
[background behavior],
[atmosphere constraint]
```

**Example**:
```
Young girl walking right across moonlit garden,
slow steady pace,
camera slowly panning right following her,
fireflies illuminating path,
peaceful nighttime atmosphere
```

### Pattern 3: Emergence/Appearance

**Use case**: Fireflies appearing, stars twinkling on, objects materializing

**Template**:
```
[Elements] appearing [progressively/simultaneously] [in pattern/randomly],
[gradual/sudden] reveal,
camera static,
[light effects] as they emerge,
[synchronized/organic] timing
```

**Example**:
```
Fireflies appearing progressively one by one throughout forest,
gradual gentle reveal,
camera static wide angle,
soft golden glow as they emerge,
synchronized rhythmic timing
```

### Pattern 4: Orbital/Circular Motion

**Use case**: Camera circling subject, objects rotating, dance movements

**Template**:
```
[Subject] [rotating/spinning] [clockwise/counter-clockwise],
OR: camera orbiting [around subject],
[speed modifier] rotation,
[subject behavior] while rotating,
[style constraint]
```

**Example**:
```
Camera slowly orbiting clockwise around ancient tree,
gentle smooth rotation,
owl perched on branch watching,
mystical forest atmosphere,
Disney animated style
```

### Pattern 5: Zoom/Scale Change

**Use case**: Revealing details, cosmic scale transitions, dramatic emphasis

**Template**:
```
[Zoom in/Zoom out] [on subject],
[gradual/rapid] [dolly/zoom],
revealing [what becomes visible],
[emotional tone],
[style constraint]
```

**Example**:
```
Slow zoom out from girl's tearful face,
gradual reveal,
showing hilltop and vast starry sky behind,
emotional triumphant moment,
Disney climax style
```

---

## Troubleshooting

### Error: "Invalid aspect ratio"

**Symptoms**: Upload fails with red error message

**Causes**:
- Image aspect ratio outside 0.5-2.358 range (too wide or too tall)
- Image resolution too low (<640px shortest side)

**Fixes**:
1. Check aspect ratio: `identify -format "%[fx:w/h]" image.png` (ImageMagick)
2. If outside range, crop image:
   ```bash
   # Crop to 16:9
   convert input.png -gravity center -crop 1280:720+0+0 output.png
   ```
3. If too small, upscale (use Topaz Gigapixel or waifu2x)

---

### Error: "Generation failed" (credits refunded)

**Symptoms**: Task shows ❌ status, credits returned

**Causes**:
- Prompt triggered content moderation (violence, NSFW)
- Image contains unsupported elements (text, watermarks)
- Server overload (rare)

**Fixes**:
1. Review prompt for triggering words (remove "blood", "nude", etc.)
2. Check image for watermarks → remove with inpainting tool
3. Wait 5 min, retry (server issues usually resolve)
4. Contact support if persists: support@runwayml.com

---

### Issue: Motion direction opposite of intended

**Symptoms**: Star descends when prompt says "ascending"

**Causes**:
- Ambiguous directional language
- Prompt contradicts visual cues in image

**Fixes**:
1. Use absolute terms: "from top of frame to bottom" instead of "downward"
2. Add explicit path: "starting at upper-right, ending at lower-left"
3. Reference cardinal directions: "northward", "southward"
4. If image shows subject mid-motion, clarify: "continuing descent" vs "beginning descent"

---

### Issue: Subject warps/morphs during motion

**Symptoms**: Character's face distorts, star shape changes, objects melt

**Causes**:
- Motion strength too high (>8)
- Prompt too complex (asking for 3+ simultaneous motions)
- Image has fine details that AI struggles to preserve

**Fixes**:
1. Lower motion strength to 4-5
2. Simplify prompt: one primary motion only
3. Add "preserving character details" to prompt
4. If character-focused, consider Act-Two model (better at preserving identity)

---

### Issue: No visible motion / output looks static

**Symptoms**: Generated video looks like still image

**Causes**:
- Motion strength set to 0-2 (too subtle)
- Prompt too vague (no specific action verbs)
- Subject already in motion in image (AI unsure what to do)

**Fixes**:
1. Increase motion strength to 6-7
2. Rewrite prompt with specific verbs: "floating", "drifting", "swaying"
3. Add environmental motion cues: "leaves rustling", "clouds drifting", "water rippling"
4. If subject is mid-action, add "continuing to [action]"

---

### Issue: Camera moves when it shouldn't

**Symptoms**: Unwanted zoom, pan, or rotation

**Causes**:
- Didn't explicitly specify "camera static"
- Prompt implies camera motion ("following", "tracking")

**Fixes**:
1. Add "camera static" to beginning of prompt
2. Replace "following" with "while subject moves"
3. Anchor camera: "camera locked, fixed perspective"

---

### Issue: Video quality looks compressed/pixelated

**Symptoms**: Blocky artifacts, loss of detail

**Causes**:
- Not an issue with Runway (outputs are high-quality H.264)
- Likely browser preview compression OR download issue

**Fixes**:
1. Ignore preview quality → download video file
2. Check downloaded file in VLC or video editor
3. If still pixelated, increase input image resolution (use 1920×1080 source)
4. Try Gen-4.5 instead of Gen-3 Turbo (higher fidelity)

---

## Examples: Complete Workflows

### Example 1: Animating "Star Descent" Shot (2B)

**Context**: Static render of night garden with golden star in upper-right, need star to descend

**Step-by-step**:

1. **Upload**: `renders/2b-star-descent.png` (1280×720, 3.2MB)
2. **Model**: Gen-3 Alpha Turbo (testing)
3. **Prompt**:
   ```
   Golden star descending vertically through dark night sky,
   leaving shimmering golden particle trail behind,
   slow graceful motion,
   camera static,
   Disney 3D animation style,
   magical atmosphere,
   smooth continuous downward movement
   ```
4. **Duration**: 10 sec (need 8, will trim)
5. **Ratio**: 1280:720
6. **Motion Strength**: 5
7. **Generate** → wait 1 min 30 sec
8. **Result**: ✅ Perfect! Star descends smoothly, trail visible, no glitches
9. **Download** → rename to `animations/2b-star-descent-runway.mp4`
10. **Credits used**: 50 (10 sec × 5 credits)

**Total time**: 5 min (including upload + prompt writing)

---

### Example 2: Iterating "Firefly Transformation" (6D)

**Context**: Dark forest with Luna, fireflies need to appear progressively

**Attempt 1**:
- **Prompt**: "Fireflies appearing in dark forest"
- **Motion Strength**: 5
- **Result**: ❌ Fireflies appear all at once, not progressively
- **Issue**: Prompt too vague

**Attempt 2** (fix):
- **Prompt**: 
  ```
  Magical fireflies appearing progressively one by one in dark forest,
  emerging from darkness with soft golden light trails,
  synchronized gentle pulsing patterns,
  camera slowly orbiting scene,
  Disney animation style,
  enchanted forest atmosphere,
  smooth gradual reveal
  ```
- **Motion Strength**: 6 (increased for more visible appearance)
- **Result**: ✅ Much better! Fireflies appear sequentially, light trails visible
- **Download** → rename to `animations/6d-firefly-transformation-runway.mp4`

**Total time**: 12 min (2 attempts × 6 min each)
**Credits used**: 100 (2 × 10 sec × 5 credits)

---

### Example 3: Money Shot "Star Ascent" (7C)

**Context**: Luna on hilltop raising basket, star needs to ascend majestically

**Approach**: Use Gen-4.5 (highest quality) since this is climax shot

**Workflow**:
1. **Upload**: `renders/7c-star-ascent.png` (1280×720, 4.1MB)
2. **Model**: Gen-4.5 (premium quality)
3. **Prompt**:
   ```
   Small golden star ascending vertically upward toward sky,
   leaving continuous golden particle trail connecting to girl's raised hands below,
   slow majestic rise,
   sunrise gradient background brightening gradually,
   camera static low angle,
   Disney epic climax moment,
   emotional triumphant atmosphere,
   smooth continuous upward motion
   ```
4. **Duration**: 10 sec (need 12, will loop or extend in editor)
5. **Ratio**: 1280:720
6. **Motion Strength**: 5 (want graceful, not rushed)
7. **Generate** → wait 2 min 45 sec (Gen-4.5 slower)
8. **Result**: ✅ PERFECT! Star ascends beautifully, trail connects to hands, sunrise brightens
9. **Download** → rename to `animations/7c-star-ascent-runway-MASTER.mp4`
10. **Credits used**: 120 (10 sec × 12 credits)

**Total time**: 8 min
**Worth it**: YES - money shot looks cinematic

---

## Integration with Video Editors

After downloading animated shots, import to editor:

### Adobe Premiere Pro
1. Import: File → Import → select `animations/*.mp4`
2. Drag to timeline at correct timing (per storyboard)
3. Trim excess: If generated 10 sec but need 8, use Razor tool
4. Speed ramping: Right-click → Speed/Duration → adjust if motion too fast/slow
5. Transitions: Apply from storyboard (dissolve, fade, etc.)

### DaVinci Resolve
1. Media Pool → Import → `animations/` folder
2. Drag to timeline per storyboard timing
3. Inspector → Retime Controls → adjust speed if needed
4. Fusion tab → add VFX if needed (particle enhancements)

### Final Cut Pro
1. Import → `animations/` folder
2. Append to timeline (⌘E)
3. Blade tool (B) → trim to exact duration
4. Retime menu → adjust speed curves

---

## Advanced Techniques

### Technique 1: Layering Static + Animated

**Use case**: Want character static but environment animated (e.g., Luna still, fireflies moving)

**Approach**:
1. Generate version with motion strength 3 → subtle environmental motion
2. In editor, mask out character from original static image
3. Composite static character over animated background

### Technique 2: Looping Animations

**Use case**: Want 30 sec of stars twinkling but only have 10 sec video

**Approach**:
1. In prompt, add "returns to starting position" or "cyclic motion"
2. Generate 10 sec with seamless loop intent
3. In editor, duplicate clip 3× → trim/crossfade to hide seams

### Technique 3: Speed Ramping for Drama

**Use case**: Star ascent should start slow, accelerate near climax

**Approach**:
1. Generate at moderate motion strength (5)
2. In editor, apply speed curve:
   - Sec 0-4: 50% speed (slow rise)
   - Sec 4-8: 100% speed (normal)
   - Sec 8-10: 150% speed (dramatic acceleration)

### Technique 4: Combining Multiple Runways

**Use case**: Want star descending AND fireflies appearing (2 simultaneous motions)

**Approach**:
1. Generate shot focusing on star descent (motion strength 6)
2. Generate shot focusing on fireflies appearing (motion strength 7)
3. In editor, composite with blend mode (Screen or Add)
4. Mask areas to control which motion dominates where

---

## Cost Optimization Strategies

1. **Test with Gen-3 Turbo**: 5 credits/sec vs 12 credits/sec (Gen-4.5) = 58% savings
2. **Generate 5 sec for tests**: Half cost, validate prompt before committing to 10 sec
3. **Batch similar shots**: Generate all "ascending" motions in one session (mental consistency)
4. **Accept first good result**: Don't over-iterate (diminishing returns after 2 attempts)
5. **Speed up in post**: If motion slightly slow, speed ramp in editor instead of regenerating

**Example budget** (4 shots):
- **Economical**: 4 × 5 sec × 5 credits = 100 credits = $1.00 (Gen-3 Turbo, 5 sec tests)
- **Balanced**: 4 × 10 sec × 5 credits = 200 credits = $2.00 (Gen-3 Turbo, full length)
- **Premium**: 4 × 10 sec × 12 credits = 480 credits = $4.80 (Gen-4.5, highest quality)

---

## Version History & Model Evolution

| Version | Release | Key Features | Status |
|---------|---------|--------------|--------|
| Gen-1 | 2022 | Text-to-video pioneer | Deprecated |
| Gen-2 | 2023 | Image-to-video, 4 sec | Deprecated |
| Gen-3 Alpha | 2024 | 10 sec, motion control | Active |
| Gen-3 Turbo | 2024 | Faster, economical | Active (recommended) |
| Gen-4 Turbo | 2025 | Better quality | Active |
| Gen-4.5 | 2026 | Highest fidelity | Active (premium) |
| Act-Two | 2025 | Character performance | Active (specialty) |

**Future models** (roadmap):
- Gen-5 (estimated 2026 Q4): 20 sec durations, 4K resolution
- Gen-5 Turbo (estimated 2027 Q1): Economical 20 sec

---

## Reference Resources

### Official Docs
- **Runway Docs**: https://docs.dev.runwayml.com/
- **Pricing**: https://docs.dev.runwayml.com/guides/pricing/
- **Models**: https://docs.dev.runwayml.com/guides/models/
- **Community Forum**: https://community.runwayml.com/

### Tutorials
- **Runway YouTube**: https://www.youtube.com/@runwayml (official tutorials)
- **Motion Prompt Guide**: https://runwayml.com/blog/motion-prompts-guide
- **Best Practices**: https://runwayml.com/blog/gen3-best-practices

### Tools
- **Runway Playground**: https://dev.runwayml.com/playground (test API)
- **Skills Repository**: https://github.com/runwayml/skills (agent skills)
- **Figma Plugin**: https://github.com/runwayml/figma-plugin (export to Runway)

---

## Project-Specific Notes (Luna y la Estrella Perdida)

### Shots to Animate
1. **Shot 2B** - Star Descent (8 sec) → Gen 10 sec, trim to 8
2. **Shot 6D** - Firefly Transformation (9 sec) → Gen 10 sec, trim to 9
3. **Shot 7C** - Star Ascent (12 sec) → Gen 10 sec, consider looping or speed ramping
4. **Shot 7D** - Constellation Reunion (5 sec) → Gen 5 sec exact

### Budget
- **Total**: 35 sec needed
- **Gen-3 Turbo**: 35 sec × 5 credits = 175 credits = $1.75
- **Gen-4.5**: 35 sec × 12 credits = 420 credits = $4.20
- **Hybrid** (3 Turbo + 1 Gen-4.5 for Shot 7C): 145 credits = $1.45

### Recommended Order
1. **Start with Shot 7C** (Money Shot) using Gen-4.5 → highest stakes, validate workflow
2. If successful → proceed with Shots 2B, 6D using Gen-3 Turbo (economical)
3. Shot 7D last (simplest, 5 sec cosmic shot)

---

**END OF SKILL**
