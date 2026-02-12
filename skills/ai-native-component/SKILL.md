---
name: ai-native-component
description: Guide for designing AI-native ODA Components including MCP server integration, dependent AI models, A2A protocol support, AI Gateway configuration, and evaluation frameworks. Use this skill when working on AI-native Canvas features, MCP endpoints, agent components, or AI model integration.
---

# AI-Native Component — Skill Instructions

## Overview

The AI-Native Canvas extends the ODA Component model with three capabilities:

1. **MCP (Model Context Protocol)** — Expose component APIs as tools for AI agents
2. **Dependent Models** — Declare AI model requirements in the component spec
3. **A2A (Agent-to-Agent)** — Enable agent-to-agent communication

Reference design: `AI-Native-Canvas-design.md` in the repository root.

## MCP Server Integration

### Component Spec Extension

Components can expose MCP servers alongside traditional REST APIs:

```yaml
coreFunction:
  exposedAPIs:
    - name: productcatalog-mcp
      apiType: mcp
      implementation: <mcp-service-name>
      path: /mcp
      port: 3001
```

### MCP-Specific Considerations

- MCP uses **long-running HTTP connections** (SSE/streaming) — API Gateways need special configuration for persistent connections
- MCP descriptions must be **natural language** (for AI agent consumption, unlike Swagger)
- MCP wrappers can be auto-generated from Swagger files with enhanced descriptions
- MCP operators configure API Gateways for long-running connections

### Existing Implementation

Test data with MCP: `feature-definition-and-test-kit/testData/productcatalog-dynamic-roles-v1/`

```yaml
component:
  MCPServer:
    enabled: true
```

With corresponding Deployment and Service templates for the MCP server container.

Production MCP service: `source/tmf-services/MCP_Resource_Inventory/`

### Canvas Resource Inventory via MCP

The Canvas exposes a TMF639 Resource Inventory API as an MCP server, allowing AI agents to query: "What resources are available in the ODA Canvas?"

## Dependent Models (Design Phase)

> **Note**: `dependentModels` is documented in the design but **not yet in the CRD schema**. This section describes the proposed extension.

### Proposed Spec Extension

```yaml
spec:
  dependentModels:
    - name: primary-llm
      description: "Main language model for natural language processing"
      priority: 1
      useCase: "Customer query understanding and response generation"
      guardrails:
        maxTokensPerRequest: 4096
        contentFilter: strict
    - name: embedding-model
      description: "Text embedding for semantic search"
      priority: 2
      useCase: "Product catalog semantic search"
```

### Model Lifecycle

1. Component declares model requirements in `dependentModels`
2. Canvas operator reads requirements
3. Operator matches against approved model catalog
4. Configures AI Gateway with access grants
5. Enforces guardrails (token limits, content filtering)
6. Tracks usage per model per component

### AI Gateway Services

The AI Gateway provides:
- **Auditing**: Log all AI interactions
- **Observability**: Token tracking, latency, error rates per model per component
- **Cost management**: Usage limits and billing attribution
- **Guardrails**: Content filtering, token limits, prompt injection protection

## A2A Protocol Support (Design Phase)

Agent components can expose **agent cards** as part of their YAML contract:
- Agent cards describe capabilities, input/output formats, and communication protocols
- Both MCP and A2A are being incorporated into the component specification

## Canvas AI Services

The AI-Native Canvas provides these platform services:

| Service | Purpose |
|---------|---------|
| **AI Models** | Foundation GenAI, embedding, multimodal, classical ML |
| **AI Gateway** | Guardrails, auditing, cost management |
| **Observability** | LangSmith, OpenLLMetry (OpenTelemetry extension) |
| **Evaluation Framework** | Pre-production and continuous post-production |
| **Use Case Registry** | Tags agents, tools, high-risk use cases (EU AI Act) |
| **Model Manager Operator** | Downloads → MLOps pipeline → deploys + API access |

## Evaluation Framework

### Pre-Deployment

Components should come packaged with evaluation datasets and tests:
- Accuracy, relevance, completeness benchmarks
- Baseline evaluation before deployment

### In-Production

- Continuous AI-based evaluation (e.g., LangGraph framework)
- Human evaluation interface: relevance, accuracy, completeness scoring
- Dashboard for tracking performance over time

## Key Assumptions

- Foundation models are consumed as services (not self-hosted by default)
- Canvas maintains an approved model catalog
- AI systems are non-deterministic — evaluation replaces traditional testing
- Additional Canvas services needed: vector databases, anonymization, chunking

## Do

- Use `apiType: mcp` for MCP endpoints in `exposedAPIs`
- Write natural language descriptions for MCP tool definitions
- Package evaluation datasets with AI-native components
- Configure API Gateways for long-running connections when using MCP
- Reference `AI-Native-Canvas-design.md` for architectural decisions

## Don't

- Don't add `dependentModels` to CRD YAML until the schema is updated
- Don't assume MCP connections behave like standard REST — they use SSE/streaming
- Don't skip evaluation framework for AI-native components
- Don't hard-code model provider endpoints — use Canvas AI Gateway
