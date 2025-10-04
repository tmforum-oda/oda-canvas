# AI Coding Assistants for ODA Canvas Development

## Overview


This document provides guidance on using assistants effectively within the ODA Canvas project, with a focus on enhancing developer productivity, encouraging consistent practices, and improving quality. 
There are sections for different popular coding assistants (many initially populated with TBD - feel free to add to these sections if you are using that particular AI Coding Assistant).


---

## GitHub Copilot

This section gives guidance on using [GitHub Copilot](https://github.com/features/copilot). 
It introduces advanced usage modes such as **Agent Mode**, discusses integration with **Model Context Protocol (MCP)**, and proposes the adoption of **Context7** to improve prompt clarity and reusability.

### GitHub Copilot: Best Practices

GitHub Copilot is a context-aware AI assistant for code completion and suggestion. When used effectively, it can accelerate development of Canvas components, conformance assets, Helm charts, CRDs, and documentation.

### Recommended Usage Scenarios
- Scaffold Kubernetes manifests (e.g., Helm charts, CRDs)
- Generate boilerplate for TMF Open APIs (e.g., TMF641)
- Write test cases and mocks
- Improve readability and add documentation

### Prompt Engineering Tips
- Comment your intent clearly before writing code
- Include type hints and function signatures for better completions
- Break tasks into small, well-scoped units

```python
# Define a Kubernetes CustomResourceDefinition for a Canvas component
# The component must include metadata, spec, and status fields
```

### Copilot instructions

Copilot will read repo-specific instructions from a `.github/copilot-instructions.md` file. This allows you to define frameworks, sdks, coding style guides and other references to help with the consistency and quality of the copilot assistance.

### Modes in Copilot 

GitHub Copilot Labs includes three modes, **Ask** for using Copilot to answer questions on your codebase, **Edit** for editing individual files,
and **Agent Mode**, which allows for longer-running assistance over multiple files and also supports integration with tools via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).



### Integrating with Model Context Protocol (MCP)

**MCP** is a standard for sharing structured context with AI systems. For ODA Canvas, you can apply MCP principles to:

- Pass architectural context and component metadata to the assistant
- Standardize prompts using structured context blocks
- Improve the traceability and reproducibility of AI-generated code

### Recommented MCP Tools

### Context7

[Context7](https://context7.com/) pulls up-to-date, version-specific documentation and code examples  and adds them to the coding assistant context.
See [https://github.com/upstash/context7](https://github.com/upstash/context7) for details on how to install and use Context7.

### GitHub MCP-Server

[Github MCP Server](https://github.com/github/github-mcp-server) rovides seamless integration with GitHub APIs, enabling advanced automation and interaction capabilities. 
It can interact with Issues, Pull Requests and code assets.

---

## Claude Code

This section gives guidance on using [Claude Code](https://claude.ai/code) from Anthropic. 
Claude Code is an interactive CLI tool that helps with software engineering tasks, offering deep codebase understanding, multi-file operations, and integration with development workflows.

### Claude Code: Best Practices

Claude Code is an advanced AI assistant designed specifically for software development. When used effectively, it can accelerate development of Canvas operators, Kubernetes manifests, BDD tests, and complex multi-component integrations.

### Recommended Usage Scenarios
- Analyze and refactor complex operator implementations across multiple files
- Generate comprehensive BDD test scenarios and step definitions
- Create and maintain Kubernetes CRDs and operator logic
- Debug multi-language integrations (Python operators, Java services, Node.js APIs)
- Implement TMF API specifications and Canvas component workflows

### Prompt Engineering Tips
- Provide clear context about the specific Canvas component or operator you're working with
- Reference the ODA Component Specification version when making changes
- Specify whether you're working with KOPF-based operators, Spring Boot services, or Vue.js components
- Include relevant Kubernetes resource types and TMF API standards

```bash
# Example: Ask Claude Code to analyze a component operator
claude analyze the component-management operator and suggest improvements for handling v1beta4 to v1 migrations
```

### Claude Code Configuration

Claude Code automatically reads repo-specific context from the `CLAUDE.md` file. This file provides essential information about:

- Development commands for different technology stacks
- Architecture patterns and operator types
- Testing approaches and BDD scenarios
- Canvas-specific concepts and terminology

See [CLAUDE.md](CLAUDE.md) for the complete configuration and development guidance.

### Advanced Features

Claude Code supports complex multi-step operations ideal for Canvas development:

- **Multi-file refactoring**: Update operator implementations across related files
- **Cross-technology integration**: Work with Python operators, Java services, and JavaScript frontends simultaneously
- **BDD workflow support**: Create features, scenarios, and step definitions as cohesive units
- **Kubernetes resource management**: Generate, validate, and update CRDs, operators, and Helm charts

For detailed documentation on Claude Code capabilities, see the [official Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code).

---

## Gemini Code Assist

[https://codeassist.google/](https://codeassist.google/)

TBD 

---

## Amazon Q Developer (formerly CodeWhisperer)

[https://aws.amazon.com/q/developer/build](https://aws.amazon.com/q/developer/build)

TBD

---

## Cursor

[https://www.cursor.com/](https://www.cursor.com/)

TBD




