# Exploration: Runway API for Video Animation

**Project**: Luna y la Estrella Perdida  
**Date**: 2026-05-03  
**Context**: Evaluating Runway API vs UI for animating 4 priority shots from storyboard  

---

## Current State

### What We Have
- **26 static renders** (MidJourney V7) in `renders/` folder
- **Storyboard complete** with timing, narrative, and transitions
- **4 priority shots identified** for animation:
  1. Shot 2B - Star Descent (8 sec)
  2. Shot 6D - Firefly Transformation (9 sec)
  3. Shot 7C - Star Ascent (12 sec) 💫 MONEY SHOT
  4. Shot 7D - Constellation Reunion (5 sec)

### Current Workflow (Manual UI)
User would:
1. Go to runwayml.com → Gen-3 Alpha Turbo
2. Upload image for each shot (4 times)
3. Write motion prompt for each (4 times)
4. Configure duration + motion strength (4 times)
5. Generate → wait → download (4 times)
6. Iterate if results not satisfactory (repeat all above)

**Estimated time**: 30-45 min manual work + 10-15 min generation time

---

## Runway API Capabilities

### Available Models (Image-to-Video)

| Model | Cost per Second | Quality | Use Case |
|-------|-----------------|---------|----------|
| gen4.5 | 12 credits ($0.12) | Highest | Best motion, detail |
| gen4_turbo | 5 credits ($0.05) | Good | Fast, economical |
| gen3a_turbo | 5 credits ($0.05) | Good | Fast alternative |
| veo3 | 40 credits ($0.40) | Premium | High-end production |
| veo3.1 | 20-40 credits | Premium + audio | High-end + sound |

**Recommendation for our project**: `gen4.5` or `gen4_turbo`

### SDK Support

✅ **Node.js SDK**: `@runwayml/sdk` (TypeScript included)  
✅ **Python SDK**: `runwayml` (MyPy type annotations)  
✅ **Built-in polling**: `.waitForTaskOutput()` method handles async waiting  
✅ **Error handling**: `TaskFailedError`, `TaskTimedOutError` classes  

### Input Formats

| Method | Max Size | Use Case |
|--------|----------|----------|
| **URL** | 16MB | Images hosted online |
| **Data URI** (base64) | 5MB | Local files, avoid upload step |
| **Ephemeral upload** | 200MB | Large files, valid 24hrs |

**Our images**: ~2-4MB each → **Data URI** or **Ephemeral upload** work

### Output Configuration

**Durations available**: 5 seconds, 10 seconds  
**Ratios supported**: 1280:720 (landscape 16:9), 720:1280 (portrait), 960:960 (square)  

**Our needs**:
- Shot 2B (8 seg) → **10 sec** (trim in editor)
- Shot 6D (9 seg) → **10 sec** (trim in editor)
- Shot 7C (12 seg) → **10 sec** (trim in editor)
- Shot 7D (5 seg) → **5 sec** ✅ exact match

**Note**: API doesn't support exact 8/9/12 sec durations — all rounded to 5 or 10

---

## Affected Files (if implementing API automation)

### Would Create
- `scripts/animate-shots.py` — Python script to automate 4 shot generations
- `scripts/runway-config.json` — Configuration with prompts, files, settings
- `scripts/requirements.txt` — Python dependencies (runwayml SDK)
- `animations/` — Output folder for generated videos

### Would Read
- `renders/2b-star-descent.png`
- `renders/6d-firefly-transformation.png`
- `renders/7c-star-ascent.png`
- `renders/7d-constellation-reunion.png`
- `storyboard-timing.md` — Extract motion prompts from "Runway prompt" sections

---

## Approaches

### Approach A: Manual UI Workflow (Current Plan)

**Description**: Use Runway web interface manually for each of the 4 shots

**Pros**:
- ✅ No coding required
- ✅ Visual feedback immediate
- ✅ Interactive controls (motion strength slider, real-time adjustments)
- ✅ Preview before committing credits
- ✅ Easier to learn for first-time users
- ✅ Can use exact durations or close approximations

**Cons**:
- ❌ Tedious: 4 separate generations, each with upload + config + wait
- ❌ Not reproducible: Hard to replicate exact settings if need to regenerate
- ❌ Error-prone: Manual copy-paste of prompts from storyboard
- ❌ No version control: Settings not saved anywhere
- ❌ Time-consuming for iterations: If Shot 2B needs adjustment, repeat entire flow

**Effort**: Low (no coding)  
**Time**: 30-45 min manual work + 10-15 min generation  
**Best for**: One-off generation, learning process, visual experimentation

---

### Approach B: Automated API Script (Python)

**Description**: Write Python script using `runwayml` SDK to generate all 4 shots programmatically

**Implementation**:
```python
from runwayml import RunwayML
import os
import base64

client = RunwayML(api_key=os.environ["RUNWAY_API_KEY"])

shots = [
    {
        "name": "2b-star-descent",
        "file": "renders/2b-star-descent.png",
        "prompt": "Golden star descending vertically through dark night sky...",
        "duration": 10,
        "motion_strength": 5,
    },
    # ... 3 more shots
]

for shot in shots:
    # Load image
    with open(shot["file"], "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
        data_uri = f"data:image/png;base64,{image_data}"
    
    # Create task
    task = client.image_to_video.create(
        model="gen4.5",
        promptImage=data_uri,
        promptText=shot["prompt"],
        ratio="1280:720",
        duration=shot["duration"],
    ).waitForTaskOutput()
    
    # Download result
    video_url = task.output[0]
    # ... download and save to animations/{name}.mp4
```

**Pros**:
- ✅ Reproducible: Same script generates same results
- ✅ Versionable: Prompts + settings in code (Git)
- ✅ Batch processing: Run once, generates all 4 shots unattended
- ✅ Easy iteration: Change prompt → re-run script
- ✅ Scalable: Add more shots without manual work increase
- ✅ Error handling: Retry logic, task status monitoring built-in

**Cons**:
- ❌ Requires coding: Python knowledge needed
- ❌ Setup overhead: Install SDK, get API key, write script (~1 hour)
- ❌ No visual preview: Can't see result until generation completes
- ❌ Fixed durations: API only supports 5/10 sec (not 8/9/12 exact)
- ❌ Debugging harder: If generation fails, less clear why

**Effort**: Medium (1-2 hours to write + test script)  
**Time after setup**: 5 min to run script + 10-15 min generation (unattended)  
**Best for**: Multiple iterations expected, reusable workflow, future projects

---

### Approach C: Hybrid - Manual First, API for Iterations

**Description**: Use UI for first generation to validate prompts/settings, then API for iterations if needed

**Workflow**:
1. Generate Shot 7C (Money Shot) via UI manually → validate motion quality
2. If satisfied with Runway's interpretation, proceed with UI for remaining 3
3. If need to iterate (e.g., motion too fast/slow), write script for batch re-generation
4. Script reuses validated settings from UI experiments

**Pros**:
- ✅ Best of both worlds: Visual validation + automation for iterations
- ✅ Risk mitigation: Don't commit to script until proven UI works
- ✅ Learning path: Understand Runway's behavior before automating
- ✅ Efficient iterations: Manual once, automated many times

**Cons**:
- ❌ Still requires coding (though deferred)
- ❌ Duplicated effort: First shot done twice (UI + script)

**Effort**: Low initially, Medium if script becomes necessary  
**Time**: 10 min first shot + 5 min script (if needed) + generation time  
**Best for**: Uncertain quality expectations, want to de-risk before automating

---

## Recommendation

**For THIS project (Luna y la Estrella Perdida, 4 shots):** 

### ✅ **APPROACH A - Manual UI Workflow**

**Reasoning**:

1. **First-time with Runway**: User hasn't used Runway before — learning UI is valuable
2. **Small batch**: Only 4 shots — automation overhead (1-2 hours) not justified
3. **Unpredictable results**: Don't know yet if prompts will work — visual feedback critical
4. **Experimentation needed**: Motion strength, camera controls need trial-and-error
5. **Duration mismatch**: API's 5/10 sec limitation not ideal for 8/9/12 sec shots
6. **One-off project**: Not building reusable pipeline (yet)

**When to reconsider API (future)**:

- ✅ If user needs to regenerate all 4 shots due to style inconsistency
- ✅ If planning to animate 10+ more children's stories (amortize script effort)
- ✅ If building a product/service that generates videos regularly
- ✅ If collaborating with team (API makes settings shareable)

---

## Cost Analysis

### Manual UI (4 shots, gen4.5 model)

```
Shot 2B: 10 sec × 12 credits = 120 credits = $1.20
Shot 6D: 10 sec × 12 credits = 120 credits = $1.20
Shot 7C: 10 sec × 12 credits = 120 credits = $1.20
Shot 7D:  5 sec × 12 credits =  60 credits = $0.60
─────────────────────────────────────────────
TOTAL:   35 sec             = 420 credits = $4.20
```

**If iterations needed** (e.g., 2 attempts per shot):
```
35 sec × 2 attempts × 12 credits = 840 credits = $8.40
```

### API Automation (same 4 shots)

**Initial generation**: $4.20 (same as UI)  
**Re-generation** (all 4 shots if prompts tweaked): $4.20 per run  

**Break-even**: If need to regenerate all 4 shots **2+ times**, API becomes worth it

**With gen4_turbo** (cheaper, faster model):
```
35 sec × 5 credits = 175 credits = $1.75 per full run
```

---

## Risks

### Manual UI Risks
- ❌ **Consistency**: Hard to maintain exact same settings across 4 shots
- ❌ **Lost settings**: If browser crashes, settings not saved
- ❌ **Prompt errors**: Copy-paste mistakes from storyboard
- ❌ **Fatigue**: Manual process prone to human error in repetition

**Mitigation**: Keep storyboard open, copy prompts carefully, save settings screenshots

### API Risks
- ❌ **Setup time**: 1-2 hours to write + debug script (50% of project time)
- ❌ **API changes**: Runway API evolving, script may break in future
- ❌ **Rate limits**: Unknown rate limits may cause throttling
- ❌ **Debugging difficulty**: Error messages less clear than UI
- ❌ **Over-engineering**: Script complexity not justified for 4 shots

**Mitigation**: Only use API if planning multiple projects or iterations

---

## Skills Creation Recommendation

### Should we create Runway Skills?

**YES, but with caveats**:

1. **Create skill for manual UI workflow** (priority HIGH)
   - `runway-gen3-manual.md` skill
   - Covers: image upload, prompt engineering, motion controls, duration/ratio settings
   - Useful immediately for current project
   - Teaches best practices for Runway UI

2. **Create skill for API automation** (priority MEDIUM)
   - `runway-api-automation.md` skill
   - Covers: SDK setup, image-to-video endpoint, polling, error handling
   - Useful for future projects with 10+ shots
   - Reference for when automation becomes worth it

3. **Defer Character API skills** (priority LOW)
   - Characters API (gwm1_avatars, act_two) not relevant for static animation
   - Only create if planning lip-sync or character performance projects

**Skills to create**:

```
.agents/skills/runway-gen3-manual/
  ├── SKILL.md          # Manual UI workflow, prompt engineering
  └── prompts-guide.md  # Motion prompt patterns, examples

.agents/skills/runway-api-automation/
  ├── SKILL.md          # Python SDK, automation script patterns
  └── examples/
      └── batch-animate.py  # Reference implementation
```

---

## Ready for Next Step

**YES — Proceed with Manual UI Tutorial**

**What the user should do NOW**:

1. **Create Runway account** at https://runwayml.com (if not exists)
2. **Purchase initial credits** (500 credits = $5 minimum, enough for 1-2 full runs)
3. **Follow UI tutorial** to animate Shot 7C (Money Shot) first
   - Validates prompt quality
   - Learns motion controls
   - Sees Runway's interpretation before committing all 4 shots
4. **If satisfied**, proceed with remaining 3 shots via UI
5. **If multiple iterations needed**, reconsider API script

**Next document to create**: `runway-ui-tutorial.md` with step-by-step screenshots

---

## Alternative: Hybrid Approach with Runway Skills Repository

**Discovery**: Runway maintains official skills repository at https://github.com/runwayml/skills

This repo includes:
- Claude Code Skills for AI agents
- Pre-built prompt patterns
- Integration examples

**Recommendation**: 
1. Clone Runway's skills repo
2. Review their Claude skills for Runway API
3. Adapt to our `.agents/skills/` structure if planning API automation

**Action**: Defer this until API automation is confirmed necessary (not for this 4-shot project)

---

**END OF EXPLORATION**
