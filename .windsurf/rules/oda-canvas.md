---
trigger: always_on
---

# Windsurf Rules for TM Forum ODA Canvas

## Project Overview

The TM Forum Open Digital Architecture (ODA) Canvas is an execution environment for ODA Components that follows the Kubernetes Operator Pattern. This repository contains the Reference Implementation, open-source code, use cases, and test kit for an ODA Canvas implementation.

## Key Concepts

- **ODA Canvas**: Execution environment that supports ODA Components by providing access to cloud-native services (API Gateway, Service Mesh, Observability, Identity Management, etc.)
- **ODA Component**: Software components following the ODA Component Specification with metadata for lifecycle management
- **Operators**: Management-plane functions that manage ODA Components using the Kubernetes Operator Pattern
- **Webhooks**: Integration with Kubernetes Control Plane supporting multiple versions of the ODA Component Standard
- **BDD Testing**: Behavior-Driven Development approach for documenting and testing Canvas behaviors

## Architecture

The ODA Canvas implements a modular architecture with independent operators:

- **Component Management**: Manages component lifecycle and decomposition into ExposedAPIs, IdentityConfigs, etc.
- **API Management**: Manages API Gateway/Service Mesh for security, throttling, and non-functional services
- **Identity Config**: Configures Identity Management Services
- **Secrets Management**: Optional operator for configuring secrets
- **Dependency Management**: Enables components to discover API dependencies

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

## Project Structure

- `charts/`: Helm charts for deploying Canvas components
- `canvas-portal/`: Spring Boot + Vue.js web portal for Canvas management
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

## Development Guidelines

1. Follow BDD approach: create use cases first, then BDD scenarios, then implementation
2. Use Kubernetes Operator Pattern for new operators
3. Support N-2 versions of ODA Component Standard (currently v1, v1beta4, v1beta3)
4. Include comprehensive docstrings in source code
5. Follow existing code conventions and patterns in each language
6. Create tests for all new functionality

## Testing

### BDD Feature Tests
Run the comprehensive test suite that validates Canvas compliance:
```bash
cd feature-definition-and-test-kit
npm start
```

### Unit Tests
- Python: `pytest` in operator directories
- Java: `mvn test` in Java modules
- Node.js: `npm test` in service directories

## Important Files

- `Canvas-design.md`: Overall Canvas design documentation
- `SecurityPrinciples.md`: Security principles and guidelines
- `Authentication-design.md`: Authentication design patterns
- `charts/canvas-oda/values.yaml`: Main Canvas configuration
- `source/operators/requirements.txt`: Python operator dependencies
- `.github/copilot-instructions.md`: AI coding assistant guidelines

## Component Specification Versions

The Canvas supports multiple versions of the ODA Component Specification:
- v1 (current)
- v1beta4 (deprecated)
- v1beta3 (deprecated with warnings)

Always check component version compatibility when making changes to operators or webhooks.