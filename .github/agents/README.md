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

**Skill:** Uses the `canvas-usecase-documentation` skill (`.github/skills/canvas-usecase-documentation/SKILL.md`) for detailed templates, terminology standards, and writing conventions.

**Scope:** Only works with `.md` and `.puml` files. Never edits source code or helm-docs generated content.

**Usage:**
```
@docs Create a README for the api-gateway-operator chart
@docs Generate a use case for component dependency management
@docs Create a sequence diagram showing authentication flow
@docs Validate cross-references in this use case
```

**Documentation:** See `docs/custom-copilot-documentation-agent.md`

---

### @bdd-feature-generator - BDD Feature Generator

**File:** `bdd-feature-generator.agent.md`

A specialized agent for creating BDD feature files and step definitions following TM Forum ODA Canvas conventions.

**Capabilities:**
- Gherkin feature file generation with correct tagging and structure
- JavaScript step definition stubs that reuse existing utilities
- README.md feature catalog updates
- Consistent naming conventions and patterns

**Skill:** Uses the `write-bdd-feature` skill (`.github/skills/write-bdd-feature/SKILL.md`) for Gherkin conventions, step definition templates, utility library usage, and the complete creation workflow.

**Usage:**
```
@bdd-feature-generator Create a BDD feature for UC008-F001 subscribed events
@bdd-feature-generator Add a scenario for component upgrade with new APIs
```

**Documentation:** See `docs/bdd-feature-generator-agent-guide.md`

---

### @plantuml-renderer - PlantUML to SVG Converter

**File:** `plantuml-renderer.md`

A specialized agent for converting PlantUML diagram files to SVG format using the Kroki online API, and updating markdown references to use local SVG files instead of remote PlantUML.com proxy URLs.

**Capabilities:**
- Single file conversion: Convert individual `.puml` files to `.svg`
- Batch directory conversion: Process all `.puml` files in a directory
- Markdown reference migration: Update proxy URLs to local SVG paths
- SVG validation: Verify generated SVGs are valid and complete

**Scope:** Only works with `.puml` files in `pumlFiles/` directories. Updates `.md` files that reference PlantUML diagrams. Never modifies `.puml` source files.

**Usage:**
```
@plantuml-renderer convert usecase-library/pumlFiles/exposed-API-create.puml
@plantuml-renderer convert all in usecase-library/pumlFiles
@plantuml-renderer migrate all diagrams
```

**Documentation:** See `docs/plantuml-to-svg-guide.md`

---

### @tutorial - ODA Canvas Tutorial

**File:** `tutorial.md`

An interactive tutorial agent for learning and exploring the ODA Canvas on Kubernetes. Guides users through architecture concepts, component deployment, API inspection, and more via context-aware menus.

**Capabilities:**
- Menu-driven interactive tutorial with 7 learning topics
- Live cluster exploration via kubectl and helm commands
- CRD schema education from live cluster, Helm templates, and example components
- Observability stack discovery and access
- Identity management exploration
- BDD test execution guidance

**Skill:** Uses the `canvas-ops-tutorial` skill (`.github/skills/canvas-ops-tutorial/SKILL.md`) for tutorial content, menu structure, interaction rules, and helper scripts.

**Scope:** Command line only — interacts with the cluster exclusively through terminal commands. Does not edit files.

**Usage:**
```
@tutorial
@tutorial Show me the deployed components
@tutorial How do ExposedAPIs work?
@tutorial Help me run BDD tests
```

---

## Agent Skills

Skills are on-demand knowledge bundles that agents (and any AI coding assistant) can load when needed. They live in `.github/skills/<skill-name>/SKILL.md`.

| Skill | Description | Used By |
|-------|-------------|---------|
| `write-bdd-feature` | Gherkin conventions, step definition templates, utility library usage, creation workflow | @bdd-feature-generator |
| `canvas-ops-tutorial` | Interactive Kubernetes tutorial: menus, CRD education, helper scripts, cluster exploration | @tutorial |
| `canvas-usecase-documentation` | Documentation templates, terminology, PlantUML guidelines, writing style | @docs |
| `create-oda-operator` | KOPF handler patterns, CRD watching, logging, Dockerfile, Helm chart, RBAC | Any agent |
| `oda-component-yaml` | v1 CRD schema, segments, ExposedAPIs, DependentAPIs, events, security roles | Any agent |
| `helm-chart-development` | Umbrella chart, sub-chart conventions, _helpers.tpl, versioning, dependencies | Any agent |
| `ai-native-component` | MCP server integration, dependent models, A2A protocol, AI Gateway, evaluation | Any agent |
| `github-actions-debugging` | CI/CD workflows, Docker builds, PR test pipeline, debugging commands | Any agent |

Skills are activated automatically when an AI assistant's prompt matches the skill description. They can also be loaded explicitly by referencing the SKILL.md path.

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

### Skill Format

Skills use a similar format with YAML frontmatter:

```markdown
---
name: skill-name
description: When to activate this skill (used for matching)
---

# Skill Title

Detailed conventions, templates, and workflow instructions...
```

### Design Principle

Agents are **thin personas** — they define scope, behavior rules, and tool access. The detailed domain knowledge lives in **skills** that can be shared across agents and AI tools.

---

## Adding New Agents or Skills

### New Agent
1. Create a new `.md` file in `.github/agents/`
2. Add YAML frontmatter with `name`, `description`, and `tools`
3. Write scope, behavior rules, and reference any relevant skills
4. Update this README

### New Skill
1. Create `.github/skills/<skill-name>/SKILL.md`
2. Add YAML frontmatter with `name` and `description`
3. Write detailed conventions, templates, and workflow instructions
4. Reference the skill from any agents that use it
5. Update this README's Agent Skills table

---

## References

- **Project Instructions:** `AGENTS.md`
- **Writing Style Guide:** `docs/writing-style.md`
- **Documentation Agent Guide:** `docs/custom-copilot-documentation-agent.md`
- **BDD Feature Generator Guide:** `docs/bdd-feature-generator-agent-guide.md`
- **PlantUML Conversion Guide:** `docs/plantuml-to-svg-guide.md`
