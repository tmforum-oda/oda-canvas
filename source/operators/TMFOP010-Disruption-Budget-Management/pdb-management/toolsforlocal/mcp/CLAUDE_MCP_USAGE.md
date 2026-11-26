# Claude API + MCP Integration Usage Guide

## Prerequisites

1. **Claude API Key**: Get from [Anthropic Console](https://console.anthropic.com/)
2. **Port-forward running**: MCP server accessible at localhost:8090
3. **Python 3.8+** with virtual environment

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv claude_env
source claude_env/bin/activate
```

2. Install dependencies:
```bash
pip install -r toolsforlocal/requirements.txt
```

3. Set your Claude API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

4. Start port-forward to MCP server:
```bash
kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090
```

## Usage

### Interactive Mode
```bash
python toolsforlocal/claude_mcp_integration.py
```

Commands:
- `analyze pdb-demo` - Claude analyzes the namespace
- `recommend pdb-demo` - Claude recommends policies
- `chat` - Free-form conversation
- Any text - Send directly to Claude

### Python Script Usage

```python
from claude_mcp_integration import ClaudeMCPIntegration

# Initialize
integration = ClaudeMCPIntegration()

# Ask Claude to analyze
response = integration.analyze_namespace("pdb-demo")
print(response)

# Get recommendations
response = integration.recommend_policies("pdb-demo")
print(response)

# Custom prompt
response = integration.chat_with_tools(
    "What deployments in pdb-demo need better availability?"
)
print(response)
```

### Direct API Usage

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Define your MCP tools based on what's available
tools = [
    {
        "name": "analyze_cluster_availability",
        "description": "Analyze cluster-wide PDB coverage",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "detailed": {"type": "boolean"}
            }
        }
    }
]

# Send message with tools
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Analyze the pdb-demo namespace availability"
    }],
    tools=tools
)
```

## What Claude Can Do

With MCP tools, Claude can:

1. **Analyze** - Check PDB coverage, identify gaps
2. **Recommend** - Suggest optimal availability policies
3. **Create** - Generate availability policies (with your approval)
4. **Simulate** - Test policy impact before applying
5. **Update** - Modify deployment annotations
6. **Pattern Analysis** - Identify workload patterns

## Example Conversations

```
You: What's the PDB coverage in my pdb-demo namespace?
Claude: [Uses analyze_cluster_availability tool]
Claude: Your pdb-demo namespace has 100% PDB coverage with 15 deployments...

You: Which deployments need better availability settings?
Claude: [Uses recommend_policies tool]
Claude: Based on my analysis, payment-processor and auth-service should be mission-critical...

You: Create a policy for the payment services
Claude: [Uses create_availability_policy tool]
Claude: I'll create a mission-critical policy for your payment services...
```

## Troubleshooting

1. **Connection Error**: Check port-forward is running
2. **MCP Not Initialized**: Verify MCP server health: `curl http://localhost:8090/health`
3. **API Key Error**: Ensure ANTHROPIC_API_KEY is set correctly
4. **Tool Not Found**: MCP server may need restart

## Cost Optimization

- Claude 3.5 Sonnet: ~$3 per million input tokens
- Use caching for repeated analysis
- Batch multiple operations in one conversation
- Use specific namespaces instead of cluster-wide analysis