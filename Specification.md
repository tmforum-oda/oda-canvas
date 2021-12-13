# ODA Reference Implementation and Environment Specification
The ODA Reference Implementation (ODA-RI) is the proving ground for building a common environment for TM Forum ODA Components. The five levels of specifications and implementation details in this process are:
- The set of _core component specifications_, which define the core functions exposed by each individual component
- The component _generic specification_, which defines the common characteristics shared by every ODA component
- The _environment specification_, which defines the underlying platform required to support the components
- The _ODA Reference Implementation_, which is a practical implementation of the environment specification
- The _supplemental services_ required to emulate capabilities that are normally available in a service provider outside the ODA scope.

This page documents the environment specification, reference implementation and supplemental services as we discover them through building and testing the ODA-RI.

## ODA Environment Specification
### Kubernetes
[Kubernetes](https://kubernetes.io) is the base platform technology.
- Version 1.19 or higher (1.21 has been shown to work at the time of writing) is required
- Cluster DNS is required
- The cloud provider is not important as long as the Kubernetes API is exposed.

### Custom Resource Definitions

There are custom resource definitions for:
- api.oda.tmforum.org
- components.oda.tmforum.org

### Controllers

SRE teams will need to maintain custom controllers for:
- Managing the configuration of components
- Managing ingress and API gateways for APIs
- The CRD webhook controller
- Bootstrapping and integrating with identiy and access management
- Integrating service discovery and service mesh
- Managing certificates

### Service discovery
- Most discovery will happen either via DNS to pre-defined names or using TM Forum ODA specific custom resource definitions

Default DNS entries are required for:
- Service discovery itself

### Service Mesh
Service mesh is required to provide the following functions:
- automatic encryption of all cluster traffic using sidecar proxies

### Key and certificate management
- The cluster requires API-driven access to a certifying authority for issuing trusted certificates for the API front end. This could be an external service, but for perfoamnce reasons it may be dsirable to provide a cluster-hosted sub-CA using technology like [Hashicorp Vault](https://www.vaultproject.io/) or [cert-manager](https://cert-manager.io/).
- Kubernetes secrets are good, but provision should be made for this to be backed by a third party key manager like [Hashicorp Vault](https://www.vaultproject.io/).

### Identity and access management
- The ODA expects there to be an identity management in the external organisation and does not provide any identity management services.
- Authentication and authorisationto be provided by an external provider using any combination of OIDC, SAML, Active Directory or LDAP.
- The ODA expects exchange of identity information using SCIM, with TM-Forum APIs as fallback.
- Bootstrapping identity between components and the underlying environment relies on the identity and access integration being provided and components supporting TMF669 Party role Management being exposed into the canvas environment (i.e. within the cluster).

### Observability
- The ODA implements a collection service for events and metrics. Custom controllers may be required to collect from components that expect different collectors.

## ODA-RI environment implementation
- [Rancher](https://rancher.com/) is being used to manage the Kubernetes clusters.
- [Istio](https://istio.io/) has been implemented as the service mesh as it is provided with Rancher.
- [Prometheus] is the default metric collector.
- No default log/event collector has been implemented yet.
- For minimal (non-service-mesh) implementations, [cert-manager](https://cert-manager.io/) is also an available option for providing certifiactes for securing the CRD webhook.
- A full suite of example controllers is provided.

## ODA-RI specific supplementary services
- [Keycloak](https://www.keycloak.org/) has been implemented to provide identity and access services that would normally be provided by the organisation outside the ODA architecture. So far, the ODA-RI has the capability to synchronise roles with components, but user account management, authorisation and authentication journeys are backlogged.