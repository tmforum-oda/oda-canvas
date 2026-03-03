# TMFO008 OAuth2 Config Operators

Enforces token-based authentication at the service mesh level, ensuring that only properly authorised callers can communicate between ODA Components. It provides a consistent, policy-driven security boundary across all inter-component traffic without requiring individual components to implement their own authentication logic.

At present, there is one implementation:

* [Envoy Filter](./envoy-filter/): OAuth2 EnvoyFilter Operator for Istio service mesh.

## Sequence Diagrams

See [UC009-Internal-Authentication](../../../usecase-library/UC009-Internal-Authentication.md) for details of the OAuth2 authentication use case.

