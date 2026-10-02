# AGENTS.md — usecase-library/

Documentation of how ODA Components interact with the ODA Canvas. Each use case describes a specific interaction pattern with PlantUML sequence diagrams.

## Naming Convention

Files follow: `UC<NNN>-<Descriptive-Name>.md`
- Example: `UC003-Configure-Exposed-APIs.md`
- Use active verbs and avoid jargon — see `use-case-naming-conventions.md` for full guidelines
- UC numbers may have gaps (some have been deprecated to `archive/`)

## Document Structure

Each use case follows this format:

```markdown
# <Descriptive Name> use-case

Introductory paragraph explaining the use case.

## Assumptions
- Bullet list of prerequisites

## <Sub-scenario 1> (e.g., Create)
Description and sequence diagram.

![diagram-name](./pumlFiles/diagram-name.svg)
[plantUML code](pumlFiles/diagram-name.puml)

## <Sub-scenario 2> (e.g., Update)
...
```

## PlantUML Diagrams

Diagrams live in `pumlFiles/` as paired `.puml` source and `.svg` rendered files.

### Naming
- Kebab-case: `exposed-API-create.puml`, `manage-components-install.puml`
- Each `.puml` file must have a corresponding `.svg` file

### Rendering
SVGs are pre-rendered using the script at `scripts/plantuml-to-svg.js` (uses Kroki API). Run it after modifying any `.puml` file.

```bash
# Render a single diagram
node scripts/plantuml-to-svg.js usecase-library/pumlFiles/my-diagram.puml

# Render all diagrams in a directory
node scripts/plantuml-to-svg.js usecase-library/pumlFiles/
```

## Do

- Always update BOTH `.puml` and `.svg` when modifying diagrams
- Follow the naming conventions in `use-case-naming-conventions.md`
- Update `README.md` when adding or removing use cases
- Cross-reference related BDD features in `../feature-definition-and-test-kit/`
- Use PlantUML sequence diagrams for interaction patterns
- Include image references as: `![name](./pumlFiles/name.svg)`
- Include PlantUML source link: `[plantUML code](pumlFiles/name.puml)`

## Don't

- Do not add a `.puml` file without rendering the `.svg`
- Do not reference PlantUML.com proxy URLs — use local SVG files
- Do not delete use cases without moving them to `archive/`
