# Identity Config Operator - Permission Specification Set Support

## Overview

The Identity Config Operator has been extended to support `permissionSpecificationSetAPI` in addition to the existing `partyRoleAPI` support. This allows ODA Components to expose dynamic permission/role management through permission specification sets.

## Changes Made

### 1. Identity Config Operator (`identityConfigOperatorKeycloak.py`)

- **Extended listener registration**: The operator now checks for both `partyRoleAPI` and `permissionSpecificationSetAPI` in the IdentityConfig spec
- **Dual registration support**: If either API is present, the operator registers a listener with the respective API's hub endpoint
- **Improved status reporting**: The `listenerRegistered` status is now set to `true` if either API listener is successfully registered

### 2. Identity Listener (`identity-listener-keycloak.py`)

- **Unified event handling**: The Flask listener now handles both party role and permission specification set events
- **New event constants**: Added support for:
  - `PermissionSpecificationSetCreationNotification`
  - `PermissionSpecificationSetAttributeValueChangeNotification` 
  - `PermissionSpecificationSetRemoveNotification`
- **Modular event processing**: Separated handling into discrete functions for maintainability

## Usage

### IdentityConfig Resource Example

```yaml
apiVersion: oda.tmforum.org/v1
kind: IdentityConfig
metadata:
  name: my-component
spec:
  canvasSystemRole: CanvasRole
  
  # For dynamic party roles
  partyRoleAPI:
    implementation: my-component-service
    path: /my-component/partyRoleManagement/v4
    port: 8080
  
  # For dynamic permission specifications
  permissionSpecificationSetAPI:
    implementation: my-component-service
    path: /my-component/rolesAndPermissionsManagement/v5
    port: 8080
```

### Event Structure

#### Permission Specification Set Events

Events should follow this structure:

```json
{
  "eventType": "PermissionSpecificationSetCreationNotification",
  "event": {
    "permissionSpecificationSet": {
      "@baseType": "PermissionSpecificationSet",
      "name": "MyNewRole",
      "href": "/my-component/rolesAndPermissionsManagement/v5/permissionSpecificationSet/123"
    }
  }
}
```

## Behavior

1. **Component Registration**: When an IdentityConfig is created/updated:
   - The operator creates a Keycloak client for the component
   - If `partyRoleAPI` is present, registers listener for party role events
   - If `permissionSpecificationSetAPI` is present, registers listener for permission specification set events
   - Both APIs can be present simultaneously

2. **Event Processing**: When events are received:
   - **Creation events**: New roles are added to the component's Keycloak client
   - **Deletion events**: Roles are removed from the component's Keycloak client  
   - **Update events**: Currently ignored (no action taken)

3. **Error Handling**: Failed operations are logged with CloudEvents-formatted messages and retried according to the operator's retry policy

## Compatibility

This extension is backward compatible. Existing IdentityConfig resources using only `partyRoleAPI` will continue to work unchanged.
