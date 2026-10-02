# AGENTS.md

Instructions for AI coding agents working in the ODA Canvas repository.

## Project Overview

The TM Forum Open Digital Architecture (ODA) Canvas is an execution environment for ODA Components that follows the Kubernetes Operator Pattern. This repository contains the Reference Implementation, open-source code, use cases, and test kit for an ODA Canvas implementation.

## Key Concepts and Terminology

- **ODA Canvas**: An execution environment that supports ODA Components by providing access to cloud-native services required by the components (API Gateway, Service Mesh, Observability services, Identity Management, etc.).
- **ODA Component**: Software components that follow the ODA Component Specification, which the Canvas reads as metadata to execute lifecycle processes.
- **Operators**: Management-plane functions that manage ODA Components by reading the Component's requirements and executing lifecycle processes. Operators follow the Kubernetes Operator Pattern.
- **Webhooks**: Used to integrate with the Kubernetes Control Plane, supporting multiple versions of the ODA Component Standard.
- **BDD (Behaviour-Driven Development)**: The approach used to document and test Canvas behaviors through features and scenarios.

## Modular Architecture

The ODA Canvas implements a modular architecture with independent operators:

- **Component Management**: Manages the lifecycle of each component and handles decomposition into ExposedAPIs, IdentityConfigs, and other sub-resources.
- **API Management**: Manages API Gateway and/or Service Mesh to provide security, throttling, and other non-functional services.
- **Identity Config**: Configures Identity Management Services.
- **Secrets Management**: Optional operator for configuring secrets.
- **Dependency Management**: Allows Components to discover API dependencies.

## Do

- Use the Kubernetes Operator Pattern with kopf for Python operators
- Follow the v1 CRD schema for component specifications
- Write BDD features that are implementation-agnostic
- Use PlantUML for sequence diagrams in use cases
- Default to small, focused diffs
- Follow BDD approach: create use cases first, then BDD scenarios, then implementation
- Support N-2 versions of ODA Component Standard (currently v1, v1beta4, v1beta3)
- Include comprehensive docstrings in source code
- Follow existing code conventions and patterns in each language
- Create tests for all new functionality
- Follow the code-of-conduct and contribution guidelines in CONTRIBUTING.md
- Document design decisions in the Architecture Decision Log
- Use GitHub issues for tracking work

## Don't

- Do not hard-code namespace references; use Helm template variables
- Do not add new CRD fields without updating the webhook conversion logic
- Do not write BDD steps that reference specific operator implementations
- Do not modify CRD schemas without considering backward compatibility across N-2 versions

## Development Commands

### BDD Tests (Feature Definition and Test Kit)
```bash
cd feature-definition-and-test-kit
npm install
npm start                    # Run BDD tests and publish results
npm run start:tags          # Run BDD tests with specific tags
```

### Canvas Portal (Vue.js Frontend)
```bash
cd canvas-portal/portal-web
npm install
npm run dev                  # Development server
npm run build               # Production build
npm run lint                # Lint code
npm run format              # Format code with Prettier
```

### Java Components (Spring Boot)
```bash
cd canvas-portal
mvn clean install          # Build all Java modules
mvn spring-boot:run         # Run Spring Boot applications
```

### Python Operators (KOPF Framework)
```bash
cd source/operators
pip install -r requirements.txt     # Install Python dependencies
python componentOperator.py         # Run component operator
```

### TMF Services

#### Node.js Services (TMF639 Resource Inventory)
```bash
cd source/tmf-services/TMF639_Resource_Inventory
npm install
npm start                   # Start TMF639 service
```

#### Python Services (MCP Resource Inventory)
```bash
cd source/tmf-services/MCP_Resource_Inventory
# Using UV package manager
uv install                  # Install dependencies
uv run pytest              # Run tests
uv run python resource_inventory_mcp_server.py  # Start server

# Alternative with pip
pip install -e .
pytest                      # Run tests
python -m resource_inventory_mcp_server  # Start server
```

### Kubernetes Commands
```bash
# Check Canvas version
kubectl get crd components.oda.tmforum.org -o jsonpath='{.spec.versions[?(@.served==true)].name}'

# Deploy Canvas using Helm
helm install oda-canvas charts/canvas-oda

# View components
kubectl get components
kubectl get exposedapis
```

### Helm Chart Validation
```bash
helm lint charts/canvas-oda
```

### Component YAML Validation
```bash
kubectl apply --dry-run=client -f path/to/component.yaml
```

## Project Structure

- `charts/`: Helm charts for deploying Canvas components
- `canvas-portal/`: Spring Boot + Vue.js web portal for Canvas management
- `docs/`: Additional documentation for developers
- `feature-definition-and-test-kit/`: BDD tests and utilities for Canvas validation
- `installation/`: Installation guides and deployment scripts
- `source/`: Core Canvas implementation
  - `operators/`: Kubernetes operators (Component, API, Identity, Secrets Management)
  - `webhooks/`: Kubernetes admission webhooks
  - `utilities/`: Development and troubleshooting tools
  - `tmf-services/`: TMF API implementations
- `usecase-library/`: Use cases documenting component-canvas interactions

## Technology Stack

- **Backend**: Python (KOPF framework), Java (Spring Boot), Node.js
- **Frontend**: Vue.js 3, Element Plus UI, Vite
- **Container**: Docker, Kubernetes
- **Deployment**: Helm charts
- **Testing**: Cucumber.js (BDD), JUnit (Java), pytest (Python)
- **Package Management**: Maven (Java), npm (Node.js), uv/pip (Python)

## Testing

### BDD Feature Tests
Run the comprehensive test suite that validates Canvas compliance:
```bash
cd feature-definition-and-test-kit
npm start
```

BDD features and scenarios are used to create executable tests. The test kit validates Canvas implementations. Components are tested against the standard ODA Component Specification. Tests are automated to ensure compliance with security principles.

### Unit Tests
- Python: `pytest` in operator directories
- Java: `mvn test` in Java modules
- Node.js: `npm test` in service directories

## Component Specification Versions

The Canvas supports multiple versions of the ODA Component Standard:
- **v1**: Current stable version
- **v1beta4**: Previous version, still supported
- **v1beta3**: Oldest supported version (deprecation warnings may apply)

Always check version compatibility when working with CRDs and webhook conversions.

## Important Files and Documentation

- `Canvas-design.md`: Overall Canvas design documentation
- `README.md`: Main project introduction
- `SecurityPrinciples.md`: Security principles and guidelines
- `Authentication-design.md`: Authentication design patterns
- `Event-based-integration-design.md`: Event-based integration design
- `Observability-design.md`: Observability design patterns
- `charts/canvas-oda/values.yaml`: Main Canvas configuration
- `source/operators/requirements.txt`: Python operator dependencies
- `CONTRIBUTING.md`: Contribution guidelines and code of conduct

## Safety and Permissions

### Allowed without prompt
- Read files, list directories, search codebase
- Run lint, dry-run validation, helm lint
- Run individual BDD scenarios
- Run unit tests (pytest, mvn test, npm test)

### Ask first
- Modifying CRD schemas
- Changing Helm chart default values
- Adding new dependencies to requirements.txt, package.json, or pom.xml
- Pushing to any branch
- Deleting files

## Good and Bad Examples

- Preferred operator pattern: see `source/operators/componentOperator/`
- Preferred BDD style: see feature files following TAC-353 style guide in `feature-definition-and-test-kit/features/`
- Preferred use case format: see `usecase-library/UC003-Configure-Exposed-APIs.md`
- Preferred Helm chart structure: see `charts/canvas-oda/`
