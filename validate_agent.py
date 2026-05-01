import json
import sys

try:
    with open('agents/character-agent/agent.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('✅ Valid JSON Schema')
    print(f'Agent: {data["name"]} v{data["version"]}')
    print(f'Protocol: {data["protocol_version"]}')
    print(f'Capabilities: {len(data["capabilities"]["tools"])} tools')
    print(f'Dependencies: {len(data["dependencies"]["skills"])} skills')
    
    # Validate required MCP fields
    required_fields = ["name", "version", "runtime", "protocol_version", "capabilities"]
    missing = [field for field in required_fields if field not in data]
    
    if missing:
        print(f'❌ Missing required fields: {missing}')
        sys.exit(1)
    
    if data["protocol_version"] != "2024-11-05":
        print(f'⚠️  Unexpected protocol version: {data["protocol_version"]}')
    
    if data["runtime"] != "mcp":
        print(f'⚠️  Unexpected runtime: {data["runtime"]}')
    
    print('✅ All MCP 2024-11-05 required fields present')
    
except Exception as e:
    print(f'❌ Validation failed: {e}')
    sys.exit(1)
