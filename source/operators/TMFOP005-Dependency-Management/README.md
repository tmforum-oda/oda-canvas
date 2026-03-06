# TMFOP005 Dependency Management Operators

Ensures ODA Components can reliably discover and connect to the APIs they depend on. Rather than requiring manual wiring between components, it continuously resolves service dependencies at runtime — enabling components to interoperate seamlessly as the Canvas evolves, new components are deployed, or existing ones are upgraded.

At present, there is one implementation: 

* [simple-dependency-management](./simple-dependency-management/): Implementation of a Dependency Management operator suitable for testing. 

Typically the real implementation of this will be specific to each Service Provider and will link into their processes and policies for granting access for API dependencies.

## Sequence Diagrams

See [UC007-Configure-Dependent-APIs](../../../usecase-library/UC007-Configure-Dependent-APIs.md) for details of the Dependency Management use case.

