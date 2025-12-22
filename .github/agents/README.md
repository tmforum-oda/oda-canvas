# GitHub Copilot Custom Agents

This directory contains custom GitHub Copilot agents for the ODA Canvas project. These agents are specialized assistants that help maintain documentation quality and automate routine tasks.

## Available Agents

### @docs - Documentation Specialist

**File:** `docs.md`

A documentation specialist for creating and improving README files, markdown documentation, and PlantUML diagrams in the ODA Canvas project.

**Capabilities:**
- README generation for Helm charts, operators, and test components
- Use case documentation following TM Forum ODA standards
- PlantUML diagram generation with auto-constructed proxy URLs
- Cross-reference validation between documentation layers
- Terminology consistency enforcement

**Scope:**
- Only works with `.md` and `.puml` files
- Never edits source code or helm-docs generated content

**Usage:**
```
@docs Create a README for the api-gateway-operator chart
@docs Generate a use case for component dependency management
@docs Create a sequence diagram showing authentication flow
@docs Validate cross-references in this use case
```

**Documentation:** See `docs/custom-copilot-documentation-agent.md`

---

### @plantuml-renderer - PlantUML to SVG Converter

**File:** `plantuml-renderer.md`

A specialized agent for converting PlantUML diagram files to SVG format using the Kroki online API, and updating markdown references to use local SVG files instead of remote PlantUML.com proxy URLs.

**Capabilities:**
- Single file conversion: Convert individual `.puml` files to `.svg`
- Batch directory conversion: Process all `.puml` files in a directory
- Markdown reference migration: Update proxy URLs to local SVG paths
- SVG validation: Verify generated SVGs are valid and complete
- Progress reporting: Clear feedback on conversion status

**Scope:**
- Only works with `.puml` files in `pumlFiles/` directories
- Updates `.md` files that reference PlantUML diagrams
- Never modifies `.puml` source files

**Usage:**
```
@plantuml-renderer convert usecase-library/pumlFiles/exposed-API-create.puml
@plantuml-renderer convert all in usecase-library/pumlFiles
@plantuml-renderer migrate all diagrams
```

**Technical Details:**
- Uses `scripts/plantuml-to-svg.js` Node.js utility
- Kroki API endpoint: `https://kroki.io/plantuml/svg/{encoded}`
- Encoding: PlantUML source → deflate compression → base64url
- SVG files saved in same directory as source `.puml` files

**Benefits:**
- Better performance (local files vs remote API calls)
- Offline availability (diagrams work without internet)
- Reduced external dependencies (no reliance on PlantUML.com)
- Version control (SVG files tracked in git)

---

## Agent Architecture

### File Format

Agents are defined using **markdown files with YAML frontmatter**:

```markdown
---
name: agent-name
description: Brief description of agent purpose
tools: ['edit', 'search', 'changes']
---

# Agent Title

Detailed instructions and guidelines for the agent...
```

### Required Fields

- `name`: Agent identifier used for invocation (e.g., `@docs`, `@plantuml-renderer`)
- `description`: One-line summary of agent capabilities
- `tools`: Array of tools the agent can use

### Available Tools

- `'edit'`: Edit files in the workspace
- `'search'`: Search for files and content
- `'changes'`: View and track file changes

### File Naming Convention

- Agent definition files use the agent name with `.md` extension
- Example: `docs.md` defines the `@docs` agent
- Example: `plantuml-renderer.md` defines the `@plantuml-renderer` agent

---

## Usage Guidelines

### When to Use @docs

- Creating or improving README files
- Documenting use cases with PlantUML diagrams
- Validating cross-references and terminology
- Ensuring documentation follows project standards

### When to Use @plantuml-renderer

- Converting PlantUML files to SVG format
- Migrating from remote proxy URLs to local SVG files
- Batch processing diagram conversions
- Updating markdown references after diagram changes

### Agent Collaboration

The two agents work together:

1. **@docs** creates PlantUML source files (`.puml`) with proper naming and structure
2. **@plantuml-renderer** converts them to SVG and updates markdown references
3. Both maintain consistent file naming (kebab-case) and directory structure
4. Both work only with documentation files (never source code)

---

## Adding New Agents

To create a new custom agent:

1. Create a new `.md` file in `.github/agents/`
2. Add YAML frontmatter with `name`, `description`, and `tools`
3. Write detailed instructions in the markdown body
4. Document the agent's scope, capabilities, and constraints
5. Provide usage examples and invocation patterns
6. Update this README with the new agent information

---

## References

- **Project Instructions:** `.github/copilot-instructions.md`
- **Writing Style Guide:** `docs/writing-style.md`
- **Documentation Agent Guide:** `docs/custom-copilot-documentation-agent.md`
- **GitHub Copilot Documentation:** [docs.github.com/copilot](https://docs.github.com/en/copilot)

---

## Troubleshooting

### Agent Not Responding

- Ensure you're using the correct `@agent-name` syntax
- Check that the agent file exists in `.github/agents/`
- Verify the YAML frontmatter is valid

### Agent Behavior Issues

- Review the agent's instruction file for scope and constraints
- Check if the operation is within the agent's capabilities
- Verify file types and locations match agent's scope

### Tool Limitations

- Agents can only use tools specified in their `tools` array
- Some operations may require manual intervention
- Complex tasks may need multiple agent invocations

---

## Contributing

When modifying or creating agents:

1. Follow the established file format and structure
2. Document all capabilities and constraints clearly
3. Provide comprehensive usage examples
4. Test the agent thoroughly before committing
5. Update this README with any changes
6. Follow the project's code-of-conduct and contribution guidelines
