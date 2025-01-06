# Identity Config Operators

Each ODA Component includes a declarative definition of its requirements for creating Roles and Permissions in the Identity Management system. 

A Canvas platform can use any Identity Management system. IdentityConfig Operators automate the configuration of whatever Identity Management service is used.

The Component Operator takes the `Component` custom resource and extracts the identity configuration requirements into an IdentityConfig resource. The IdentityConfig Operator is a class of Canvas Operator then manages the lifecycle of these `IdentityConfig` resources. In a given Canvas implementation, you can implement any Identity Management system by installing the corresponding IdentityConfig operator as part of the Canvas installation.  

At present, there are IdentityConfig Operators for the following:

* [Keycloak](./keycloak): Operator for the Keycloak open source Identity Management system (https://www.keycloak.org/).
* [Microsoft Azure Entra ID](../../../installation/azure): Operator for Azure Entra ID (https://learn.microsoft.com/en-us/entra/identity/).

## IdentityConfig Data Model

The `IdentityConfig` resource describes the permissions a component would like to configure in the Identity Management system. The component can provide static definitions in the component itself, or the component can dynamically manage the permissions by exposing a TM Forum Open-API.


IdentityConfig with statically defined roles.

```yaml
apiVersion: oda.tmforum.org/v1
kind: IdentityConfig
metadata:
  name: ctk-productcatalogmanagementproductcatalogmanagement # Kubernetes resource name for the instance of the IdentityConfig
spec:
  canvasSystemRole: Admin
  componentRole:
  - description: Product Catalogue Administrator
    name: pcadmin
  - description: Catalogue Owner for catalogue 1
    name: cat1owner
  - description: Catalogue Owner for catalogue 2
    name: cat2owner
```

IdentityConfig with dynamically defined roles. At present this uses the TMF669 Party Role Management API; In the future this will be updated to use the TMF672 User Roles and Permissions API.

```yaml
apiVersion: oda.tmforum.org/v1
kind: IdentityConfig
metadata:
  name: ctk-productcatalogmanagementproductcatalogmanagement # Kubernetes resource name for the instance of the IdentityConfig
spec:
  canvasSystemRole: Admin
  partyRoleAPI:
    implementation: ctk-partyroleapi
    path: /ctk-productcatalogmanagement/tmf-api/partyRoleManagement/v4
    port: 8080
```

## Sequence Diagrams

See [UC005-Configure-Users-and-Roles](../../../usecase-library/UC005-Configure-Users-and-Roles.md) for details of the Identity Management System use case.