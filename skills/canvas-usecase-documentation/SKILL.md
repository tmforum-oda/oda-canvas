---
name: canvas-usecase-documentation
description: Guide for writing ODA Canvas documentation including README files, use case documents, PlantUML diagrams, and Helm chart docs. Covers templates, terminology standards, writing style conventions, cross-reference validation, and documentation structure patterns. Use this skill when creating or improving markdown documentation, use cases, or PlantUML diagrams in the ODA Canvas project.
---

# Canvas Use-Case Documentation — Skill Instructions

## Scope

This skill covers creation and improvement of:
- Markdown files (`*.md`)
- PlantUML files (`*.puml`)

Never edit source code files, or Helm-docs generated content (between `<!--- BEGIN PARAMS --->` and `<!--- END PARAMS --->` markers).

## Templates

Templates are available in `docs/templates/`:
- `chart-readme-template.md` — Helm chart documentation
- `operator-readme-template.md` — Operator documentation
- `use-case-template.md` — Use case documentation
- `test-component-readme-template.md` — Test component documentation
- `plantuml-sequence-template.puml` — PlantUML diagrams

## Exemplar Documentation

Study these files for style and structure:
- `README.md` — Main project README
- `source/operators/README.md` — Operators overview
- `source/operators/componentOperator/README.md` — Individual operator
- `usecase-library/UC002-Manage-Components.md` — Use case example
- `SecurityPrinciples.md` — Design document example
- `Canvas-design.md` — Architecture overview

## Terminology Standards

**Always capitalize:**
- "ODA Canvas" (never standalone "Canvas")
- "ODA Component"
- "Software Operators"
- "Component Management", "API Management", "Identity Management"
- "Kubernetes Operator Pattern"
- "Behaviour-Driven Development" (British spelling)

**Always hyphenate:**
- sub-resources, cloud-native, machine-readable, use-case (in titles)

**Use backticks for:**
- Custom Resource Definitions: `Component`, `ExposedAPI`, `DependentAPI`
- Kubernetes resources: `Deployment`, `Service`, `ConfigMap`
- Commands: `kubectl`, `helm`, `kopf`
- File paths: `README.md`, `values.yaml`
- Version identifiers: `v1`, `v1beta3`

**Bold on first use:**
- Key technical concepts: **operators**, **coreFunction**, **security**, **management**

## Documentation Structure Patterns

### Use-Case Documentation
```markdown
# {Verb} {Object} use case

Overview paragraph explaining the use case.

## Assumptions
- Bullet list of assumptions

## {Scenario name}
Description with PlantUML diagram.

![{diagram-name}](./pumlFiles/{diagram-filename}.svg)

[plantUML code]({relative-path-to-puml})

Link to BDD features at end.
```

### Operator README
```markdown
# {Operator Name}

Purpose/overview paragraph.

## Sequence Diagram
PlantUML diagram showing operator workflow.

## Reference Implementation
Description of implementation.

## Interactive development and Testing
Development instructions (include `kopf run --namespace=components --standalone` for Python/kopf operators).

## Build automation
CI/CD information.
```

### Helm Chart README
```markdown
# {Chart Name}

## Overview
Contextual description of what the chart does.

## Architecture
How it fits in the ODA Canvas.

<!--- BEGIN PARAMS --->
<!--- Helm-docs generated content - DO NOT EDIT --->
<!--- END PARAMS --->

## Usage Examples
Practical helm install commands.

## Troubleshooting
Common issues and solutions.

Links to:
- Related operators
- Relevant use cases
- Installation guide
```

## PlantUML Diagram Guidelines

**Output directories:**
- Use cases: `usecase-library/pumlFiles/`
- Design docs: `docs/pumlFiles/`
- Operators: `source/operators/pumlFiles/`

**Naming convention:**
- Use kebab-case: `uc002-install-component.puml`
- Pattern: `{use-case-id}-{scenario-name}.puml`

**Standard markdown pattern (using local SVG):**
```markdown
![{diagram-name}](./pumlFiles/{diagram-filename}.svg)

[plantUML code]({relative-path-to-puml})
```

**Standard actors:**
- Canvas, Component, Operator, Kubernetes API, API Gateway, Identity Management, Developer, Component Vendor

## Cross-Reference Validation

Always validate bidirectional links:
- Use cases ↔ BDD features: `usecase-library/UC###-*.md` ↔ `feature-definition-and-test-kit/features/UC###-F###-*.feature`
- Operator READMEs should reference use case sequence diagrams
- Use relative paths with `./` or `../`
- Always use forward slashes
- Verify target files exist

## Writing Style

Follow the comprehensive writing style guide in `docs/writing-style.md` which covers:
- Voice and tone (active voice, imperative mood, perspective)
- Sentence structure and length variation
- Heading hierarchy and capitalization
- Code blocks, links, and list formatting
- Markdown formatting conventions

The writing style guide is the single source of truth for all documentation formatting and style decisions.

## Key Reference Files

- `AGENTS.md` — Project-level conventions
- `docs/writing-style.md` — Comprehensive writing style guide
- `usecase-library/use-case-naming-conventions.md` — Use-case naming conventions

## Constraints

- NEVER edit source code files
- NEVER modify helm-docs generated content between markers
- NEVER create documentation without checking templates first
- NEVER use standalone "Canvas" — always "ODA Canvas"
- ALWAYS preserve existing PlantUML diagram URLs
- ALWAYS use British spelling "Behaviour-Driven Development" not "Behavior"
- ALWAYS check bidirectional cross-references when adding links
