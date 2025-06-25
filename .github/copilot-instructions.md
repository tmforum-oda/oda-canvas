# Copilot Instructions for TM Forum ODA Canvas

## Project Overview

This repository contains the Reference Implementation, open-source code, use cases, and test kit for a TM Forum Open Digital Architecture (ODA) Canvas. The ODA Canvas is an execution environment for ODA Components.

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

## Project Structure

- **usecase-library/**: Contains use cases describing how ODA Components interact with the ODA Canvas
- **feature-definition-and-test-kit/**: Details the features required for Canvas compliance and tests to validate implementations
- **source/**: Contains source code for Canvas operators
  - **operators/**: Key part of the Canvas that manages ODA Components
  - **webhooks/**: Integrates with Kubernetes Control Plane
  - **utilities/**: Tools for development and troubleshooting
- **charts/**: Helm charts for deploying Canvas components
- **installation/**: Installation guides and scripts
- **docs/**: Additional documentation for developers

## Development Guidelines

When contributing to this project:

1. Follow the code-of-conduct and contribution guidelines in CONTRIBUTING.md
2. Use BDD for new features, starting with use cases and creating corresponding BDD scenarios
3. Document design decisions in the Architecture Decision Log
4. Include docstrings in source code
5. Use GitHub issues for tracking work
6. For operators, follow the Kubernetes Operator Pattern

## Testing and Validation

- BDD features and scenarios are used to create executable tests
- The test kit validates Canvas implementations
- Components are tested against the standard ODA Component Specification
- Tests are automated to ensure compliance with security principles

## Further Documentation

For more detailed information, refer to:

- Canvas-design.md: Overall Canvas design documentation
- README.md: Main project introduction
- SecurityPrinciples.md: Detailed security principles
- Authentication-design.md, Event-based-integration-design.md, Observability-design.md: Design epic documentation
