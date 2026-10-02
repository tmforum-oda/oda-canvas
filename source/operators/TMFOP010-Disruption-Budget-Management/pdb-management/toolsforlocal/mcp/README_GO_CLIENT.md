# Claude MCP Client - Go Version

## Setup

1. **Install dependencies:**
```bash
cd toolsforlocal
go mod tidy
```

2. **Set your Claude API key:**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'  # Your actual key
```

3. **Start port-forward:**
```bash
kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090
```

4. **Build and run:**
```bash
go build -o claude-mcp claude_mcp_client.go
./claude-mcp
```

## Usage

### Interactive Commands:
- `analyze pdb-demo` - Analyze namespace availability  
- `recommend pdb-demo` - Get policy recommendations
- `quit` - Exit

### As a library:

```go
import "path/to/toolsforlocal"

// Initialize
integration, err := NewClaudeMCPIntegration(apiKey, "http://localhost:8090/mcp")
if err != nil {
    log.Fatal(err)
}

// Use it
ctx := context.Background()
response, err := integration.AnalyzeNamespace(ctx, "pdb-demo")
fmt.Println(response)
```

## Features

- Native Go implementation
- Uses official Anthropic SDK
- Direct MCP server communication
- Tool calling support
- Interactive CLI mode

## Advantages over Python

- Single binary deployment
- No virtual environment needed  
- Better performance
- Native to your PDB operator codebase
- Can be integrated directly into operator if needed