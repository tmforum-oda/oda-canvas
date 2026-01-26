# Documentation Templates

This directory contains templates for creating consistent documentation across the ODA Canvas project. These templates are used by the `@docs` GitHub Copilot agent and can also be used manually by contributors.

## Available Templates

### 1. Chart README Template
**File**: [chart-readme-template.md](chart-readme-template.md)

**Use for**: Helm charts in `charts/` directory

**Purpose**: Enhance auto-generated helm-docs content with contextual information about the chart's role in the ODA Canvas architecture.

**Key Sections**:
- Overview explaining the chart's purpose
- Architecture showing integration with operators and components
- Usage examples with helm install commands
- Troubleshooting common issues

### 2. Operator README Template
**File**: [operator-readme-template.md](operator-readme-template.md)

**Use for**: Operators in `source/operators/` directory

**Purpose**: Document operator implementation, architecture, and development workflows.

**Key Sections**:
- Purpose and overview
- PlantUML sequence diagram
- Reference implementation details
- Interactive development and testing instructions
- Build automation

### 3. Use-Case Template
**File**: [use-case-template.md](use-case-template.md)

**Use for**: Use case documentation in `usecase-library/` directory

**Purpose**: Create implementation-agnostic use case documentation following TM Forum ODA standards.

**Key Sections**:
- Overview with scope
- Assumptions (prerequisites)
- Scenario sections with PlantUML diagrams
- Links to BDD features

### 4. Test Component README Template
**File**: [test-component-readme-template.md](test-component-readme-template.md)

**Use for**: Test data components in `feature-definition-and-test-kit/testData/` directory

**Purpose**: Document test ODA Components with TMF API implementations.

**Key Sections**:
- TMF Forum references
- Core/Management/Security function breakdown
- Microservices architecture
- Installation and configuration

### 5. PlantUML Sequence Template
**File**: [plantuml-sequence-template.puml](plantuml-sequence-template.puml)

**Use for**: Sequence diagrams in `usecase-library/pumlFiles/` or `docs/pumlFiles/`

**Purpose**: Create consistent sequence diagrams for Canvas interactions.

**Standard Actors**:
- Canvas
- Component
- Operator
- Kubernetes API

## Using Templates

### With GitHub Copilot
Invoke the documentation agent with the `@docs` keyword:

```
@docs Create a README for the new api-gateway-operator chart
@docs Generate a use case for component lifecycle management
@docs Create a sequence diagram showing API exposure workflow
```

The agent will automatically select and apply the appropriate template.

### Manual Usage

1. Copy the relevant template file
2. Replace placeholder text (indicated with `{...}` brackets)
3. Fill in all required sections
4. Follow the [Writing Style Guide](../writing-style.md)
5. Validate cross-references

## Template Placeholders

Templates use the following placeholder conventions:

- `{Name}` - Replace with actual name (e.g., component name, operator name)
- `{Description}` - Replace with specific description
- `{Version}` - Replace with version number
- `{TMF-API-Number}` - Replace with TMF API number (e.g., TMF620)
- `{Use-Case-ID}` - Replace with use case identifier (e.g., UC002)
- `[Optional Section]` - Include only if applicable
- Comments `<!-- ... -->` - Guidance to be removed

## Template Maintenance

### Proposing Template Changes

If you identify improvements to templates:

1. Create an issue describing the proposed change
2. Explain the rationale (consistency, clarity, completeness)
3. Provide examples from existing documentation
4. Submit a PR with the template update

### Template Evolution

Templates evolve as documentation patterns mature. When updating templates:

- Maintain backward compatibility where possible
- Document breaking changes in PR description
- Update this README with change rationale
- Update [Writing Style Guide](../writing-style.md) if patterns change

## Template Validation

Before using templates in production documentation:

✅ **Verify**:
- All placeholder values replaced
- Required sections completed
- Cross-references valid
- PlantUML diagrams render correctly
- Terminology follows [.github/copilot-instructions.md](../../.github/copilot-instructions.md)
- Writing style matches [docs/writing-style.md](../writing-style.md)
- helm-docs content not manually edited (charts only)

## Related Documentation

- [Writing Style Guide](../writing-style.md) - Detailed style conventions
- [Use-Case Naming Conventions](../../usecase-library/use-case-naming-conventions.md) - Use case standards
- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute
- [GitHub Copilot Instructions](../../.github/copilot-instructions.md) - Project overview for AI assistants

## Questions or Issues?

If you have questions about template usage or need assistance:

- Check existing documentation examples (see "Examples of Good Documentation" in [Writing Style Guide](../writing-style.md))
- Review [CONTRIBUTING.md](../../CONTRIBUTING.md)
- Open an issue with the `documentation` label
- Ask in project discussions

---

*Templates are living documents. Contribute improvements to make ODA Canvas documentation even better!*
