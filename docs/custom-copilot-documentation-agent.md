# Custom GitHub Copilot Documentation Agent

## Overview

The ODA Canvas project includes a custom GitHub Copilot agent (`@docs`) specialized in creating and improving markdown documentation and PlantUML diagrams. This agent helps maintain consistency across all project documentation while following established patterns and standards.

## Purpose

The documentation agent addresses key documentation challenges:

1. **Consistency**: Ensures all documentation follows the same writing style and structure
2. **Completeness**: Helps identify and fill documentation gaps
3. **Quality**: Maintains high-quality technical writing across all markdown files
4. **Efficiency**: Accelerates documentation creation with intelligent templates
5. **Maintenance**: Validates cross-references and keeps documentation synchronized

## Agent Capabilities

### 1. README Generation and Enhancement

The agent can create or enhance README files for:

- **Helm Charts** (`charts/*/README.md`)
  - Adds contextual sections to complement helm-docs auto-generated content
  - Links to related operators and use cases
  - Provides usage examples and troubleshooting guidance
  
- **Operators** (`source/operators/*/README.md`)
  - Creates comprehensive operator documentation
  - Generates PlantUML sequence diagrams
  - Includes development and testing instructions
  
- **Test Components** (`feature-definition-and-test-kit/testData/*/README.md`)
  - Documents TMF API implementations
  - Describes component architecture and microservices
  - Provides installation and configuration details

### 2. Use Case Documentation

Creates implementation-agnostic use case documentation following TM Forum ODA standards:

- Structured scenarios with PlantUML sequence diagrams
- Clear assumptions and prerequisites
- Links to BDD feature tests
- Alignment with ODA Component Specification

### 3. PlantUML Diagram Generation

Generates sequence diagrams with:

- Consistent actor naming (Canvas, Component, Operator, Kubernetes API)
- Auto-constructed proxy URLs for rendering
- Source `.puml` files in appropriate `pumlFiles/` directories
- Standard formatting and styling

### 4. Cross-Reference Validation

Validates and maintains documentation links:

- Bidirectional links between use cases and BDD features
- Operator-to-use-case references
- Relative path accuracy
- PlantUML diagram URL validation

### 5. Terminology Consistency

Enforces consistent terminology:

- "ODA Canvas" (not just "Canvas")
- "ODA Component" (always capitalized)
- "Software Operators" (capitalized)
- Proper use of backticks for technical elements
- British spelling ("Behaviour-Driven Development")

## How to Use the Agent

### Activation Methods

#### 1. Keyword Invocation (`@docs`)

Explicitly invoke the agent when editing any markdown file:

```
@docs Create a README for the api-gateway-operator chart
@docs Generate a use case for component dependency management
@docs Create a sequence diagram showing authentication flow
@docs Enhance this README with troubleshooting section
@docs Validate cross-references in this use case
```

#### 2. Auto-Suggestions

The agent automatically provides suggestions when you:

- Open any README file
- Create a new markdown file
- Edit use case documentation
- Work with PlantUML diagrams

### Common Use Cases

#### Creating a New Chart README

```
@docs Create a comprehensive README for charts/new-operator-chart that complements helm-docs
```

The agent will:
1. Analyze the chart structure
2. Apply the chart README template
3. Add Overview and Architecture sections
4. Link to related operators and use cases
5. Include usage examples
6. Preserve helm-docs auto-generated content

#### Generating a Use Case

```
@docs Create a use case for UC017 component auto-scaling
```

The agent will:
1. Apply the use case template
2. Follow naming conventions
3. Create placeholder sections for scenarios
4. Generate PlantUML diagram references
5. Link to related BDD features

#### Creating a Sequence Diagram

```
@docs Generate a PlantUML sequence diagram showing component installation flow
```

The agent will:
1. Create a `.puml` file in the appropriate `pumlFiles/` directory
2. Use standard Canvas actors
3. Generate the proxy URL for rendering
4. Add the source code link

#### Enhancing Existing Documentation

```
@docs Add a troubleshooting section to this README based on common issues
@docs Validate and fix all cross-references in this document
@docs Ensure this use case follows the writing style guide
```

## Agent Configuration

### Configuration File

The agent is configured in `.github/copilot-agent-docs.yml` with:

- **Activation keywords**: `@docs`
- **Auto-trigger patterns**: `**/*README.md`, `**/*.md`
- **File scope**: `**/*.md`, `**/*.puml` (limited to documentation files)
- **Knowledge base**: References to key documentation and style guides
- **Templates directory**: `docs/templates/`

### Knowledge Base

The agent has access to:

1. **Project Overview**: [.github/copilot-instructions.md](../.github/copilot-instructions.md)
2. **Writing Style Guide**: [docs/writing-style.md](writing-style.md)
3. **Use Case Conventions**: [usecase-library/use-case-naming-conventions.md](../usecase-library/use-case-naming-conventions.md)
4. **Exemplar Documentation**: README files, design documents, use cases

### Templates

Five templates guide documentation creation:

1. **Chart README Template** - [docs/templates/chart-readme-template.md](templates/chart-readme-template.md)
2. **Operator README Template** - [docs/templates/operator-readme-template.md](templates/operator-readme-template.md)
3. **Use Case Template** - [docs/templates/use-case-template.md](templates/use-case-template.md)
4. **Test Component README Template** - [docs/templates/test-component-readme-template.md](templates/test-component-readme-template.md)
5. **PlantUML Sequence Template** - [docs/templates/plantuml-sequence-template.puml](templates/plantuml-sequence-template.puml)

See [docs/templates/README.md](templates/README.md) for template usage details.

## Agent Behavior and Rules

### What the Agent Will Do

✅ **Create and edit markdown files** (`.md`)  
✅ **Generate PlantUML diagrams** (`.puml`)  
✅ **Validate cross-references** between documentation  
✅ **Suggest improvements** based on style guide  
✅ **Apply templates** consistently  
✅ **Auto-construct PlantUML proxy URLs**  
✅ **Preserve helm-docs content** between markers  
✅ **Enforce terminology standards**  

### What the Agent Will NOT Do

❌ **Edit source code files** (`.py`, `.java`, `.js`, `.ts`, etc.)  
❌ **Modify helm-docs generated content** between markers  
❌ **Change version badges** without approval  
❌ **Create standalone "Canvas"** (always "ODA Canvas")  
❌ **Use American spelling** for "Behavior" (British: "Behaviour")  
❌ **Break existing PlantUML URLs**  

### Helm-docs Preservation

For Helm chart READMEs, the agent:

- **Preserves** all content between `<!--- BEGIN PARAMS --->` and `<!--- END PARAMS --->`
- **Adds** contextual sections (Overview, Architecture, Usage, Troubleshooting)
- **Maintains** version badges and footer attribution
- **Complements** rather than replaces helm-docs

Example structure:

```markdown
# Chart Name

## Overview
[Agent-generated contextual content]

## Architecture
[Agent-generated content with links]

<!--- BEGIN PARAMS --->
[helm-docs auto-generated - PRESERVED]
<!--- END PARAMS --->

## Usage Examples
[Agent-generated examples]

## Troubleshooting
[Agent-generated troubleshooting]
```

## PlantUML Workflow

### Diagram Generation

When creating a PlantUML diagram, the agent:

1. **Creates source file** in appropriate `pumlFiles/` directory:
   - Use cases: `usecase-library/pumlFiles/`
   - Design docs: `docs/pumlFiles/`
   - Operators: `source/operators/pumlFiles/`

2. **Uses kebab-case naming**: `uc002-install-component.puml`

3. **Generates local SVG reference**:
   ```markdown
   ![diagram-name](./pumlFiles/diagram-name.svg)
   ```

4. **Adds source link**:
   ```markdown
   [plantUML code](pumlFiles/diagram-name.puml)
   ```

### Standard Actors

PlantUML diagrams use consistent actors:

- **Canvas** - ODA Canvas environment
- **Component** - ODA Component being managed
- **Operator** - Software Operator (Component, API, Identity, etc.)
- **Kubernetes API** - K8s control plane
- **Developer** - Human actor
- **API Gateway** - Istio/Kong/Apisix gateway
- **Identity Management** - Keycloak or similar

## Writing Style Guidelines

The agent follows comprehensive writing style guidelines documented in [docs/writing-style.md](writing-style.md):

### Voice and Tone
- Active voice for technical descriptions
- Imperative mood for instructions
- "We" for organizational voice, "you" for reader instructions

### Technical Terminology
- Capitalize: "ODA Canvas", "ODA Component", "Software Operators"
- Hyphenate: "cloud-native", "machine-readable", "sub-resources"
- Backticks for: Kubernetes resources, commands, file paths, versions

### Structure Patterns
- Title case for H1 document titles
- Sentence case for H2/H3 subsections
- Question format for design documents

### Code and Links
- Always use language tags for code blocks
- Inline links with relative paths for internal references
- Introductory phrases: "see [link]", "For more information..."

See the full [Writing Style Guide](writing-style.md) for detailed conventions.

## Cross-Reference Validation

The agent validates and maintains documentation links:

### Bidirectional Links

**Use Cases ↔ BDD Features**:
- Use case must reference BDD features
- BDD features must reference use case
- Tags match: `@UC002` in feature file ↔ `UC002-*.md`

**Operators → Use Cases**:
- Operator READMEs reference use case diagrams
- Use case diagrams show operators involved

### Link Validation

- **Relative paths** verified (`./ ` for same dir, `../` for parent)
- **Target files** must exist
- **PlantUML URLs** format checked
- **Branch references** appropriate (main vs. feature branch)

## Success Criteria

Documentation created or enhanced by the agent should meet:

### Completeness
- ✅ All required sections present per template
- ✅ Cross-references valid and bidirectional
- ✅ PlantUML diagrams render correctly

### Consistency
- ✅ Terminology matches glossary
- ✅ Heading hierarchy follows patterns
- ✅ Code formatting consistent

### Quality
- ✅ Writing style matches [docs/writing-style.md](writing-style.md)
- ✅ Examples are practical and tested
- ✅ Links are relative and valid

## Troubleshooting

### Agent Not Responding

**Issue**: Agent doesn't respond to `@docs` keyword

**Solutions**:
1. Ensure you're editing a markdown (`.md`) or PlantUML (`.puml`) file
2. Check GitHub Copilot is enabled for your workspace
3. Verify you have the latest Copilot extension

### Agent Suggestions Not Helpful

**Issue**: Agent provides generic suggestions instead of Canvas-specific content

**Solutions**:
1. Provide more context in your prompt: "@docs Create a README for the component-operator chart in the ODA Canvas"
2. Reference specific templates: "@docs Use the operator README template"
3. Include use case or operator names for better context

### PlantUML Diagrams Not Rendering

**Issue**: PlantUML proxy URL shows error

**Solutions**:
1. Verify the `.puml` file exists in the correct `pumlFiles/` directory
2. Check the GitHub branch reference in the URL (main vs. feature branch)
3. Ensure PlantUML syntax is valid (test at plantuml.com)

### helm-docs Content Modified

**Issue**: Agent accidentally edited helm-docs generated content

**Solutions**:
1. Verify markers are present: `<!--- BEGIN PARAMS --->` and `<!--- END PARAMS --->`
2. Regenerate helm-docs content: `helm-docs -c charts/{chart-name}`
3. Report issue if agent bypassed markers

## Best Practices

### For Contributors

1. **Always use `@docs` for new documentation** - Ensures consistency from the start
2. **Review agent suggestions** - Agent is helpful but verify accuracy
3. **Follow templates** - Templates ensure nothing is missed
4. **Validate links** - Check that cross-references work
5. **Test PlantUML diagrams** - Verify diagrams render before committing

### For Reviewers

1. **Check template adherence** - Ensure all required sections present
2. **Verify terminology** - "ODA Canvas", "ODA Component" capitalized
3. **Validate cross-references** - Links should be bidirectional where appropriate
4. **Test examples** - Code examples should be accurate and tested
5. **Review PlantUML diagrams** - Diagrams should render and be accurate

## Future Enhancements

Potential improvements to the documentation agent:

### Planned Features

- **Automated link checking** - CI/CD integration to validate all links
- **Diagram validation** - Pre-commit hooks to check PlantUML syntax
- **Template versioning** - Track template evolution over time
- **Documentation metrics** - Measure completeness and consistency
- **Multi-language support** - Templates for API specifications

### Feedback and Contributions

To improve the documentation agent:

1. **Report issues** - Create GitHub issue with `documentation` label
2. **Suggest improvements** - Propose template enhancements
3. **Share patterns** - Contribute exemplar documentation
4. **Update style guide** - Submit PRs to [docs/writing-style.md](writing-style.md)

## Related Documentation

- **Writing Style Guide**: [docs/writing-style.md](writing-style.md)
- **Templates Directory**: [docs/templates/](templates/)
- **GitHub Copilot Instructions**: [.github/copilot-instructions.md](../.github/copilot-instructions.md)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Use Case Naming Conventions**: [usecase-library/use-case-naming-conventions.md](../usecase-library/use-case-naming-conventions.md)

## References

- [GitHub Copilot Custom Agents Documentation](https://docs.github.com/en/copilot/customizing-copilot/custom-agents)
- [PlantUML Documentation](https://plantuml.com/)
- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [TM Forum ODA Specification](https://www.tmforum.org/oda/)

---

*This documentation agent is designed to maintain high-quality, consistent documentation across the ODA Canvas project. For questions or suggestions, see [CONTRIBUTING.md](../CONTRIBUTING.md).*
