# AI + MCP Integration Clients

This directory contains Go-based clients to integrate AI assistants with your Kubernetes PDB Management MCP server.

## Available Clients

### 1. Claude Client (`claude-mcp`)
Uses Anthropic's Claude API with MCP tools for Kubernetes cluster analysis.

### 2. ChatGPT Client (`chatgpt-mcp`) 
Uses OpenAI's ChatGPT API with MCP tools for Kubernetes cluster analysis.

## Prerequisites

1. **Port-forward running**: MCP server accessible at localhost:8090
   ```bash
   kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090
   ```

2. **API Keys**: Get API keys from respective providers:
   - Claude: [Anthropic Console](https://console.anthropic.com/)
   - ChatGPT: [OpenAI Platform](https://platform.openai.com/)

## Setup

### Claude Client Setup

1. **Set API key:**
   ```bash
   export ANTHROPIC_API_KEY='sk-ant-...'  # Your actual key
   ```

2. **Build and run:**
   ```bash
   go build -o claude-mcp claude_mcp_client.go
   ./claude-mcp
   ```

### ChatGPT Client Setup

1. **Set API key:**
   ```bash
   export OPENAI_API_KEY='sk-...'  # Your actual key
   ```

2. **Build and run:**
   ```bash
   go build -o chatgpt-mcp chatgpt_mcp_client.go
   ./chatgpt-mcp
   ```

## Usage Examples

Both clients support the same types of queries:

### Interactive Commands
```bash
> analyze pdb-demo
> What's the PDB coverage in canvas namespace?
> Which deployments are most vulnerable to node failures?
> Create availability policies for payment services in pdb-demo namespace
> Compare availability between pdb-demo and canvas namespaces
> quit
```

### As a Library

**Claude Integration:**
```go
integration, err := NewClaudeMCPIntegration(apiKey, "http://localhost:8090/mcp")
if err != nil {
    log.Fatal(err)
}

ctx := context.Background()
response, err := integration.AnalyzeNamespace(ctx, "pdb-demo")
fmt.Println(response)
```

**ChatGPT Integration:**
```go
integration, err := NewChatGPTMCPIntegration(apiKey, "http://localhost:8090/mcp")
if err != nil {
    log.Fatal(err)
}

ctx := context.Background()
response, err := integration.AnalyzeNamespace(ctx, "pdb-demo")
fmt.Println(response)
```

## Available MCP Tools

Both clients have access to all 7 MCP tools:

1. **analyze_cluster_availability** - Analyze cluster-wide PDB coverage
2. **analyze_workload_patterns** - Identify deployment patterns
3. **recommend_availability_policies** - Get policy recommendations  
4. **create_availability_policy** - Create availability policies
5. **update_deployment_annotations** - Update deployment annotations
6. **simulate_policy_impact** - Simulate policy changes
7. **get_deployment_availability_status** - Get deployment status

## Key Features

- **Native Go implementation** - Single binary deployment
- **Pretty JSON formatting** - Human-readable output
- **Tool calling support** - Full MCP protocol implementation
- **Interactive CLI mode** - Easy to use interface
- **Library integration** - Can be embedded in other Go applications
- **Error handling** - Comprehensive error reporting
- **Timeout management** - Configurable timeouts

## Model Comparison

| Feature | Claude Client | ChatGPT Client |
|---------|---------------|----------------|
| Model | `claude-3-haiku-20240307` | `gpt-4-turbo-preview` |
| Max Tokens | 1024 | 1024 |
| Tool Support | ✅ Native | ✅ Function Calling |
| Cost | ~$0.25/1M input tokens | ~$10/1M input tokens |
| Speed | Very Fast | Fast |
| JSON Output | Excellent | Excellent |

## Troubleshooting

### Connection Issues
1. **Port-forward not running**: Start with `kubectl port-forward`
2. **MCP server unhealthy**: Check with `curl http://localhost:8090/health`
3. **API key issues**: Verify environment variables are set

### API Errors
- **Claude**: Check ANTHROPIC_API_KEY is valid
- **ChatGPT**: Check OPENAI_API_KEY is valid and has credits

### Performance Tips
- Use Claude for cost-effective analysis
- Use ChatGPT for more detailed explanations
- Both support the same MCP tools and capabilities

## Example Session

```bash
$ ./claude-mcp
Initializing Claude + MCP integration...
MCP server initialized successfully
Loaded 7 MCP tools

Claude + MCP Integration Ready!
--------------------------------------------------

> Which deployments would be affected by a node failure?

Claude is calling tool: analyze_cluster_availability

Tool result:
{
  "summary": {
    "totalDeployments": 23,
    "deploymentsWithPDB": 17,
    "deploymentsWithoutPDB": 6,
    "coveragePercentage": 73.91
  },
  "issues": [
    {
      "type": "deployment",
      "severity": "warning", 
      "resource": "coredns",
      "namespace": "kube-system",
      "description": "Multi-replica deployment without PDB"
    }
  ]
}

Claude: Based on the analysis, 6 deployments would be most affected by node failures:

1. **coredns** (kube-system) - 2 replicas, no PDB - CRITICAL
2. **cert-manager** components - Single replica each, no PDBs
3. **metrics-server** (kube-system) - Single replica, no PDB
...
```

## Integration Benefits

✅ **Natural Language Interface** - Ask questions in plain English
✅ **Real-time Cluster Analysis** - Live data from your Kubernetes cluster  
✅ **Intelligent Recommendations** - AI-powered policy suggestions
✅ **Automated Policy Creation** - Generate policies from descriptions
✅ **Multi-namespace Analysis** - Compare across namespaces
✅ **Rich Formatting** - Clean, readable JSON output