# MCP Agents Directory

This directory contains MCP-compliant agents for the video-generator-orchestrator workflow. Each agent is a modular, self-contained component that handles one phase of the video generation pipeline.

## Directory Structure

```
agents/
├── character-agent/
│   ├── agent.json          # MCP config (capabilities, inputs, outputs, dependencies)
│   ├── prompt.md           # System prompt (instructions, rules, examples)
│   └── examples/           # Optional: few-shot examples
├── dialogue-agent/
├── scenography-agent/
├── cinematography-agent/
├── scriptwriter-agent/
├── prompt-engineer-agent/
└── README.md               # This file
```

## MCP Agent Structure

### agent.json (MCP 2024-11-05 Schema)

**Required fields**:
- `name` (string): Agent identifier (kebab-case, e.g., "character-agent")
- `version` (string): Semantic version (e.g., "1.0.0")
- `description` (string): Brief purpose description
- `runtime` (string): Must be "mcp"
- `protocol_version` (string): Must be "2024-11-05"
- `capabilities` (object): Tools, resources, prompts exposed by agent
- `inputs` (object): Input schema (types, descriptions, required flags)
- `outputs` (object): Output schema (structured response format)
- `dependencies` (object): External dependencies (skills, other agents)

**Example**:
```json
{
  "name": "character-agent",
  "version": "1.0.0",
  "description": "Extract characters with MidJourney consistency tags",
  "runtime": "mcp",
  "protocol_version": "2024-11-05",
  "capabilities": {
    "tools": ["extract_characters", "generate_consistency_tags"],
    "resources": ["character-design-patterns"],
    "prompts": ["character_extraction_prompt"]
  },
  "inputs": {
    "story_text": {"type": "string", "required": true},
    "target_age": {"type": "string", "enum": ["2-3", "4-5", "6-7", "8-9"], "required": true},
    "selected_style": {"type": "string", "required": true}
  },
  "outputs": {
    "characters": {"type": "array", "items": {...}}
  },
  "dependencies": {
    "skills": ["character-design-sheet", "kids-book-writer"]
  }
}
```

### prompt.md (System Prompt)

**Recommended structure**:
1. **Header**: Agent name and role description
2. **Purpose**: What the agent does and why
3. **Inputs**: Detailed descriptions of each input parameter
4. **Output Format**: Expected response structure with examples
5. **Rules**: Numbered list of constraints, guidelines, best practices (10-20 rules typical)
6. **Skills Applied**: Which skills from the registry this agent uses
7. **Validation Checklist**: Pre-return checks to ensure quality

**Example excerpt**:
```markdown
# Character Agent

You are a character extraction specialist for children's video content.

## Purpose
Extract and describe all characters with visual consistency for MidJourney.

## Inputs
- **story_text** (string, required): Full story to analyze
- **target_age** (enum, required): ["2-3", "4-5", "6-7", "8-9"]
...

## Rules
1. Identify ALL named characters (protagonist, antagonist, supporting)
2. No duplicates — each character appears exactly once
3. Use age-appropriate vocabulary (kids-book-writer guidelines)
...
```

## How to Add a New Agent

### Step 1: Create Directory

```bash
mkdir agents/my-new-agent
```

### Step 2: Create agent.json

```bash
cd agents/my-new-agent
# Copy template from existing agent or create from scratch
```

**Minimal template**:
```json
{
  "name": "my-new-agent",
  "version": "1.0.0",
  "description": "What this agent does",
  "runtime": "mcp",
  "protocol_version": "2024-11-05",
  "capabilities": {
    "tools": ["tool1", "tool2"],
    "resources": [],
    "prompts": ["main_prompt"]
  },
  "inputs": {
    "input1": {"type": "string", "required": true}
  },
  "outputs": {
    "output1": {"type": "object"}
  },
  "dependencies": {
    "skills": []
  }
}
```

### Step 3: Create prompt.md

Write system prompt following the structure above. Include:
- Clear role definition
- Detailed input/output descriptions
- Numbered rules (10-20)
- Validation checklist

### Step 4: Validate

```bash
cd ../..  # Back to project root
python validate_agent.py
```

Validation checks:
- JSON parses correctly
- Required MCP fields present
- `protocol_version` = "2024-11-05"
- `runtime` = "mcp"
- `prompt.md` exists

### Step 5: Update Orchestrator (if new phase)

If your agent is a NEW phase (not replacing existing), update orchestrator workflow:

1. Add phase to workflow diagram in `video-generator-orchestrator/SKILL.md`
2. Add agent loading call in phase execution
3. Update compact rules (if needed)

## Skill Dependencies and Compact Rule Injection

### How It Works

1. **Agent declares dependencies** in `agent.json`:
   ```json
   "dependencies": {
     "skills": ["character-design-sheet", "kids-book-writer"]
   }
   ```

2. **Orchestrator reads skill-registry** (from Engram or `.atl/skill-registry.md`)

3. **Orchestrator extracts compact rules** for those specific skills

4. **Orchestrator injects rules** into agent prompt:
   ```markdown
   {original prompt.md content}
   
   ---
   
   ## Project Standards (auto-resolved)
   
   **character-design-sheet**:
   - Turnaround sheets: generate front/3-4/side/back views
   - Consistency anchors: use detailed, specific descriptions
   ...
   
   **kids-book-writer**:
   - Age-appropriate vocabulary: 50-100 words (ages 2-3), 200-400 (ages 4-5)
   - Perfect meter and rhythm: read-aloud tested
   ...
   ```

5. **Agent receives full context** without needing to read registry itself

### Why This Matters

- **Compaction-safe**: Orchestrator re-reads registry on each launch (no stale cache)
- **Context isolation**: Sub-agents don't have memory access — rules arrive pre-digested
- **Consistency**: All agents using same skill get identical rules
- **Maintainability**: Update rules in ONE place (registry) → propagates to all agents

### Adding Skill Dependencies

To add a skill dependency to an existing agent:

1. Edit `agent.json`:
   ```json
   "dependencies": {
     "skills": ["existing-skill", "new-skill"]
   }
   ```

2. Validate:
   ```bash
   python validate_agent.py
   ```

3. Test that orchestrator injects rules correctly (check agent context in logs)

## Feature Flag: MCP Mode vs Legacy Mode

### Environment Variable

- **`USE_MCP_AGENTS=true`**: Load agents from `agents/` directory (MCP protocol)
- **`USE_MCP_AGENTS=false`** (default): Use legacy inline definitions from `SKILL.md.legacy`

### Setting the Flag

**PowerShell**:
```powershell
$env:USE_MCP_AGENTS = "true"
```

**Bash** (Git Bash, WSL):
```bash
export USE_MCP_AGENTS=true
```

**Config file** (if supported by your system):
```yaml
# .env or similar
USE_MCP_AGENTS=true
```

### Graceful Degradation

If MCP mode fails for ANY reason:
- Missing agent file
- Corrupt JSON schema
- Filesystem error
- Skill registry not found

Orchestrator will:
1. Log warning with error details
2. Automatically fall back to `SKILL.md.legacy`
3. Continue workflow without interruption

**No workflow breaks due to MCP issues.**

### Rollback Procedure

If you encounter issues with MCP mode:

1. **Quick rollback** (< 30 seconds):
   ```powershell
   $env:USE_MCP_AGENTS = "false"
   # Restart orchestrator or reload skill
   ```

2. **Verify legacy mode**:
   - Orchestrator should log: "Using legacy agent definitions from SKILL.md.legacy"
   - Workflow behavior identical to pre-migration

3. **No file deletion needed**:
   - `agents/` directory coexists with `SKILL.md.legacy`
   - Both modes use same Engram persistence
   - Switching modes doesn't affect saved workflows

## Agent Registry (Discovery)

When orchestrator starts with `USE_MCP_AGENTS=true`:

1. **Scan** `agents/*/agent.json` files
2. **Validate** each schema against MCP 2024-11-05 spec
3. **Fail-fast** if any agent invalid (prevents partial loading)
4. **Build registry**: `{agent_name: AgentConfig}`
5. **Log** discovered agents: "✅ Discovered 6 MCP agents: [character-agent, dialogue-agent, ...]"

### Error Handling

**AgentNotFoundError**:
```
Agent 'my-agent' not found in agents/
Available agents: [character-agent, dialogue-agent, ...]
Expected path: agents/my-agent/agent.json
```

**InvalidMCPSchemaError**:
```
Agent scriptwriter-agent schema invalid: missing 'protocol_version'
Path: agents/scriptwriter-agent/agent.json
Required: name, version, runtime, protocol_version, capabilities
```

**NoAgentsFoundError**:
```
No valid MCP agents found in agents/
Ensure agents/ directory contains subdirectories with agent.json files
```

## Testing

### Unit Test: Single Agent

```bash
python validate_agent.py
```

### Integration Test: Full Workflow

```bash
# Set MCP mode
$env:USE_MCP_AGENTS = "true"

# Run existing workflow (uses agents/ instead of SKILL.md)
# Example: luna-y-la-estrella-perdida story
```

Compare outputs:
- Character count matches legacy
- Scene count matches legacy
- Prompt count matches legacy
- Quality consistent with legacy

### Error Scenario Tests

1. **Missing agent**:
   - Delete `agents/character-agent/agent.json`
   - Expect: AgentNotFoundError → fallback to legacy

2. **Corrupt schema**:
   - Remove `"name"` field from `agent.json`
   - Expect: InvalidMCPSchemaError → fallback to legacy

3. **Missing prompt.md**:
   - Delete `agents/dialogue-agent/prompt.md`
   - Expect: FileNotFoundError → fallback to legacy

## Maintenance

### Updating an Agent

1. Edit `prompt.md` to change rules or examples
2. Edit `agent.json` to change inputs/outputs/dependencies
3. Increment `version` in `agent.json` (semantic versioning)
4. Validate: `python validate_agent.py`
5. Test with existing workflow to verify no regressions

### Updating All Agents

When updating a cross-cutting concern (e.g., all agents need new output field):

1. Update all 6 `agent.json` files
2. Update all 6 `prompt.md` files
3. Validate all: `python validate_all_agents.py`
4. Increment versions (breaking change → major version bump)
5. Test full workflow

### Deprecating an Agent

1. Remove agent directory: `rm -r agents/deprecated-agent`
2. Remove from orchestrator workflow (if phase removed)
3. Update documentation
4. Ensure workflows don't reference deprecated agent

## Migration Notes

This `agents/` directory structure replaces the monolithic inline agent definitions in `video-generator-orchestrator/SKILL.md`. The original definitions are preserved in `SKILL.md.legacy` for rollback purposes.

**Migration benefits**:
- **Modularity**: Each agent self-contained, easier to test/update
- **Versioning**: Track agent changes independently
- **Reusability**: Agents can be shared across projects
- **Discovery**: Dynamic loading via MCP protocol
- **Type safety**: JSON schema validation catches errors early

**Backward compatibility**:
- Feature flag (`USE_MCP_AGENTS`) enables gradual adoption
- Legacy mode available for instant rollback
- Both modes produce identical outputs (validated in Phase 10 testing)

## Resources

- **MCP Protocol Spec**: [https://modelcontextprotocol.io/spec/2024-11-05](https://modelcontextprotocol.io/spec/2024-11-05)
- **Skill Registry**: `.atl/skill-registry.md` or Engram topic `skill-registry`
- **Orchestrator Skill**: `.agents/skills/video-generator-orchestrator/SKILL.md`
- **Legacy Definitions**: `.agents/skills/video-generator-orchestrator/SKILL.md.legacy` (created after migration)

## Support

For issues with MCP agents:

1. Check logs for error messages (AgentNotFoundError, InvalidMCPSchemaError)
2. Validate schema: `python validate_agent.py` or `python validate_all_agents.py`
3. Test legacy mode fallback: `$env:USE_MCP_AGENTS = "false"`
4. Consult orchestrator SKILL.md "MCP Agent Discovery" section
5. Review this README.md for troubleshooting guidance
