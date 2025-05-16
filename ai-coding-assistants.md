# AI Coding Assistants for ODA Canvas Development

## Overview


This document provides guidance on using osing assistants effectively within the ODA Canvas project, with a focus on enhancing developer productivity, encouraging consistent practices, and improving quality. 
There are sections for different popular coding assistants (many initially populated with TBD - feel free to add to these sections if you are using that particular AI Coding Assistant).




## GitHub Copilot

This section gives guidance on using [GitHub Copilot](https://github.com/features/copilot). 
It introduces advanced usage modes such as **Agent Mode**, discusses integration with **Model Context Protocol (MCP)**, and proposes the adoption of **Context7** to improve prompt clarity and reusability.

---

## GitHub Copilot: Best Practices

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

---

## Copilot instructions

Copilot will read repo-specific instructions from a `.github/copilot-instructions.md` file. This allows you to define frameworks, sdks, coding style guides and other references to help with the consistency and quality of the copilot assistance.

## Modes in Copilot 

GitHub Copilot Labs includes three modes, **Ask** for using Copilot to answer questions on your codebase, **Edit** for editing individual files,
and **Agent Mode**, which allows for longer-running assistance over multiple files and also supports integration with tools via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).



## Integrating with Model Context Protocol (MCP)

**MCP** is a standard for sharing structured context with AI systems. For ODA Canvas, you can apply MCP principles to:

- Pass architectural context and component metadata to the assistant
- Standardize prompts using structured context blocks
- Improve the traceability and reproducibility of AI-generated code

## Recommented MCP Tools

### Context7

[Context7](https://context7.com/) pulls up-to-date, version-specific documentation and code examples  and adds them to the coding assistant context.
See [https://github.com/upstash/context7](https://github.com/upstash/context7) for details on how to install and use Context7.

### GitHub MCP-Server

[Github MCP Server](https://github.com/github/github-mcp-server) rovides seamless integration with GitHub APIs, enabling advanced automation and interaction capabilities. 
It can interact with Issues, Pull Requests and code assets.

### Gemini Code Assist

[https://codeassist.google/](https://codeassist.google/)

TBD 

## Amazon Q Developer (formerly CodeWhisperer)

[https://aws.amazon.com/q/developer/build](https://aws.amazon.com/q/developer/build)

TBD

## Cursor

[https://www.cursor.com/](https://www.cursor.com/)

TBD




