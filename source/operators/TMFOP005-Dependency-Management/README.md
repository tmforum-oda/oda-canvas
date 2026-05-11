# TMFOP005 Dependency Management Operators

Ensures ODA Components can reliably discover and connect to the APIs they depend on. Rather than requiring manual wiring between components, it continuously resolves service dependencies at runtime — enabling components to interoperate seamlessly as the Canvas evolves, new components are deployed, or existing ones are upgraded.

There are two implementations:

* [simple-dependency-management](./simple-dependency-management/): Reference implementation suitable for testing and development. Resolves dependencies automatically without authorization checks.
* [dependency-management-using-keycloak-authorization](./dependency-management-using-keycloak-authorization/): Production-oriented implementation that ties dependency resolution to Keycloak role grants. A dependency is only resolved after authorization has been explicitly granted in Keycloak.

Typically, the real implementation of this will be specific to each Service Provider and will link into their processes and policies for granting access for API dependencies. The canvas-oda Helm chart allows you to enable exactly one of these operators at a time.

## Sequence Diagrams

See [UC007-Configure-Dependent-APIs](../../../usecase-library/UC007-Configure-Dependent-APIs.md) for details of the Dependency Management use case.

