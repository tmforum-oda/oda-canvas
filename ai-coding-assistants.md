# AI Coding Assistants for ODA Canvas Development

## Overview


This document provides guidance on using assistants effectively within the ODA Canvas project, with a focus on enhancing developer productivity, encouraging consistent practices, and improving quality. 
There are sections for different popular coding assistants (many initially populated with TBD - feel free to add to these sections if you are using that particular AI Coding Assistant).

### Shared Configuration

All AI coding assistants share a common set of project instructions via **[AGENTS.md](AGENTS.md)** at the repository root. This file follows the cross-tool AGENTS.md standard and is read natively by Copilot, Claude Code, Cursor, Windsurf, Codex, and others. Directory-level `AGENTS.md` files in `source/`, `charts/`, `feature-definition-and-test-kit/`, etc. add folder-specific conventions.

**Agent Skills** (`/skills/`) provide on-demand domain knowledge that any AI assistant can load:

| Skill | Purpose |
|-------|--------|
| `ai-native-component` | Guide for designing AI-native ODA Components and MCP integration |
| `canvas-ops-tutorial` | Interactive tutorial for operating and exploring the ODA Canvas |
| `canvas-usecase-documentation` | Documentation templates, terminology, PlantUML |
| `create-oda-operator` | KOPF operator patterns, handler examples, Dockerfile and Helm guidance |
| `github-actions-debugging` | CI/CD workflow debugging, Docker build and pipeline tips |
| `helm-chart-development` | Umbrella chart patterns, sub-chart conventions, templating best practices |
| `oda-component-yaml` | ODA Component CRD schema guidance and example component YAMLs |
| `skill-creator` | Instructions for creating new skills and extending the skills catalog |
| `write-bdd-feature` | BDD/Gherkin conventions, step definitions, and test kit workflows |


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

Copilot reads repo-specific instructions from [AGENTS.md](AGENTS.md) (cross-tool standard) and `.github/copilot-instructions.md` (which redirects to `AGENTS.md`). Custom agents are defined in `.github/agents/` and on-demand skills in `.github/skills/`. See the [agents README](.github/agents/README.md) for the full catalog.

### Skills Symlinks for Copilot

Copilot and related tooling may look for on-demand skills under `.github/skills`. To ensure tools pick up the repository `skills/` folder, create a symbolic link from `.github/skills` to `skills/` (run from the repo root). See the `Setting Up Skills Symlinks` section for details.

Unix / macOS:

```sh
ln -s ./skills .github/skills
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Path .github -ErrorAction SilentlyContinue
New-Item -ItemType SymbolicLink -Path .github\skills -Target .\skills
```

Windows (CMD):

```cmd
mkdir .github 2>nul
mklink /D .github\skills skills
```

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

See [AGENTS.md](AGENTS.md) for the complete configuration and development guidance. (`CLAUDE.md` redirects to `AGENTS.md` for backward compatibility.)

### Skills Symlinks for Claude Code

Claude Code looks for on-demand skills under `.claude/skills`. To make the repository `skills/` directory available, create a symbolic link from `.claude/skills` to `skills/` (run from the repo root). See the `Setting Up Skills Symlinks` section for details.

Unix / macOS:

```sh
ln -s ./skills .claude/skills
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Path .claude -ErrorAction SilentlyContinue
New-Item -ItemType SymbolicLink -Path .claude\skills -Target .\skills
```


### Advanced Features

Claude Code supports complex multi-step operations ideal for Canvas development:

- **Multi-file refactoring**: Update operator implementations across related files
- **Cross-technology integration**: Work with Python operators, Java services, and JavaScript frontends simultaneously
- **BDD workflow support**: Create features, scenarios, and step definitions as cohesive units
- **Kubernetes resource management**: Generate, validate, and update CRDs, operators, and Helm charts

For detailed documentation on Claude Code capabilities, see the [official Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code).

---

## Windsurf (formerly Codeium)

This section gives guidance on using [Windsurf](https://windsurf.com/) from Codeium.
Windsurf is an agentic IDE built on VS Code that combines familiar interface with AI agents capable of understanding entire codebases and performing autonomous multi-step development tasks.

### Windsurf: Best Practices

Windsurf distinguishes itself through **Cascade** - deep codebase understanding that goes beyond file-level context. It can reason across entire Canvas project architectures and execute complex, goal-oriented development workflows autonomously.

### Recommended Usage Scenarios
- Implement complete Canvas features autonomously across multiple operators and services
- Perform complex refactoring across Python, Java, and Node.js codebases while maintaining consistency
- Migrate ODA Component specifications (v1beta4 to v1) across entire component ecosystems
- Debug multi-operator integration issues with cross-file dependency analysis
- Generate comprehensive BDD test scenarios with corresponding step definitions

### Prompt Engineering Tips
- Describe high-level goals rather than specific implementation steps
- Provide Canvas architectural context and ODA Component specification requirements
- Set clear boundaries for which files/directories should be modified
- Reference specific operator types (KOPF, Spring Boot, Vue.js) and Canvas versions

```bash
# Example: Agentic task for Windsurf
"Implement dependency resolution for Canvas components that validates TMF API dependencies across all operator versions, including BDD tests and integration with existing lifecycle management"
```

### Windsurf Configuration

Windsurf leverages Canvas project structure automatically:

- Reads `AGENTS.md` for Canvas development commands and architectural patterns (`.windsurf/rules/oda-canvas.md` redirects to `AGENTS.md`)
- Understands multi-technology relationships between KOPF operators, Spring Boot services, and Vue.js components
- Recognizes Canvas-specific patterns like component decomposition and API exposure

### Windsurf Modes

Windsurf provides two distinct interaction modes:

- **Chat Mode**: Interactive conversation for code analysis, questions, and guidance
- **Agent Mode**: Autonomous execution of complex multi-step development tasks with minimal supervision

### Advanced Features

Windsurf's agentic capabilities excel at Canvas development:

- **Cascade codebase understanding**: Traces dependencies and relationships across the entire Canvas project
- **Autonomous workflow execution**: Plans and executes multi-step development tasks without constant guidance
- **Cross-file consistency**: Maintains coherence across operators, CRDs, and Helm charts simultaneously
- **Self-correction**: Identifies and fixes issues during execution, adapting approach as needed

For detailed documentation on Windsurf capabilities, see the [official Windsurf documentation](https://docs.windsurf.com/).

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




