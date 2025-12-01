# ODA Canvas Documentation

This directory contains documentation resources, templates, and guides for contributors and developers working on the ODA Canvas project.

## Contents

### Documentation Guides

- **[Writing Style Guide](writing-style.md)** - Comprehensive guide to writing style conventions for all markdown documentation
- **[Custom Copilot Agent](custom-copilot-documentation-agent.md)** - Guide to using the `@docs` AI agent for documentation creation and enhancement

### Templates

The [templates/](templates/) directory contains standardized templates for creating consistent documentation:

- **Chart README Template** - For Helm charts in `charts/` directory
- **Operator README Template** - For operators in `source/operators/` directory
- **Use Case Template** - For use cases in `usecase-library/` directory
- **Test Component README Template** - For test components in `feature-definition-and-test-kit/testData/`
- **PlantUML Sequence Template** - For sequence diagrams

See [templates/README.md](templates/README.md) for detailed usage instructions.

### Developer Documentation

The [developer/](developer/) directory contains technical guides for developers:

- How-to guides for common development tasks
- Architecture decision records
- Development workflows and best practices

### PlantUML Diagrams

The [pumlFiles/](pumlFiles/) directory stores PlantUML source files for design documentation diagrams. For use case diagrams, see [usecase-library/pumlFiles/](../usecase-library/pumlFiles/).

## Quick Start

### For Contributors

#### Writing New Documentation

1. **Invoke the documentation agent** with `@docs` keyword:
   ```
   @docs Create a README for the new-operator
   ```

2. **Or use templates manually**:
   - Browse [templates/](templates/) directory
   - Copy relevant template
   - Fill in placeholders
   - Follow [Writing Style Guide](writing-style.md)

3. **Validate documentation**:
   - Check all cross-references work
   - Verify terminology follows standards
   - Test code examples
   - Ensure PlantUML diagrams render

#### Improving Existing Documentation

1. **Open the markdown file** - Agent auto-suggests improvements
2. **Or invoke explicitly**:
   ```
   @docs Add troubleshooting section to this README
   @docs Validate cross-references in this document
   ```

### For Reviewers

When reviewing documentation PRs, verify:

- ✅ Template structure followed (if applicable)
- ✅ Writing style matches [writing-style.md](writing-style.md)
- ✅ Terminology consistent ("ODA Canvas", "ODA Component" capitalized)
- ✅ Cross-references valid and bidirectional
- ✅ Code examples tested and accurate
- ✅ PlantUML diagrams render correctly
- ✅ helm-docs content not manually edited (for charts)

## Documentation Structure

### Project-Wide Documentation Layers

The ODA Canvas documentation follows a hierarchical structure:

```
Level 1: Strategic Documentation
├── Canvas-design.md
├── SecurityPrinciples.md
├── Authentication-design.md
├── Event-based-integration-design.md
└── Observability-design.md

Level 2: Use Cases (Implementation-Agnostic)
└── usecase-library/UC*.md

Level 3: BDD Features (Executable Specifications)
└── feature-definition-and-test-kit/features/UC*.feature

Level 4: Implementation Documentation
├── source/operators/*/README.md
├── charts/*/README.md
└── feature-definition-and-test-kit/testData/*/README.md

Level 5: Operational Documentation
├── installation/README.md
└── docs/developer/*.md
```

### Cross-Reference Patterns

Documentation should maintain bidirectional links:

- **Use Cases ↔ BDD Features** - Use case references features; features reference use case
- **Operators → Use Cases** - Operator READMEs reference use case diagrams
- **Charts → Operators** - Chart READMEs link to operator implementations
- **Design Docs → Use Cases** - Design epics reference implementing use cases

## Writing Style

See the complete [Writing Style Guide](writing-style.md) for detailed conventions.

## PlantUML Diagrams

### Creating Diagrams

Use the `@docs` agent to generate diagrams:

```
@docs Create a sequence diagram showing component installation flow
```

Or manually:

1. Copy [templates/plantuml-sequence-template.puml](templates/plantuml-sequence-template.puml)
2. Customize actors and sequence
3. Save in appropriate `pumlFiles/` directory:
   - Use cases: `usecase-library/pumlFiles/`
   - Design docs: `docs/pumlFiles/`
   - Operators: `source/operators/pumlFiles/`

### Embedding Diagrams

Use the PlantUML proxy URL pattern:

```markdown
![diagram-name](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/path/to/diagram.puml)

[plantUML code](pumlFiles/diagram-name.puml)
```

### Standard Actors

Use consistent actor names:
- Canvas
- Component
- Operator
- Kubernetes API
- Developer
- API Gateway
- Identity Management

## Custom Copilot Agent

The `@docs` agent assists with documentation creation and maintenance:

### Capabilities

- ✅ Generate README files from templates
- ✅ Create use case documentation
- ✅ Generate PlantUML sequence diagrams
- ✅ Validate cross-references
- ✅ Enforce terminology standards
- ✅ Suggest improvements based on style guide
- ✅ Complement helm-docs for charts

### Limitations

- ❌ Cannot edit source code files
- ❌ Cannot modify helm-docs generated content
- ❌ Limited to markdown and PlantUML files

See [Custom Copilot Agent Guide](custom-copilot-agent.md) for detailed usage.

## Contributing to Documentation

### Documentation Improvements

To improve documentation:

1. **Identify the issue** - Missing section, unclear explanation, broken links
2. **Check templates** - Does a template exist? Should it be updated?
3. **Use the `@docs` agent** - Let it help with consistency
4. **Follow style guide** - Maintain writing conventions
5. **Validate changes** - Test links and examples
6. **Submit PR** - With clear description of improvements

### Template Evolution

To propose template changes:

1. **Create an issue** - Describe proposed improvement
2. **Provide rationale** - Why is this change needed?
3. **Show examples** - Reference existing good documentation
4. **Update template** - Make changes in `docs/templates/`
5. **Update style guide** - If patterns change, update [writing-style.md](writing-style.md)

### Style Guide Updates

To update the writing style guide:

1. **Analyze patterns** - Review multiple markdown files
2. **Identify inconsistencies** - What needs standardization?
3. **Propose convention** - Suggest best practice
4. **Provide examples** - Show good vs. avoid patterns
5. **Submit PR** - Update [writing-style.md](writing-style.md)

## Documentation Quality

### Quality Checklist

Before finalizing documentation, verify:

- [ ] All required sections present (per template if applicable)
- [ ] Headings follow capitalization rules
- [ ] Technical terms properly capitalized and formatted
- [ ] Code blocks have language tags
- [ ] Links use relative paths for internal references
- [ ] PlantUML diagrams render correctly
- [ ] Cross-references are bidirectional where appropriate
- [ ] Lists use consistent formatting
- [ ] Tables are properly aligned
- [ ] No spelling errors
- [ ] Examples are tested and accurate
- [ ] helm-docs content not manually edited (charts only)

### Automated Validation

Future enhancements may include:

- CI/CD link validation
- PlantUML syntax checking
- Terminology linting
- Template compliance verification

## Resources

### Internal Resources

- **Main README**: [README.md](../README.md)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Code of Conduct**: [code-of-conduct.md](../code-of-conduct.md)
- **GitHub Copilot Instructions**: [.github/copilot-instructions.md](../.github/copilot-instructions.md)
- **Use Case Naming Conventions**: [usecase-library/use-case-naming-conventions.md](../usecase-library/use-case-naming-conventions.md)

### External Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [PlantUML Documentation](https://plantuml.com/)
- [Markdown Guide](https://www.markdownguide.org/)
- [TM Forum ODA](https://www.tmforum.org/oda/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Questions or Help

If you need assistance with documentation:

1. **Check existing examples** - Look at exemplar documentation listed in [writing-style.md](writing-style.md)
2. **Use the `@docs` agent** - Invoke with your question
3. **Review templates** - See [templates/README.md](templates/README.md)
4. **Ask in discussions** - Open a GitHub discussion
5. **Create an issue** - Use the `documentation` label

---

*This documentation infrastructure helps maintain high-quality, consistent documentation across the ODA Canvas project. Contribute improvements to make it even better!*
