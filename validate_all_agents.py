import json
import sys
from pathlib import Path

agents_dir = Path('agents')
agent_dirs = [
    'character-agent',
    'dialogue-agent',
    'scenography-agent',
    'cinematography-agent',
    'scriptwriter-agent',
    'prompt-engineer-agent'
]

print("🔍 Validating all 6 MCP agents...\n")

errors = []
warnings = []
success_count = 0

for agent_name in agent_dirs:
    agent_path = agents_dir / agent_name / 'agent.json'
    prompt_path = agents_dir / agent_name / 'prompt.md'
    
    print(f"📋 {agent_name}:")
    
    # Check files exist
    if not agent_path.exists():
        errors.append(f"  ❌ {agent_name}/agent.json not found")
        continue
    if not prompt_path.exists():
        warnings.append(f"  ⚠️  {agent_name}/prompt.md not found")
    
    try:
        # Validate JSON
        with open(agent_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required MCP fields
        required_fields = ["name", "version", "runtime", "protocol_version", "capabilities"]
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            errors.append(f"  ❌ Missing fields: {missing}")
            continue
        
        # Validate protocol version
        if data["protocol_version"] != "2024-11-05":
            warnings.append(f"  ⚠️  Protocol: {data['protocol_version']} (expected 2024-11-05)")
        
        # Validate runtime
        if data["runtime"] != "mcp":
            errors.append(f"  ❌ Runtime: {data['runtime']} (expected 'mcp')")
            continue
        
        # Success
        print(f"  ✅ agent.json valid")
        print(f"  ✅ prompt.md exists ({prompt_path.stat().st_size // 1024}KB)")
        print(f"     Tools: {len(data['capabilities']['tools'])}, Skills: {len(data['dependencies']['skills'])}")
        success_count += 1
        
    except json.JSONDecodeError as e:
        errors.append(f"  ❌ JSON parse error: {e}")
    except Exception as e:
        errors.append(f"  ❌ Validation error: {e}")
    
    print()

print("=" * 50)
print(f"✅ {success_count}/6 agents validated successfully")

if warnings:
    print(f"\n⚠️  {len(warnings)} warnings:")
    for w in warnings:
        print(w)

if errors:
    print(f"\n❌ {len(errors)} errors:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("\n🎉 All agents valid and ready for MCP discovery!")
