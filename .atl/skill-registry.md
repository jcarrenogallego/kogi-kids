# Skill Registry — kogi-kids

**Generated**: 2026-05-01  
**Updated**: 2026-05-01  
**Project**: kogi-kids  
**Purpose**: Catalog of available skills for sub-agent injection  
**Total Skills**: 27 user-level + 4 project-level workflows + 7 domain-specific + 1 orchestrator  

---

## User Skills

| Trigger | Skill Name | Path |
|---------|-----------|------|
| LangChain agent, create_agent, tools, middleware | langchain-fundamentals | c:\Users\Alejandra\.agents\skills\langchain-fundamentals\SKILL.md |
| LangGraph, StateGraph, nodes, edges, Command, Send | langgraph-fundamentals | c:\Users\Alejandra\.agents\skills\langgraph-fundamentals\SKILL.md |
| Checkpointer, thread_id, persistence, Store, subgraph | langgraph-persistence | c:\Users\Alejandra\.agents\skills\langgraph-persistence\SKILL.md |
| Clean Architecture, layers, Dependency Rule, hexagonal | clean-architecture | c:\Users\Alejandra\.agents\skills\clean-architecture\SKILL.md |
| Domain-Driven Design, bounded context, aggregate, ubiquitous language | domain-driven-design | c:\Users\Alejandra\.agents\skills\domain-driven-design\SKILL.md |
| Architecture patterns, Clean Architecture, Hexagonal, DDD | architecture-patterns | c:\Users\Alejandra\.agents\skills\architecture-patterns\SKILL.md |
| FastAPI, Pydantic models, async, endpoints | fastapi | c:\Users\Alejandra\.agents\skills\fastapi\SKILL.md |
| FastAPI templates, async patterns, dependency injection | fastapi-templates | c:\Users\Alejandra\.agents\skills\fastapi-templates\SKILL.md |
| Pytest, fixtures, mocking, TDD, parametrization | python-testing-patterns | c:\Users\Alejandra\.agents\skills\python-testing-patterns\SKILL.md |
| Pytest coverage, increase coverage, missing lines | pytest-coverage | c:\Users\Alejandra\.agents\skills\pytest-coverage\SKILL.md |
| Python performance, profiling, cProfile, optimization | python-performance-optimization | c:\Users\Alejandra\.agents\skills\python-performance-optimization\SKILL.md |
| Docker Compose, multi-container, networking, volumes | docker-compose-orchestration | c:\Users\Alejandra\.agents\skills\docker-compose-orchestration\SKILL.md |
| Dockerfile, multi-stage, optimization, layers | multi-stage-dockerfile | c:\Users\Alejandra\.agents\skills\multi-stage-dockerfile\SKILL.md |
| Git commit, conventional commits, commit message | git-commit | c:\Users\Alejandra\.agents\skills\git-commit\SKILL.md |
| Find skills, discover skills, install skills, npx skills | find-skills | c:\Users\Alejandra\.agents\skills\find-skills\SKILL.md |
| Create skill, document patterns, skill structure | skill-creator | c:\Users\Alejandra\.copilot\skills\skill-creator\SKILL.md |
| Judgment day, adversarial review, dual review, juzgar | judgment-day | c:\Users\Alejandra\.copilot\skills\judgment-day\SKILL.md |
| PR creation, pull request, branch, GitHub | branch-pr | c:\Users\Alejandra\.copilot\skills\branch-pr\SKILL.md |
| GitHub issue, bug report, feature request | issue-creation | c:\Users\Alejandra\.copilot\skills\issue-creation\SKILL.md |
| Character design, character sheet, consistency, turnaround, reference sheet | character-design-sheet | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\character-design-sheet\SKILL.md |
| Children's books, kids content, rhyming books, picture books, ages 2-9 | kids-book-writer | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\kids-book-writer\SKILL.md |
| MidJourney, image generation, MJ prompts, style codes, sref, oref | midjourney-prompt-engineering | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\midjourney-prompt-engineering\SKILL.md |
| Screenplay, Fountain format, mockumentary, talking heads, dialogue | mockumentary-screenplay | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\mockumentary-screenplay\SKILL.md |
| Prompt engineering, few-shot, chain-of-thought, structured outputs | prompt-engineering-patterns | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\prompt-engineering-patterns\SKILL.md |
| Storytelling, narrative, story arc, customer stories, SCAR | storytelling | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\storytelling\SKILL.md |
| Workflow orchestration, Temporal, saga patterns, distributed systems | workflow-orchestration-patterns | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\workflow-orchestration-patterns\SKILL.md |
| Video generation, genera video, MidJourney prompts, story to video, orchestrate agents | video-generator-orchestrator | c:\Users\Alejandra\Documents\JoseCarreno\projects\kogi-kids\.agents\skills\video-generator-orchestrator\SKILL.md |

---

## Compact Rules

### langchain-fundamentals
- ALWAYS use `create_agent()` — all other agent creation methods are deprecated
- Tools: `@tool` decorator (Python) or `tool()` function (TypeScript) with schema
- Middleware: pass `middleware=[...]` for human-in-the-loop, retry logic, or custom flows
- Persistence: add `checkpointer=MemorySaver()` + thread_id in config for stateful conversations
- Model parameter: `"anthropic:claude-sonnet-4-5"` or model instance
- DO NOT use deprecated classes like `AgentExecutor`, `initialize_agent`, or `create_react_agent`

### langgraph-fundamentals
- StateGraph: compile() before invoke() — always required
- State reducers: use `Annotated[list, operator.add]` for lists, default overwrites
- Nodes return partial updates (dict), never mutate and return full state
- Edges: `add_edge(START, "node")` for static, `add_conditional_edges` for routing
- Command object: `return Command(goto="next_node", update={"key": "val"})` for dynamic routing
- Send object: `return [Send("node", {"input": i}) for i in items]` for fan-out parallelism
- Design: map workflow steps → nodes, design state schema, build nodes, wire edges, compile

### langgraph-persistence
- Checkpointer at compile: `compile(checkpointer=...)` NOT in nodes
- thread_id ALWAYS required: `config={"configurable": {"thread_id": "unique-id"}}`
- Production: use PostgresSaver, NEVER MemorySaver in prod
- Store for cross-thread memory: `store.put(...)` for user preferences, `store.search(...)` to retrieve
- Subgraphs: use `subgraphs_config` for scoped vs parent checkpointers
- Time travel: `get_state(...).next` + `update_state(..., as_node="nodeName")` for replay

### clean-architecture
- Dependency Rule: dependencies ALWAYS point inward (frameworks → adapters → use cases → entities)
- Inner circles define interfaces, outer circles implement them
- Repository pattern: abstract all persistence, business logic never imports ORM
- DTOs cross boundaries, NEVER domain entities or ORM models
- Framework isolation: wrap framework calls behind interfaces
- Test boundaries: use case tests should NOT require a database or HTTP server

### domain-driven-design
- Ubiquitous Language: every class/method/event uses domain expert terminology
- Bounded Contexts: different contexts can use same word with different meanings — that's OK
- Aggregates: enforce invariants within aggregate boundary, use aggregate root for external access
- Value Objects: immutable, equality by value, no identity (e.g., Money, Address)
- Domain Events: past-tense names (OrderPlaced, PaymentProcessed), capture business facts
- Anti-Corruption Layer: translate between contexts to prevent model pollution

### architecture-patterns
- Layers: Entities (core), Use Cases (app logic), Adapters (I/O translation), Frameworks (tools)
- Hexagonal: ports (interfaces) defined inward, adapters (implementations) outward
- DDD tactical: aggregates for consistency boundaries, repositories for persistence abstraction
- Dependency Inversion: high-level policies define interfaces, low-level details implement them
- Screaming Architecture: folder structure should scream the domain (shipping/, billing/), not the framework

### fastapi
- Use `fastapi dev` for development with auto-reload, `fastapi run` for production
- Pydantic v2 models for request/response validation
- Async endpoints: `async def` when calling I/O (DB, HTTP, file), sync `def` for CPU-bound
- Dependency injection: `Depends(...)` for shared logic, session management, auth
- Router: `APIRouter(prefix="/api/v1")` for modular structure
- Exception handlers: `@app.exception_handler(CustomException)` for consistent error responses

### fastapi-templates
- Project structure: `app/api/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`
- Async patterns: use `httpx.AsyncClient` for external APIs, `asyncio.gather` for parallelism
- Middleware: CORS, authentication, logging middleware in `app/core/middleware.py`
- Config: use Pydantic Settings for environment variables with `.env` support
- Error handling: centralized exception handlers returning JSON with status codes

### python-testing-patterns
- Pytest fixtures: use `@pytest.fixture` for setup/teardown, `scope="session"` for expensive resources
- Mocking: `mocker.patch` (pytest-mock) for external dependencies, NEVER mock internal logic
- Parametrize: `@pytest.mark.parametrize` for testing multiple inputs, not loops in tests
- Async tests: `@pytest.mark.asyncio` + `async def test_...` for async code
- Test structure: Arrange-Act-Assert (AAA) pattern, one assertion per test
- Isolation: each test should run independently, no shared state between tests

### pytest-coverage
- Run: `pytest --cov=src --cov-report=term-missing` to see uncovered lines
- Target: aim for 90%+ coverage on business logic, 100% on critical paths
- Exclude: use `# pragma: no cover` for unreachable code (e.g., if TYPE_CHECKING)
- Branch coverage: `--cov-branch` to catch missing conditional branches
- Report formats: `html`, `xml`, `json` for CI integration

### python-performance-optimization
- Profiling: `cProfile` for function-level, `line_profiler` for line-level bottlenecks
- Memory: `memory_profiler` for leak detection, `tracemalloc` for allocation tracking
- Optimization: profile FIRST, optimize AFTER, never premature optimization
- Patterns: use generators for large datasets, avoid global lookups, cache expensive calls
- Tools: `py-spy` for production profiling without code changes

### docker-compose-orchestration
- Networks: create named networks for service isolation, use `depends_on` for startup order
- Volumes: named volumes for data persistence, bind mounts for development
- Health checks: `healthcheck` directive for service readiness before dependents start
- Environment: `.env` file for secrets, `env_file` directive in compose
- Multi-stage: combine with multi-stage Dockerfiles for optimized production images

### multi-stage-dockerfile
- Builder stage: install dependencies, compile code, generate artifacts
- Runtime stage: copy only artifacts from builder, minimal base image (alpine, distroless)
- Layer caching: copy dependency files BEFORE source code to leverage cache
- Security: run as non-root user, minimal packages, scan with trivy
- Size optimization: combine RUN commands with `&&`, clean up in same layer

### git-commit
- Format: `<type>(<scope>): <description>` (Conventional Commits)
- Types: feat, fix, docs, style, refactor, test, chore, perf, ci
- Scope: module or component affected (optional but recommended)
- Description: imperative mood, no period, max 72 chars
- Body: explain WHY, not WHAT (optional)
- Breaking changes: `BREAKING CHANGE:` in footer or `!` after type/scope

### find-skills
- Command: `npx skills find [query]` for interactive search
- Install: `npx skills add <package>` from GitHub or other sources
- Update: `npx skills update` to sync all installed skills
- Domains: design, testing, deployment, frameworks, languages, workflows
- When to use: user asks "how do I do X" or "find a skill for X"

### skill-creator
- Structure: `skills/{name}/SKILL.md` with frontmatter (name, description, trigger)
- Compact rules: 5-15 lines max, actionable only (do/don't), no motivation
- Trigger: clear phrase for when AI should load this skill
- Assets: templates, schemas in `assets/`, references in `references/`
- Naming: `{tech}` for generic, `{project}-{component}` for project-specific

### judgment-day
- Parallel blind review: launch TWO sub-agents simultaneously, neither knows about the other
- Skill injection: ALWAYS inject project standards from skill registry into BOTH judges + fix agent
- Verdict synthesis: orchestrator compares findings (Confirmed, Suspect A/B, Contradiction)
- Warning classification: real (fix required) vs theoretical (report only, no fix, no re-judge)
- Convergence: max 2 fix iterations, then ASK user to continue or escalate
- Approved criteria: 0 confirmed CRITICALs + 0 confirmed real WARNINGs after Round 1

### branch-pr
- Issue-first: ALWAYS verify issue exists before creating PR, enforce issue reference
- Branch naming: `{type}/{issue-number}-{description}` (e.g., `feat/123-add-auth`)
- PR template: use `.github/pull_request_template.md` if exists
- Draft PR: use `--draft` flag for work-in-progress PRs
- Review: assign reviewers, add labels, link to issue

### issue-creation
- Template: use `.github/ISSUE_TEMPLATE/*.md` for bug/feature/task templates
- Labels: apply type (bug/feature/chore), priority, and area labels
- Title: clear, actionable, follows project conventions
- Description: context, steps to reproduce (bug), acceptance criteria (feature)
- Assignee: assign to responsible person or leave unassigned for triage

### character-design-sheet
- Turnaround sheets: generate front/3-4/side/back views with identical description except angle
- Consistency anchors: use detailed, specific descriptions (hair style, eye color, clothing, accessories)
- Color palette: define exact colors early (navy blue, bright green, etc.)
- Style consistency: keep art style descriptor constant (concept art, clean lines, white background)
- Reference images: generate full-body neutral pose first, then variations
- FLUX LoRA: for ongoing projects with many images, train custom LoRA on character set
- Expression sheets: grid of emotions (happy, sad, angry, surprised) with same character design

### kids-book-writer
- Age-appropriate vocabulary: 50-100 words (ages 2-3), 200-400 (ages 4-5), 400-800 (ages 6-7), 800-1500 (ages 8-9)
- Perfect meter and rhythm: read-aloud tested, consistent syllable patterns, no forced inversions
- Repetition and refrains: use predictable patterns for engagement and memory
- Story arc: clear beginning/middle/end, relatable characters, satisfying resolution
- Values naturally woven: kindness, empathy, courage embedded in story, not preachy
- Interactive elements: call-and-response, counting, finding, naming
- Sight words integration: include age-appropriate high-frequency words
- Illustration guidance: describe scenes with sensory details for illustrators

### midjourney-prompt-engineering
- V7 prompt structure: `[subject] [action] [details] [environment] [lighting] [mood] [style] --parameters`
- Style references: `--sref <URL>` for style consistency, `--oref <URL>` for character reference
- Aspect ratios: `--ar 16:9` (landscape), `--ar 9:16` (portrait), `--ar 1:1` (square)
- Quality control: score 7 dimensions (subject, lighting, color, mood, composition, material, spatial)
- Iteration protocol: analyze gaps, rewrite specific keywords, test incrementally
- Keyword effectiveness: track what works per category (lighting: golden hour, mood: whimsical, etc.)
- Avoid over-prompting: MJ V7 is intelligent, prefer concise natural language over keyword spam
- Style codes: use community-tested codes for consistent aesthetics across generations

### mockumentary-screenplay
- Fountain format: plain text screenplay (INT./EXT., CHARACTER, dialogue, action)
- Talking heads: scene heading includes "TALKING HEAD", character speaks to off-camera interviewer
- Documentary crew: characters acknowledge camera, speak to it, interact with crew
- Verite scenes: natural action without interview framing, fly-on-wall perspective
- Parentheticals sparingly: only for crucial direction, avoid over-directing actors
- Scene headings: INT./EXT. LOCATION - TALKING HEAD/VERITE - TIME
- Natural dialogue: realistic speech patterns, interruptions, overlaps
- Visual storytelling: show through action, minimize expository dialogue

### prompt-engineering-patterns
- Few-shot learning: 2-5 examples with input-output pairs, select diverse representative cases
- Chain-of-thought: add "Let's think step by step" or provide reasoning traces in examples
- Structured outputs: use Pydantic schemas with `with_structured_output()` for reliable JSON
- System prompts: define role, constraints, output format, safety guidelines upfront
- Template variables: use `{variable}` for dynamic content, f-strings for complex logic
- Optimization: measure accuracy/consistency, A/B test variations, reduce tokens without quality loss
- Error handling: validate outputs, handle malformed responses, provide fallback behavior
- Context window: balance example count vs available tokens, prioritize recent/relevant context

### storytelling
- SCAR framework: Situation → Complication → Action → Resolution
- Audience first: identify hero (customer persona), their obstacle, their stakes
- Sensory detail: use vivid language, specific metrics, concrete examples (not abstract claims)
- Character quotes: record real customer language from interviews for authenticity
- Moral/CTA: tie resolution to product value, explicit next step
- Story inventory: log customer, industry, proof points for reuse
- Tailor per persona: swap metaphors/analogies so stories feel personalized
- Align with positioning: every story reinforces current messaging, no mixed signals

### workflow-orchestration-patterns
- Workflows vs Activities: workflows = orchestration logic (deterministic), activities = external calls (can fail)
- Determinism required: workflows MUST produce same output for same input, no random(), no time.now()
- Activities are idempotent: calling N times = calling once, use unique IDs to prevent duplicates
- Saga pattern: register compensation BEFORE executing step, run compensations in reverse (LIFO) on failure
- Long-running workflows: state persists automatically, workflows can run for years despite infrastructure failures
- Timeouts and retries: built-in for activities, exponential backoff, circuit breaker patterns
- Human-in-the-loop: use signals or activities with long timeouts for approval steps
- Versioning: use workflow versioning for deployments, old versions finish on old code

### video-generator-orchestrator
- Orchestrate 6 sequential agents: Character → Dialogue → Scenography → Cinematography → Scriptwriter → Prompt Engineer
- STOP after each agent, show results, WAIT for explicit approval ("apruebo", "sí", "continúa") before proceeding
- Save each phase to Engram: `topic_key = "video-gen/{story-slug}/phase-{N}"`, `type = "decision"`
- If user gives feedback → re-run current agent with constraints, don't proceed to next
- Character Agent: JSON array of characters with physical traits + MidJourney consistency tags (use character-design-sheet skill)
- Dialogue Agent: JSON array of scenes with dialogue, duration, age-appropriate vocabulary (use kids-book-writer skill for word limits)
- Scenography Agent: JSON array of scene descriptions with location, mood, color palette, props (use storytelling skill)
- Cinematography Agent: JSON array of shots with type, angle, movement, duration (shorter for younger ages)
- Scriptwriter Agent: Unified text script synchronizing all elements (use mockumentary-screenplay for structure)
- Prompt Engineer Agent: MidJourney V7 prompts per shot with `--ar 16:9`, style consistency, character tags (use midjourney-prompt-engineering skill)
- Recovery: Search Engram `"video-gen/{story-slug}"`, find latest phase, offer to resume
- Final output: Markdown document with all prompts + character consistency tags + Engram archive references

---

## Project Conventions

No project-specific convention files detected (empty project).

---

## Notes

- SDD workflow skills (sdd-explore, sdd-propose, etc.) are excluded — they are orchestrator tools, not coding skills
- Project is empty (no code yet), so no stack-specific skills are active
- **NEW: 7 domain-specific skills installed for AI video generation**:
  - ✅ **character-design-sheet** — turnaround views, expression sheets, consistency techniques
  - ✅ **midjourney-prompt-engineering** — MJ V7 prompts, style refs, scoring framework
  - ✅ **kids-book-writer** — age-appropriate content (2-9 years), rhyming, story arcs
  - ✅ **storytelling** — SCAR framework, customer narratives, sensory detail
  - ✅ **mockumentary-screenplay** — Fountain format, talking heads, dialogue (adaptable for storyboarding)
  - ✅ **prompt-engineering-patterns** — few-shot, chain-of-thought, structured outputs
  - ✅ **workflow-orchestration-patterns** — Temporal workflows, saga patterns, human-in-the-loop

**Still missing (domain-specific for video production)**:
  - ❌ `cinematography` — camera angles, shot types, framing, lighting for video storytelling
  - ❌ `scenography` — set design, location description, props, atmosphere
  - ❌ `video-editing-workflow` — scene transitions, pacing, cuts, timing

**These can be created using `skill-creator` or adapted from existing skills** (mockumentary-screenplay covers some cinematography basics)

---

## Recommendations

1. **Create missing cinematography skill**: Use `skill-creator` to document camera angles (wide, medium, close-up), shot types (establishing, POV, over-shoulder), framing rules (rule of thirds), and lighting techniques (3-point, natural, dramatic)

2. **Create scenography skill**: Document set design principles, location description templates, prop catalogs, and atmosphere/mood creation for children's content

3. **Stack selection**: Confirm Python + LangGraph + FastAPI stack, then install pytest to enable TDD workflow

4. **Testing setup**: Install pytest + pytest-cov to enable Strict TDD Mode:
   ```bash
   pip install pytest pytest-asyncio pytest-cov ruff mypy
   ```

5. **Next phase**: Run `/sdd-explore multi-agent-video-pipeline` to investigate LangGraph patterns for orchestrating the 6-agent workflow (Character → Dialogue → Scenography → Cinematography → Script → Prompts)
