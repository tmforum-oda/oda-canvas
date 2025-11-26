# ODA Canvas Documentation Writing Style Guide

This guide captures the writing style conventions used across ODA Canvas documentation. Following these patterns ensures consistency and maintainability across all markdown files, use cases, and technical documentation.

## Voice and Tone

### Active Voice
Use active, declarative voice for technical descriptions:

✅ **Good**: "The ODA Canvas **is** an execution environment for ODA Components."  
✅ **Good**: "The Canvas **reads** the Component requirements from the specification."  
❌ **Avoid**: "Component requirements are read by the Canvas from the specification."

### Imperative Mood for Instructions
Use direct commands when providing instructions:

✅ **Good**: "Run the following command to install..."  
✅ **Good**: "See [Installation Guide] for details."  
✅ **Good**: "Refer to [Canvas Design] for architecture overview."  
❌ **Avoid**: "You should run the command..." or "The command can be run..."

### Perspective and Pronouns
- Use **"we"** for organizational voice (TM Forum team perspective)
  - "We expect a typical production implementation will use..."
  - "We foresee additional operators in the future..."
- Use **"you"** for direct reader instructions
  - "You can install the Canvas using Helm..."
  - "You should see the ExposedAPI resources created..."
- Use **third-person** for describing system components
  - "The operator manages the component lifecycle..."
  - "Kubernetes reconciles the desired state..."

### Tone Characteristics
- **Formal but accessible**: Professional technical writing without being overly academic
- **Conversational but precise**: Avoid colloquialisms while maintaining readability
- **Inclusive and welcoming**: Especially in community documents (CONTRIBUTING.md, code-of-conduct.md)
- **Question-driven engagement**: Use questions as section headers in design documents and community guides

## Sentence Structure

### Length Variation
Vary sentence length for readability and emphasis:

- **Short declarative** for key points:
  - "Software Operators are a key concept in the ODA Canvas."
  
- **Medium explanatory** for context:
  - "The ODA Canvas is an execution environment for ODA Components and the release automation part of a CI/CD pipeline."
  
- **Long complex** for detailed technical context:
  - "The ODA Canvas is itself a modular architecture, with independent **operators** that embed the management and operations activities in software."

### Semicolons for Related Ideas
Use semicolons to connect closely related concepts:

✅ **Good**: "The ODA Components are **not** given raised privileges to expose their APIs directly; Instead, the API Management operator in the Canvas reads the requirements and configures the API Gateway or Service Mesh."

### List-Heavy Documentation
Prefer bulleted or numbered lists for:
- Assumptions and prerequisites
- Step-by-step procedures
- Feature enumerations
- Configuration options
- Multiple related points

## Heading Hierarchy and Capitalization

### H1 (Document Titles)
Use **Title Case** for main document titles:
- `# Open Digital Architecture Canvas`
- `# Manage Components Use Case`
- `# Component Management Operator`

### H2 (Major Sections)
Use **Sentence case** for subsections:
- `## What is the ODA Canvas?`
- `## Install component`
- `## Upgrade component`
- `## Interactive development and Testing`

### H3 (Subsections)
Use **Sentence case**:
- `## Secrets Management Initialization and Usage`
- `### Prerequisites`
- `### Configuration options`

### Question Format
Use questions as headers in design documents and explanatory content:
- `## What is the ODA Canvas?`
- `## How do I buy or build a Canvas?`
- `## Why are these principles important?`

### Use Case Naming Convention
Follow the pattern: `# {Verb} {Object} use case` or `# {Descriptive phrase} use-case`

✅ **Good**:
- `# Manage Components use case`
- `# Configure Exposed APIs use case`
- `# Secrets Management for Component use-case`

See [usecase-library/use-case-naming-conventions.md](../usecase-library/use-case-naming-conventions.md) for detailed conventions.

## Technical Terminology

### Always Capitalize
These terms are consistently capitalized throughout the documentation:

- **ODA Canvas** (never just "Canvas" alone in technical docs)
- **ODA Component** (capitalize both words)
- **Software Operators** (capital S, capital O)
- **Component Management**
- **API Management**
- **Identity Management**
- **Kubernetes Operator Pattern**
- **Behaviour-Driven Development (BDD)** (British spelling)

### Bold Emphasis on First Use
Bold key technical terms when introduced:

✅ **Good**: "The ODA Canvas is itself a modular architecture, with independent **operators** that embed the management and operations activities in software."

✅ **Good**: "Each component describes its **coreFunction**, **security** and **management** requirements."

✅ **Good**: "Components are **not** given raised privileges..." (emphasize negation)

### Inline Code for Technical Elements

Use backticks for:

**Kubernetes Resources and CRDs:**
- `Component`
- `ExposedAPI`
- `DependentAPI`
- `IdentityConfig`
- `Deployment`
- `Service`
- `ConfigMap`

**Commands and Tools:**
- `kubectl`
- `helm`
- `kopf`
- `docker`

**File Paths:**
- `README.md`
- `values.yaml`
- `$HOME/.kube/config`
- `source/operators/`

**Configuration Values:**
- `--standalone`
- `--namespace=components`
- `replicas: 3`

**Version Identifiers:**
- `v1`
- `v1beta3`
- `v1beta4`
- `v1alpha4`

**API Endpoints:**
- `info.canvas.svc.cluster.local`

### Hyphenated Terms
Always hyphenate these compound terms:
- cloud-native
- machine-readable
- de-composition
- sub-resources
- use-case (when used as compound adjective: "use-case naming conventions")

### Acronyms
- **BDD**: Always use acronym after first mention, not "Behavior-Driven Development"
- **API**: No need to spell out in technical documentation
- **TMF**: TM Forum standards (e.g., TMF620, TMF669, TMF671) - no backticks in prose
- **CRD**: Custom Resource Definition
- **K8s**: Acceptable shorthand for Kubernetes in informal contexts

## Code Block Formatting

### Always Use Language Tags

````markdown
```bash
kubectl auth can-i create namespaces
```

```yaml
apiVersion: oda.tmforum.org/v1beta3
kind: component
metadata:
  name: productcatalog
```

```json
{
  "aud": ["https://kubernetes.default.svc.cluster.local"],
  "exp": 1735689600
}
```

```python
@kopf.on.create('oda.tmforum.org', 'v1beta3', 'components')
def create_fn(spec, **kwargs):
    pass
```
````

### Nested Markdown Examples
Use four backticks when showing markdown within markdown:

`````markdown
````markdown
```bash
echo "nested example"
```
````
`````

### Include Explanatory Comments

```bash
# Set log level (can be set to DEBUG)
export LOG_LEVEL=INFO

# Run the operator in standalone mode
kopf run --namespace=components --standalone ./componentOperator.py
```

## Link Formatting

### Inline Links (Preferred)
Use inline links with descriptive text:

```markdown
[Canvas use case library](usecase-library/README.md)
[Software Operators](source/operators/README.md)
[Install Canvas](./UC001-Install-Canvas.md)
```

### Relative Paths for Internal Links
- Same directory: `[file](./UC001-Install-Canvas.md)`
- Parent directory: `[file](../usecase-library/README.md)`
- Nested path: `[file](../../source/operators/README.md)`
- Always use forward slashes (even on Windows)

### External Links
Use full URLs for external resources:

```markdown
[What is an Operator?](https://operatorhub.io/what-is-an-operator)
[TMF IG1306](https://www.tmforum.org/resources/standard/ig1306-...)
[Kubernetes Documentation](https://kubernetes.io/docs/)
```

### Introductory Phrases for Links
Prefer natural introductory phrases:

✅ **Good**: "see [Installation Guide](installation/README.md)"  
✅ **Good**: "For more information see [Software Operators](source/operators/README.md)"  
✅ **Good**: "Refer to [Which OAuth2 flow should I use](https://auth0.com/docs/...)"  
✅ **Good**: "For details about how to contribute, see [CONTRIBUTING.md](CONTRIBUTING.md)"

❌ **Avoid**: Bare links without context

## List Formatting

### Bullet Points
Use dash (`-`) for unordered lists:

```markdown
- First item
- Second item
  - Nested item with 2-space indent
  - Another nested item
- Third item
```

### Numbered Lists
Use numbered lists for sequential steps or ordered items:

```markdown
1. Install prerequisites
2. Configure the environment
3. Deploy the Canvas
4. Verify installation
```

### List Item Structure

**Bold term followed by description:**
```markdown
- **Feature**: Description of the feature
- **Operator**: Software that manages resources
- **Component**: An ODA-compliant software package
```

**Colon separation for structured lists:**
```markdown
- UC001: [Install Canvas](UC001-Install-Canvas.md) - Install the Canvas into a Kubernetes cluster
- UC002: [Manage Components](UC002-Manage-Components.md) - Install, upgrade and delete components
```

### Nested Lists
Use consistent 2-space indentation:

```markdown
- Main point
  - Sub-point
    - Further nested point
  - Another sub-point
- Next main point
```

## Table Formatting

### Alignment Patterns

```markdown
| Left-aligned | Center-aligned | Right-aligned |
| ------------ | :------------: | ------------: |
| Content      | Content        | Content       |
```

### Common Table Types

**Version Compatibility Matrix:**
```markdown
| Software | Version | Tested | Notes |
| -------- | ------- | ------ | ----- |
| Kubernetes | 1.20-1.28 | ✅ | All versions |
| Helm | 3.x | ✅ | Required |
```

**Operator Inventory:**
```markdown
| Operator | Purpose | Status |
| -------- | ------- | ------ |
| Component Management | Lifecycle management | Implemented |
| API Management | Gateway configuration | Implemented |
```

**BDD Feature Table:**
```markdown
| **Feature** | **Given** | **When** | **Then** | **Outcome** |
| ----------- | --------- | -------- | -------- | ----------- |
| Install Component | Package available | Install command | Resources created | ✅ Pass |
```

### Header Capitalization
- Sentence case preferred: "Software version", "Tested", "Notes"
- Bold for emphasis in BDD tables: **Feature**, **Action**, **Outcome**

## Emphasis and Formatting

### Bold (`**text**`)
Use bold for:
- Key concepts on first introduction: "**operators**", "**coreFunction**"
- Emphasis on negation: "**not** given raised privileges"
- Term definitions: "**Component Management**: Manages the lifecycle..."
- Table headers in text: "**Feature**, **Given**, **When**, **Then**"

### Italic (`*text*`)
Rarely used. Mainly for:
- References in notes: "*Refer to [link] for details*"
- Emphasis in quotes

### Code Backticks
See "Inline Code for Technical Elements" section above.

### Avoid Over-Formatting
❌ **Don't combine**: `**bold and code**` or ***bold and italic***  
✅ **Choose one**: Either `code` OR **bold**, not both

## Diagram Integration

### PlantUML Sequence Diagrams

**Standard Pattern:**
```markdown
![install-component-sequence](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/installComponent.puml)

[plantUML code](pumlFiles/installComponent.puml)
```

**Key Elements:**
- Alt text uses kebab-case: `install-component-sequence`, `manage-components-upgrade`
- Proxy URL format: `http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/...`
- Followed by link to source `.puml` file with relative path
- Place after section header, before explanatory text

### Embedded Videos

**YouTube Thumbnail Link:**
```markdown
[![Introduction to ODA Canvas](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://youtu.be/VIDEO_ID)
```

## Documentation Structure Patterns

### Use Case Structure
```markdown
# {Verb} {Object} use case

[Overview paragraph with scope]

Uses assumptions:
- Assumption 1
- Assumption 2
- Assumption 3

## {Scenario name}

![diagram-name](plantuml-proxy-url)

[plantUML code](pumlFiles/diagram.puml)

[Explanatory text for scenario]

## {Another scenario}

[Repeat pattern]

## Error scenarios

[Description of error handling and status states]

[Link to BDD features]
```

### Operator README Structure
```markdown
# {Operator Name}

[Purpose and overview paragraph]

## Sequence Diagram

![sequence-diagram](plantuml-proxy-url)

[plantUML code](pumlFiles/diagram.puml)

## Reference Implementation

The reference implementation is written in [Python/Java/etc.] using [KOPF/Spring Boot/etc.]...

## Interactive development and Testing

Run locally:
```bash
kopf run --namespace=components --standalone ./componentOperator.py
```

## Build automation

[Build and CI/CD information]
```

### Chart README Structure (with helm-docs)
```markdown
# {Chart Name}

## Overview

[Contextual description of what this chart provides and its role in the ODA Canvas]

## Architecture

[How this chart fits into the Canvas architecture, links to operators and use cases]

<!--- BEGIN PARAMS --->
[helm-docs auto-generated content - DO NOT EDIT]
<!--- END PARAMS --->

## Usage Examples

Install the chart:
```bash
helm install my-release ./chart-name -n namespace
```

## Troubleshooting

### Common Issue 1
[Description and solution]

### Common Issue 2
[Description and solution]

## Related Documentation

- [Related Operator](../source/operators/operator-name/)
- [Use Case UC00X](../usecase-library/UC00X-name.md)
- [Installation Guide](../installation/README.md)
```

### Test Component README Structure
```markdown
# {Component Name}

TM Forum {TMF API Name} component implementing TMF{number} {API Name}.

In its **core function** it implements:
* The *mandatory* TMF{number} {API Name} Open API
* The *optional* TMF{number} {API Name} Open API

In its **management function** it implements:
* Optional metrics API (Open Metrics standard)
* Outbound Open Telemetry events

In its **security function** it implements:
* The *mandatory* TMF669 Party Role Management Open API

The implementation consists of {N} microservices:
- **{Service Name}**: {Purpose}
- **{Service Name}**: {Purpose}

## Installation

```bash
helm install r1 ./component-name -n components
```

## Configuration

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `var.name` | Description | `value` |
```

## Cross-Reference Patterns

### Hierarchical Documentation Flow
```
Canvas-design.md (Overview)
    ↓
Design Epics (Authentication-design.md, etc.)
    ↓
Use Case Library (UC001-UC016)
    ↓ (linked via @tags)
BDD Features (UC00X-F00Y-*.feature)
    ↓ (tested against)
Operators & Charts (source/, charts/)
    ↓ (deployed via)
Installation Guide
```

### Bidirectional Links
- Use cases should link to BDD features
- BDD features should reference use cases in comments
- Operator READMEs should reference use case sequence diagrams
- Use case diagrams should show operators involved

### Explicit Cross-References
```markdown
described in use case [UC003](UC003-Configure-Exposed-APIs.md)
see [Software Operators](source/operators/README.md)
For more information see [Canvas Design](Canvas-design.md)
The sequence diagram is shown in [UC002-F001](../feature-definition-and-test-kit/features/UC002-F001-Install-Component.feature)
```

## Spacing and Formatting

### Blank Lines
- One blank line before headings
- One blank line after headings
- One blank line before code blocks
- One blank line after code blocks
- One blank line between list items with sub-items
- No blank line between simple list items

### Indentation
- Use **2 spaces** for nested lists
- Use **4 spaces** or **tabs** for code indentation (language-dependent)
- Consistent indentation within same file

## Common Vocabulary and Phrases

### Recurring Technical Terms
- "execution environment"
- "lifecycle management" or "lifecycle processes"
- "machine-readable specification"
- "reference implementation"
- "sequence diagram"
- "use case"

### Action Verbs
- Configure, manage, expose, integrate, deploy, bootstrap, discover
- Install, upgrade, uninstall, delete
- Read, write, create, update
- Validate, verify, test

### Qualifying Phrases
- "at present" (current state)
- "in the near future" (planned features)
- "We expect that..." (anticipated usage)
- "We foresee..." (future direction)
- Modal verbs: "should", "will", "can", "may"

## Notes and Admonitions

### Note Format
Use bold **Note** inline:

```markdown
**Note**: This use case is separate from the main installation process.
```

### Prerequisites Format
```markdown
**Prerequisites**:
- A running Kubernetes distribution (version 1.20 or higher)
- Helm 3.x installed
- kubectl configured with cluster admin access
```

Or as section:
```markdown
## Prerequisites

- Item 1
- Item 2
```

## Writing for Different Audiences

### Use Cases (Business + Technical)
- **Audience**: Product managers, architects, developers
- **Tone**: Clear, scenario-driven, implementation-agnostic
- **Structure**: Assumptions → Scenarios → Diagrams
- **Language**: Business terminology with technical precision

### Operator READMEs (Developers)
- **Audience**: Developers implementing or extending operators
- **Tone**: Technical, practical, command-focused
- **Structure**: Purpose → Architecture → Development → Build
- **Language**: Technical terminology, framework-specific details

### Installation Guides (Operators/SREs)
- **Audience**: Operations teams deploying Canvas
- **Tone**: Procedural, step-by-step, troubleshooting-focused
- **Structure**: Prerequisites → Installation → Verification → Troubleshooting
- **Language**: Command examples, version matrices, platform-specific notes

### Design Documents (Architects)
- **Audience**: Technical architects, standards bodies
- **Tone**: Explanatory, principle-driven, rationale-focused
- **Structure**: What → Why → How → Design Decisions
- **Language**: Architectural patterns, design principles, trade-offs

### Contributing Guides (Community)
- **Audience**: Open source contributors
- **Tone**: Welcoming, question-driven, supportive
- **Structure**: Questions → Answers → Process → Links
- **Language**: Inclusive, encouraging, clear expectations

## Version References

### In Code/Technical Context
Use backticks:
- `v1`
- `v1beta3`
- `v1beta4`
- `v1alpha4`

### In Tables
Plain text acceptable:
- v1beta3
- 1.20-1.28
- 3.x

### Version Ranges
- "1.20 or higher"
- "Kubernetes 1.20-1.28"
- "Helm 3.x"
- "Support for N, N-1, N-2 versions" (explaining version support policy)

## Examples of Good Documentation

Reference these files as exemplars:

- **Main README**: [README.md](../README.md) - Comprehensive overview with badges, clear structure
- **Operators Overview**: [source/operators/README.md](../source/operators/README.md) - Best operator type overview
- **Component Operator**: [source/operators/componentOperator/README.md](../source/operators/componentOperator/README.md) - Complete operator documentation
- **BDD README**: [feature-definition-and-test-kit/README.md](../feature-definition-and-test-kit/README.md) - Excellent BDD explanation
- **Use Case Example**: [usecase-library/UC002-Manage-Components.md](../usecase-library/UC002-Manage-Components.md) - Well-structured use case
- **Security Principles**: [SecurityPrinciples.md](../SecurityPrinciples.md) - Principle-based documentation
- **Installation Guide**: [installation/README.md](../installation/README.md) - Comprehensive installation documentation

## Checklist for Documentation Review

Before finalizing documentation, verify:

- [ ] All required sections present (per template)
- [ ] Headings follow capitalization rules
- [ ] Technical terms use proper capitalization and backticks
- [ ] "ODA Canvas" and "ODA Component" always capitalized
- [ ] Code blocks have language tags
- [ ] Links use relative paths for internal references
- [ ] PlantUML diagrams include proxy URL and source link
- [ ] Cross-references are bidirectional where appropriate
- [ ] Lists use consistent formatting (dash bullets, 2-space indent)
- [ ] Tables are properly aligned
- [ ] No spelling errors (British: "Behaviour", American: "Organization")
- [ ] Voice is active and appropriate for audience
- [ ] Examples are practical and tested
- [ ] Blank lines for proper spacing
- [ ] helm-docs content not manually edited (charts only)

---

*This style guide is a living document. As documentation patterns evolve, update this guide to reflect current best practices. For questions or suggestions, see [CONTRIBUTING.md](../CONTRIBUTING.md).*
