# UC005-F005 Test Implementation Guide

## Overview

This document provides implementation guidance for testing Use Case 5, Feature 5: "Bootstrap: Add Permission Specification Sets in Component to Identity Platform".

## Test Component

The test uses the `productcatalog-dynamic-roles-v1` component which is configured to expose the TMF672 User Roles and Permissions API for dynamic role management.

## Component Configuration

The `productcatalog-dynamic-roles-v1` component includes:

1. **Core Function**: Standard TMF620 Product Catalog Management API
2. **Security Function**: 
   - TMF672 User Roles and Permissions API (when `permissionspec.enabled=true`)
   - Path: `/rolesAndPermissionsManagement/v5`
   - Implementation: `{{.Release.Name}}-permissionspecapi`

## Test Scenarios

### 1. Bootstrap Component with Dynamic Permission Specification Sets

**Purpose**: Verify that a component with permission specification set API gets properly registered

**Steps**:
1. Install the component with `permissionspec.enabled=true`
2. Verify the component is created in Kubernetes
3. Verify the IdentityConfig resource is created
4. Verify the Identity Config operator registers a listener with the TMF672 API

**Expected Results**:
- Component deployed successfully
- Keycloak client created for the component
- Listener registered with TMF672 API at `/hub` endpoint
- IdentityConfig status shows `listenerRegistered: true`

### 2. Add New Permission Specification Set

**Purpose**: Test creating a new role through the TMF672 API

**Steps**:
1. POST a new PermissionSpecificationSet to the TMF672 API:
   ```json
   {
     "@type": "PermissionSpecificationSet",
     "name": "DynamicRole1",
     "description": "Test dynamic role",
     "involvementRole": "TestRole"
   }
   ```
2. Verify the component sends a `PermissionSpecificationSetCreationNotification` event
3. Check that the identity listener receives the event
4. Verify the role is created in Keycloak

**Expected Results**:
- Event notification sent to identity listener
- Role `DynamicRole1` created in Keycloak for the component client
- Detailed logging shows successful processing

### 3. Update Permission Specification Set

**Purpose**: Test updating an existing permission specification set

**Steps**:
1. PATCH an existing PermissionSpecificationSet
2. Verify `PermissionSpecificationSetAttributeValueChangeNotification` is sent
3. Confirm no changes are made to Keycloak (updates are ignored)

**Expected Results**:
- Update notification received
- No changes made to Keycloak role
- Event logged as processed but ignored

### 4. Delete Permission Specification Set

**Purpose**: Test removing a role through the TMF672 API

**Steps**:
1. DELETE an existing PermissionSpecificationSet
2. Verify `PermissionSpecificationSetRemoveNotification` is sent
3. Check that the role is removed from Keycloak

**Expected Results**:
- Delete notification received
- Role removed from Keycloak
- Component client no longer has the role

### 5. Multiple Role Management

**Purpose**: Test creating multiple roles simultaneously

**Steps**:
1. Create multiple PermissionSpecificationSets via API
2. Verify all roles are created in Keycloak
3. Query Keycloak admin API to confirm all roles exist

## Test Configuration

### Values.yaml Settings

To enable permission specification set testing:

```yaml
permissionspec:
  enabled: true  # Enables TMF672 API instead of TMF669 PartyRole API

security:
  canvasSystemRole: "CanvasRole"
```

### Environment Variables

Ensure the following are set for the identity listener:

```bash
KEYCLOAK_USER=admin
KEYCLOAK_PASSWORD=<password>
KEYCLOAK_BASE=http://keycloak:8080
KEYCLOAK_REALM=<realm-name>
LOGGING=10  # Debug level for detailed logging
```

## API Endpoints

### Component APIs

- **Product Catalog**: `/productcatalog-dynamic-roles-v1/tmf-api/productCatalogManagement/v4`
- **Permission Specification**: `/productcatalog-dynamic-roles-v1/rolesAndPermissionsManagement/v5`
- **API Hub**: `/productcatalog-dynamic-roles-v1/rolesAndPermissionsManagement/v5/hub`

### Canvas APIs

- **Identity Listener**: `http://idlistkey.canvas:5000/listener`
- **Listener Status**: `http://idlistkey.canvas:5000/status`

## Verification Steps

### Check Component Registration

```bash
# Check component is deployed
kubectl get components -n <namespace>

# Check IdentityConfig is created
kubectl get identityconfigs -n <namespace>

# Check IdentityConfig status
kubectl get identityconfig <component-name> -o yaml
```

### Check Keycloak Integration

```bash
# Check Keycloak clients
curl -H "Authorization: Bearer <token>" \
  "http://keycloak:8080/auth/admin/realms/<realm>/clients"

# Check roles for specific client
curl -H "Authorization: Bearer <token>" \
  "http://keycloak:8080/auth/admin/realms/<realm>/clients/<client-id>/roles"
```

### Check Event Processing

```bash
# Check identity listener logs
kubectl logs -n canvas deployment/identity-listener-keycloak -f

# Check identity config operator logs  
kubectl logs -n canvas deployment/identity-config-operator -f
```

## Expected Event Structure

### PermissionSpecificationSetCreationNotification

```json
{
  "eventId": "uuid",
  "eventTime": "2025-06-30T10:00:00.000Z", 
  "eventType": "PermissionSpecificationSetCreationNotification",
  "event": {
    "permissionSpecificationSet": {
      "@type": "PermissionSpecificationSet",
      "@baseType": "PermissionSpecificationSet", 
      "name": "DynamicRole1",
      "href": "/productcatalog-dynamic-roles-v1/rolesAndPermissionsManagement/v5/permissionSpecificationSet/123",
      "description": "Test dynamic role"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Component name extraction fails**: 
   - Check the href structure in the event payload
   - Verify the href parsing logic in the identity listener

2. **Keycloak client not found**:
   - Ensure the component was properly registered
   - Check that the client name matches the component name

3. **Listener not registered**:
   - Verify the TMF672 API is accessible
   - Check that `permissionspec.enabled=true` in values.yaml
   - Confirm the hub endpoint is available

4. **Events not received**:
   - Check the TMF672 API implementation
   - Verify the hub registration was successful
   - Check network connectivity between components

### Debug Commands

```bash
# Enable debug logging
export LOGGING=10

# Check listener registry
kubectl exec -it deployment/identity-config-operator -- python -c "
from identityConfigOperatorKeycloak import log_all_registered_listeners
log_all_registered_listeners()
"

# Test listener connectivity
curl -X GET http://idlistkey.canvas:5000/status
```
