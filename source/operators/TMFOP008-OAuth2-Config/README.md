# TMFOP008 OAuth2 Config Operators

Enforces token-based authentication at the service mesh level, ensuring that only properly authorised callers can communicate between ODA Components. It provides a consistent, policy-driven security boundary across all inter-component traffic without requiring individual components to implement their own authentication logic.

At present, there is one implementation:

* [Envoy Filter](./envoy-filter/): OAuth2 EnvoyFilter Operator for Istio service mesh. This operator should not be used directly, as it uses the [oauth2](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/http/injected_credentials/oauth2/v3/oauth2.proto) prototype envoy extension, which is work in progress and subject to change. But it is a good reference for implementing an own process, where to find Client-ID and Client-Secret, how to intercept and secure outgoing traffic and how to debug envoy. See [OAUTH2DEMO.md](https://github.com/tmforum-oda/oda-canvas/blob/docs/586-operator-names-numbering-and-description/source/operators/TMFOP008-OAuth2-Config/envoy-filter/OAUTH2DEMO.md)

## Sequence Diagrams

See [UC009-Internal-Authentication](../../../usecase-library/UC009-Internal-Authentication.md) for details of the OAuth2 authentication use case.

