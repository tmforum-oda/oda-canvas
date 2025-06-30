# UC005-F005: Permission Specification Sets Testing

## Overview

This directory contains tests for Use Case 5, Feature 5: "Bootstrap: Add Permission Specification Sets in Component to Identity Platform". The tests verify that components can dynamically manage roles through the TMF672 User Roles and Permissions API, with automatic synchronization to the Identity Platform (Keycloak).

## Test Components

### 1. BDD Feature File
- **File**: `features/UC005-F005-Bootstrap-Add-Permission-Specification-Sets-in-Component-to-Identity-Platform.feature`
- **Purpose**: Defines test scenarios in human-readable Gherkin format
- **Scenarios**:
  - Bootstrap component with dynamic permission specification sets
  - Add new permission specification set via TMF672 API
  - Update permission specification set (ignored by design)
  - Delete permission specification set via TMF672 API
  - Verify multiple role management

### 2. JavaScript Test Implementation
- **File**: `phase-1-tests/uc005-f005-tests.js`
- **Purpose**: Automated test implementation using Mocha/Chai
- **Coverage**: 
  - Component deployment verification
  - IdentityConfig resource creation
  - Identity listener registration
  - Event processing validation
  - Cleanup verification

### 3. Test Component
- **Component**: `testData/productcatalog-dynamic-roles-v1`
- **Configuration**: TMF672 User Roles and Permissions API enabled
- **Features**:
  - Dynamic role management through TMF672 API
  - Event notifications for role changes
  - Integration with Canvas Identity Config system

## Prerequisites

### 1. Canvas Environment
- ODA Canvas deployed with identity management components
- Keycloak identity provider configured
- Identity Config Operator running
- Identity Listener service deployed

### 2. Test Component Deployment
Deploy the test component with permission specification sets enabled:

```bash
cd feature-definition-and-test-kit/testData
helm install productcatalog-dynamic-roles-v1 ./productcatalog-dynamic-roles-v1 \
  --set permissionspec.enabled=true \
  --namespace components
```

### 3. Environment Configuration
Ensure the following environment variables are set:

```bash
# For Identity Config Operator
KEYCLOAK_USER=admin
KEYCLOAK_PASSWORD=<your-password>
KEYCLOAK_BASE=http://keycloak:8080
KEYCLOAK_REALM=<your-realm>
LOGGING=10

# For test execution
CANVAS_CTK_MANDATORY_ONLY=false
CANVAS_CTK_OPTIONAL_KEYCLOAK=true
```

## Running the Tests

### 1. Automated JavaScript Tests
```bash
cd feature-definition-and-test-kit/phase-1-tests
npm install
npm test -- --grep "UC005-F005"
```

### 2. Manual BDD Validation
Follow the scenarios in the feature file:

1. **Verify Component Bootstrap**:
   ```bash
   kubectl get components productcatalog-dynamic-roles-v1 -n components
   kubectl get identityconfigs productcatalog-dynamic-roles-v1 -n components
   ```

2. **Test Role Creation**:
   ```bash
   # Create a new permission specification set
   curl -X POST \
     http://<component-url>/rolesAndPermissionsManagement/v5/permissionSpecificationSet \
     -H "Content-Type: application/json" \
     -d '{
       "@type": "PermissionSpecificationSet",
       "name": "TestRole1",
       "description": "Test role for UC005-F005",
       "involvementRole": "TestRole"
     }'
   ```

3. **Verify Event Processing**:
   ```bash
   # Check identity listener logs
   kubectl logs -n canvas deployment/identity-listener-keycloak -f
   
   # Check identity config operator logs
   kubectl logs -n canvas deployment/identity-config-operator -f
   ```

4. **Verify Keycloak Integration**:
   ```bash
   # Get Keycloak admin token
   TOKEN=$(curl -X POST \
     "http://keycloak:8080/auth/realms/master/protocol/openid-connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=<password>&grant_type=password&client_id=admin-cli" \
     | jq -r '.access_token')
   
   # Check component client roles
   curl -H "Authorization: Bearer $TOKEN" \
     "http://keycloak:8080/auth/admin/realms/<realm>/clients/<client-id>/roles"
   ```

## Test Validation

### Success Criteria

1. **Component Bootstrap**:
   - ✅ Component deployed successfully
   - ✅ IdentityConfig resource created
   - ✅ Keycloak client created for component
   - ✅ Listener registered with TMF672 API

2. **Role Creation**:
   - ✅ POST to TMF672 API succeeds
   - ✅ PermissionSpecificationSetCreationNotification sent
   - ✅ Identity listener receives and processes event
   - ✅ Role created in Keycloak for component client

3. **Role Deletion**:
   - ✅ DELETE from TMF672 API succeeds
   - ✅ PermissionSpecificationSetRemoveNotification sent
   - ✅ Identity listener processes deletion
   - ✅ Role removed from Keycloak

4. **Error Handling**:
   - ✅ Invalid events handled gracefully
   - ✅ Missing components reported properly
   - ✅ Keycloak errors logged with details

### Expected Log Output

#### Component Registration
```
INFO - Registering listener for permissionSpecificationSetAPI - Hub URL: http://productcatalog-dynamic-roles-v1.components.svc.cluster.local:8080/rolesAndPermissionsManagement/v5/hub
INFO - Successfully registered listener for permissionSpecificationSetAPI
INFO - Added permissionSpecificationSetAPI listener for component productcatalog-dynamic-roles-v1 to registry
```

#### Event Processing
```
INFO - === NOTIFICATION RECEIVED ===
INFO - Event Type: PermissionSpecificationSetCreationNotification
INFO - Notification Source: permissionSpecificationSet API
INFO - PermissionSpecificationSet details: name=TestRole1, href=/productcatalog-dynamic-roles-v1/rolesAndPermissionsManagement/v5/permissionSpecificationSet/123
INFO - Keycloak role TestRole1 added to productcatalog-dynamic-roles-v1
INFO - === NOTIFICATION PROCESSING COMPLETE (permissionSpecificationSet) ===
```

## Troubleshooting

### Common Issues

1. **Component not found**: Verify deployment with correct namespace
2. **Listener registration failed**: Check TMF672 API availability and network connectivity
3. **Keycloak client missing**: Verify Identity Config Operator is running and has correct credentials
4. **Events not processed**: Check identity listener service and logs

### Debug Commands

```bash
# Check Canvas services
kubectl get pods -n canvas

# Check component services  
kubectl get pods -n components

# Check service endpoints
kubectl get endpoints -n components productcatalog-dynamic-roles-v1

# Test identity listener health
curl http://idlistkey.canvas:5000/status

# Check registered listeners (from operator logs)
kubectl logs -n canvas deployment/identity-config-operator | grep "registered listeners"
```

## Integration with CI/CD

This test can be integrated into automated pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run UC005-F005 Tests
  run: |
    cd feature-definition-and-test-kit/phase-1-tests
    npm install
    npm test -- --grep "UC005-F005" --reporter json > test-results.json
    
- name: Validate Test Results
  run: |
    node -e "
      const results = require('./test-results.json');
      if (results.failures > 0) process.exit(1);
      console.log('✅ All UC005-F005 tests passed');
    "
```

## Related Documentation

- [UC005 Use Case Library](../../usecase-library/UC005-Configure-Clients-and-Roles.md)
- [Identity Config Operator Design](../../Authentication-design.md)
- [TMF672 API Specification](https://www.tmforum.org/resources/standard/tmf672-user-role-permission-api-rest-specification-r19-5-0/)
- [Test Implementation Guide](./UC005-F005-Test-Implementation-Guide.md)
