# TMFO007 Secrets Management Operators

Provides enterprise-grade secrets management for ODA Components by integrating with an external secrets vault. It ensures that sensitive configuration — such as passwords, API keys, and certificates — is stored, accessed, and rotated securely, without embedding secrets in component configuration or container images.

At present, there is one implementation:

* [Vault](./vault/): Implementation of a Secrets Management Operator for HashiCorp Vault.

## Sequence Diagrams

See [UC014-Secrets-Management-JWT-based](../../../usecase-library/UC014-Secrets-Management-JWT-based.md) for details of the Secrets Management use case.

