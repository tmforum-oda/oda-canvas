# Manage Identities

## Table of Contents
- [Identity Management in ODA Canvas](#identity-management-in-oda-canvas)
- [View IdentityConfig Resources](#view-identityconfig-resources)
- [IdentityConfig Drill-Down](#identityconfig-drill-down)
- [Understanding the CRD Schema](#understanding-the-crd-schema)
- [Add Component Roles](#add-component-roles)
- [Keycloak UI Access](#keycloak-ui-access)
- [Create a Keycloak Client](#create-a-keycloak-client)
- [Verify Keycloak-Kong JWT Integration](#verify-keycloak-kong-jwt-integration)
- [Generate a Postman Collection](#generate-a-postman-collection)
- [Contextual Next Steps](#contextual-next-steps)

## Identity Management in ODA Canvas

The ODA Canvas uses **Keycloak** as its Identity Management solution. When a Component is deployed, the **Identity Config Operator** reads the component's `spec.securityFunction` and creates an `IdentityConfig` child resource. The operator then configures Keycloak by:

1. **Creating a Keycloak client** named after the component (e.g., `pc1-productcatalogmanagement`) in the Canvas realm
2. **Registering the Canvas system role** (typically `canvasRole`) -- this is a reserved role used by Canvas operators to interact with the component's APIs; it should never be assigned to end users
3. **Listening for role changes** -- if the component exposes a `permissionSpecificationSetAPI` or `partyRoleAPI`, the operator registers a listener to detect when the component adds or removes roles dynamically

**Key concepts:**
- Each deployed component has exactly one `IdentityConfig` resource, owned by the parent Component
- The `canvasSystemRole` is reserved for Canvas infrastructure -- do not assign it to human users
- **Component roles are managed by the ODA Component, not directly in Keycloak.** The Identity Config Operator syncs roles from the component to Keycloak automatically. There are two mechanisms:
  - **Static roles**: defined in the Component YAML under `spec.securityFunction.componentRole[]` and configured at deployment time
  - **Dynamic roles**: the component exposes a `permissionSpecificationSetAPI` (TMF672) or `partyRoleAPI` (TMF669), and the Identity Config Operator registers a listener to detect role changes and syncs them to Keycloak
- Roles are scoped to a Keycloak **client**, not the realm -- each component manages its own set of roles
- **Do not create or delete roles directly in Keycloak for component clients** -- the Identity Config Operator is the authoritative source and will overwrite manual changes
- Roles **can** be created directly in Keycloak for **external clients** (non-component clients created for M2M access)
- **Clients** (applications/services) authenticate using the **Client Credentials flow** -- this is the recommended approach for API access. Always create an **external Keycloak client** for programmatic access -- do not create Keycloak users

## View IdentityConfig Resources

Present the sub-menu when the user selects "Manage identities":

| # | Action |
|---|--------|
| 1 | **View IdentityConfig resources** -- List all IdentityConfig custom resources |
| 2 | **View Keycloak UI** -- Access the Keycloak admin console |
| 3 | **Add component roles** -- Add roles to a component (static or dynamic) |
| 4 | **Create a Keycloak client** -- Create an external client for the Client Credentials flow |
| 5 | **Check Keycloak-Kong JWT integration** -- Verify Kong can validate Keycloak JWT tokens |
| 6 | **Generate a Postman collection** -- Create a Postman collection for authenticated API testing |
| 7 | **Return to main menu** |

### Listing IdentityConfigs

```bash
# Raw output
kubectl get identityconfigs -n components

# Structured summary using helper script
kubectl get identityconfigs -n components -o json | python <scripts>/parse_identityconfigs.py
```

The summary shows:

| Column | Description |
|--------|-------------|
| NAME | IdentityConfig resource name (matches component name) |
| IDENTITY PROVIDER | The identity provider in use (e.g., Keycloak) |
| LISTENER REG. | Whether a listener is registered for dynamic role changes |
| ROLES | Number of static roles, or "dynamic" if roles come via an API |

After listing, offer to drill into a specific IdentityConfig.
## IdentityConfig Drill-Down

```bash
kubectl get identityconfig <name> -n components -o json | python <scripts>/parse_identityconfig_drilldown.py
```

This shows:
- **Parent Component** -- the Component that owns this IdentityConfig
- **Canvas System Role** -- the reserved role for Canvas operators (typically `canvasRole`)
- **Identity Provider** -- the configured identity provider (Keycloak)
- **Listener Registered** -- whether the operator is listening for dynamic role changes
- **Static Component Roles** -- any roles declared in `spec.componentRole[]`
- **Permission Specification Set API** -- the API endpoint for dynamic role management (if configured)
- **Party Role API** -- legacy API for dynamic roles (if configured)

After drill-down, explain:
- The **canvasSystemRole** (e.g., `canvasRole`) is used by Canvas operators to authenticate against the component's APIs. It is created automatically and should not be assigned to users.
- If **permissionSpecificationSetAPI** is configured, the component exposes a TMF API (typically TMF672 Permission Specification) that allows it to define roles dynamically. The Identity Config Operator registers a listener on this API to detect role changes and syncs them to Keycloak.
- **Static componentRoles** are defined in the Component YAML and configured once at deployment time.

You can also view the raw YAML:

```bash
kubectl get identityconfig <name> -n components -o yaml
```
## Understanding the CRD Schema

Offer to explore the IdentityConfig schema:

```bash
kubectl explain identityconfig.spec
kubectl explain identityconfig.spec.componentRole
kubectl explain identityconfig.spec.permissionSpecificationSetAPI
```

**Key v1 schema properties** (from `charts/oda-crds/templates/oda-identityconfig-crd.yaml`):

| Field | Type | Description |
|-------|------|-------------|
| `canvasSystemRole` | string | Role name for Canvas operators to use (reserved) |
| `componentRole[]` | array of {name, description} | Statically defined roles |
| `permissionSpecificationSetAPI` | object {implementation, path, port} | API for dynamic role management |
| `partyRoleAPI` | object {implementation, path, port} | Legacy API for dynamic roles (deprecated in future) |

**Status fields:**

| Field | Description |
|-------|-------------|
| `.status.identityConfig.identityProvider` | The identity provider (e.g., Keycloak) |
| `.status.identityConfig.listenerRegistered` | Whether a listener is active for dynamic role changes |
## Add Component Roles

ODA Component roles are **managed by the component itself** and synced to Keycloak automatically by the Identity Config Operator. You should **never create roles directly in Keycloak** for a component client -- the operator is the authoritative source and will overwrite manual changes.

There are two mechanisms for defining component roles:

### Option A: Static Roles (Component YAML)

Static roles are defined in the Component's Helm chart under `spec.securityFunction.componentRole[]`. They are configured once at deployment time and synced to Keycloak by the Identity Config Operator.

**Example** (from `feature-definition-and-test-kit/testData/productcatalog-static-roles-v1/`):

```yaml
spec:
  securityFunction:
    canvasSystemRole: canvasRole
    componentRole:
    - name: pcadmin
      description: Product Catalogue Administrator
    - name: cat1owner
      description: Catalogue Owner for catalogue 1
    - name: cat2owner
      description: Catalogue Owner for catalogue 2
```

To add a new static role to an existing component:

1. **Edit** the component's Helm chart values or template to add the role to `spec.securityFunction.componentRole[]`
2. **Upgrade** the Helm release:
   ```bash
   helm upgrade <release-name> <chart> -n components
   ```
3. The Component Operator updates the `IdentityConfig` child resource, the Identity Config Operator detects the change and syncs the new role to Keycloak.
4. **Verify** the role appears in Keycloak:
   ```bash
   python <scripts>/manage_keycloak_users.py \
     --keycloak-url http://localhost:8083/auth \
     --admin-password <ADMIN_PASS> \
     --realm odari \
     --action list-roles \
     --client-id <component-name>
   ```

### Option B: Dynamic Roles (permissionSpecificationSetAPI)

Dynamic roles are defined at runtime by the component via its **TMF672 Permission Specification** API (or the legacy TMF669 Party Role API). The Identity Config Operator registers a listener on this API and syncs role changes to Keycloak automatically.

**Example** (from `feature-definition-and-test-kit/testData/productcatalog-v1/`):

```yaml
spec:
  securityFunction:
    canvasSystemRole: canvasRole
    exposedAPIs:
    - name: userrolesandpermissions
      specification:
      - url: "https://raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermissions/master/TMF672-UserRolePermissions-v5.0.0.swagger.json"
      implementation: pc1-permissionspecapi
      apiType: openapi
      path: /pc1-productcatalogmanagement/rolesAndPermissionsManagement/v5
      port: 8080
```

To add a role dynamically, **POST** a new `PermissionSpecificationSet` to the component's TMF672 API. The component must be running and the API must be accessible.

**Step 1: Find the TMF672 API URL**

```bash
kubectl get exposedapis -n components -o json | python <scripts>/parse_exposedapis.py
```

Look for the ExposedAPI with TMF ID `TMF672`. The URL will be in the format:
`https://localhost/<component-path>/rolesAndPermissionsManagement/v5`

**Step 2: POST the PermissionSpecificationSet**

> **Critical:** The `@baseType` field **must** be set to `PermissionSpecificationSet` (uppercase 'P'). If omitted, the component's API defaults to lowercase `permissionSpecificationSet`, which the Identity Config Operator's listener will reject with an "invalid @baseType" warning and the role will **not** be synced to Keycloak.

```powershell
# PowerShell
$body = @{
    "@type" = "PermissionSpecificationSet"
    "@baseType" = "PermissionSpecificationSet"
    "name" = "<ROLE_NAME>"
    "involvementRole" = "<ROLE_NAME>"
    "description" = "<ROLE_DESCRIPTION>"
    "permissionSpecification" = @(@{
        "@type" = "PermissionSpecification"
        "name" = "<ROLE_NAME>:read-only"
        "description" = "Read-only access to resources"
        "function" = "<ROLE_NAME>"
        "action" = "all"
    })
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "https://localhost/<COMPONENT_PATH>/rolesAndPermissionsManagement/v5/permissionSpecificationSet" `
    -Method POST -ContentType "application/json" -Body $body -SkipCertificateCheck
```

```bash
# bash
curl -sk -X POST "https://localhost/<COMPONENT_PATH>/rolesAndPermissionsManagement/v5/permissionSpecificationSet" \
  -H "Content-Type: application/json" \
  -d '{
    "@type": "PermissionSpecificationSet",
    "@baseType": "PermissionSpecificationSet",
    "name": "<ROLE_NAME>",
    "involvementRole": "<ROLE_NAME>",
    "description": "<ROLE_DESCRIPTION>",
    "permissionSpecification": [{
      "@type": "PermissionSpecification",
      "name": "<ROLE_NAME>:read-only",
      "description": "Read-only access to resources",
      "function": "<ROLE_NAME>",
      "action": "all"
    }]
  }'
```

**Key fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `@type` | Yes | Must be `PermissionSpecificationSet` |
| `@baseType` | Yes | **Must** be `PermissionSpecificationSet` (uppercase P) -- the operator rejects lowercase |
| `name` | Yes | The role name (e.g., `MVNO-user`) -- this becomes the Keycloak role name |
| `involvementRole` | Yes | Should match `name` -- identifies the role in TMF672 |
| `description` | No | Human-readable description of the role |
| `permissionSpecification[]` | Yes | Array of permission specs defining what the role grants |

**Step 3: Wait for sync**

The Identity Config Operator's listener sidecar receives the `PermissionSpecificationSetCreationNotification` from the component and creates the role in Keycloak. This typically takes a few seconds.

**Step 4: Verify** the role appears in Keycloak:

```bash
python <scripts>/manage_keycloak_users.py \
  --keycloak-url http://localhost:8083/auth \
  --admin-password <ADMIN_PASS> \
  --realm odari \
  --action list-roles \
  --client-id <component-name>
```

**Troubleshooting:** If the role does not appear after 10–15 seconds, check the listener sidecar logs:

```bash
kubectl logs <identityconfig-operator-pod> -n canvas -c idlistkey --tail=20
```

Look for:
- `"security-APIListener permissionSpecificationSet event listener success"` -- role was synced
- `"@baseType was permissionSpecificationSet - not processed"` -- the `@baseType` field has the wrong case; re-POST with `"@baseType": "PermissionSpecificationSet"`

### When to use each approach

| Approach | When to use |
|----------|-------------|
| **Static roles** | Roles are known at design time, don't change often, and are defined by the component developer |
| **Dynamic roles** | Roles are determined at runtime, managed by administrators or business logic, or change frequently |

### Important

- If the user asks to "create a role" on a component, guide them through one of these two approaches -- **do not create the role directly in Keycloak**
- If `canvasRole` is the only role and no `permissionSpecificationSetAPI` is configured, the component needs to be redeployed with static roles or updated to expose a permission specification API

## Keycloak UI Access

### Prerequisites

Keycloak runs in the `canvas` namespace. Check if it's running:

```bash
kubectl get pods -n canvas -l app.kubernetes.io/name=keycloak
```

### Retrieve Admin Credentials

The admin username is `admin`. Retrieve the password from the Kubernetes secret:

```bash
# bash
kubectl get secret canvas-keycloak -n canvas -o jsonpath='{.data.admin-password}' | base64 -d

# PowerShell
kubectl get secret canvas-keycloak -n canvas -o jsonpath='{.data.admin-password}' | python -c "import sys,base64; print(base64.b64decode(sys.stdin.read()).decode())"
```

### Access the Keycloak Console

Find the Keycloak service:

```bash
kubectl get svc canvas-keycloak -n canvas
```

If the service type is `LoadBalancer` and has an external IP/hostname, it may already be accessible. Otherwise, port-forward:

```bash
kubectl port-forward svc/canvas-keycloak -n canvas 8083:8083
```

Run port-forward as a **background process** so it remains accessible.

Open the Keycloak admin console in VS Code Simple Browser at: `http://localhost:8083/auth/admin`

Log in with:
- **Username**: `admin`
- **Password**: (retrieved from the secret above)

### Navigating Keycloak

After logging in, guide the user:
- **Select the realm**: The ODA Canvas realm is typically named `odari` (not `master`). Select it from the realm dropdown in the top-left.
- **Clients**: Each deployed ODA Component has a corresponding client. Navigate to **Clients** in the left menu to see component clients. Click a client name to see its configuration and roles.
- **Users**: Navigate to **Users** in the left menu to see all users in the realm. Service accounts for external clients appear here as `service-account-<client-id>`.
- **Client Roles**: To see roles for a component, go to **Clients** > select the component client > **Roles** tab. The `canvasRole` is reserved for Canvas operators.
## Create a Keycloak Client

This section covers creating a Keycloak **client** (application identity) for **external systems** that need to call ODA Component APIs using the **Client Credentials flow**. This is the recommended authentication approach for machine-to-machine (M2M) API access.

> **Note:** This creates an **external client** in Keycloak -- separate from the component clients that are automatically managed by the Identity Config Operator. Roles can be freely created and assigned on external clients without conflicting with the operator.

### Interactive Workflow

When the user selects "Create a Keycloak client", follow this workflow:

**Step 1: Identify the target component**

List the deployed components to determine which APIs the client needs to access:

```bash
kubectl get identityconfigs -n components -o json | python <scripts>/parse_identityconfigs.py
```

**Step 2: Ask for client details**

Ask the user for:
- **Client ID** (required) -- a descriptive name like `externalSystem`, `integration-test`, or `my-billing-app`. Must not conflict with existing component client names (e.g., do not use `pc1-productcatalogmanagement`)
- **Description** (optional) -- what the client is for

**Step 3: Create the client**

Use the helper script:

```bash
python <scripts>/manage_keycloak_users.py \
  --keycloak-url http://localhost:8083/auth \
  --admin-password <ADMIN_PASS> \
  --realm odari \
  --action create-client \
  --client-id <CLIENT_ID>
```

This creates a **confidential** Keycloak client with:
- **Client authentication**: Enabled (confidential client -- requires a client secret)
- **Service accounts roles**: Enabled (allows Client Credentials grant)
- **Direct access grants**: Enabled (allows password grant for testing)
- **Standard flow**: Disabled (no browser-based login needed)

**Step 4: Show the client secret**

After creation, retrieve the client secret:

```bash
python <scripts>/manage_keycloak_users.py \
  --keycloak-url http://localhost:8083/auth \
  --admin-password <ADMIN_PASS> \
  --realm odari \
  --action get-client-secret \
  --client-id <CLIENT_ID>
```

**Step 5: Assign component roles (optional)**

If the target component has roles beyond `canvasRole`, offer to assign them to the external client's service account. These roles are defined by the component (statically or dynamically) and already exist in Keycloak -- you are only **assigning** existing roles, not creating new ones:

```bash
python <scripts>/manage_keycloak_users.py \
  --keycloak-url http://localhost:8083/auth \
  --admin-password <ADMIN_PASS> \
  --realm odari \
  --action assign-client-roles \
  --client-id <CLIENT_ID> \
  --target-client <COMPONENT_CLIENT_ID> \
  --roles <ROLE1>,<ROLE2>
```

If no assignable roles exist yet (only `canvasRole`), explain that the component needs to define roles first -- either by adding static `componentRole[]` entries in the Component YAML or by publishing roles via its `permissionSpecificationSetAPI`. See the **Add component roles** section.

**Step 6: Verify with a Client Credentials call**

Test that the client can obtain a JWT token:

```powershell
# PowerShell
$token = (Invoke-RestMethod -Uri "http://localhost:8083/auth/realms/odari/protocol/openid-connect/token" `
  -Method POST -ContentType "application/x-www-form-urlencoded" `
  -Body "grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>").access_token
Write-Host "Token obtained successfully (length: $($token.Length) chars)"
```

```bash
# bash
TOKEN=$(curl -s -X POST http://localhost:8083/auth/realms/odari/protocol/openid-connect/token \
  -d "grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:50}..."
```

If the Client Credentials call fails with **"Client not enabled to retrieve service account"**, the service accounts option was not enabled. The user can fix this in the Keycloak UI:
1. Navigate to **Clients** > select the client
2. Go to the **Settings** tab
3. Enable **Service accounts roles** (or **Service account enabled** in older Keycloak versions)
4. Click **Save**
5. Retry the token request

### Explaining Client Scopes

When explaining the created client, mention:
- The client's **service account** is automatically created by Keycloak when service accounts are enabled. It appears as a user named `service-account-<client-id>` in the Users list.
- **Client scopes** control which claims appear in the JWT token. The default scopes (`email`, `profile`, `roles`) are typically sufficient.
- The JWT `iss` (issuer) claim will be the Keycloak realm URL (e.g., `http://localhost:8083/auth/realms/odari`). This is important for Kong JWT validation.
- The default token expiry is **300 seconds** (5 minutes). This can be changed in the client's **Advanced Settings** tab under **Access Token Lifespan**.
## Verify Keycloak-Kong JWT Integration

When `apiKeyVerification` is enabled on ExposedAPIs, the Kong API Operator creates JWT **KongPlugins** for those APIs automatically. However, Kong needs to know Keycloak's **RSA public key** to verify tokens. This section checks the bridge between Keycloak and Kong.

> **Important:** The KongPlugins, KongConsumers, and JWT credential secrets described in this section are created and managed by the **API Operator**. Do not create, delete, or modify these resources directly. The commands below are for **verification and debugging** only. To enable or disable JWT authentication, patch the `apiKeyVerification.enabled` field on the relevant **ExposedAPI** resource (see View ExposedAPIs > Enable/Disable Authentication).

### How Kong JWT Validation Works

The Kong JWT plugin uses these key settings (configured by the API Operator):
- `key_claim_name: iss` -- the JWT `iss` (issuer) claim identifies which consumer/key to use
- `claims_to_verify: [exp]` -- checks token expiry
- `secret_is_base64: false` -- the RSA public key is stored in PEM format

For Kong to validate a Keycloak JWT, you need:
1. A **KongConsumer** resource pointing to Keycloak
2. A **JWT credential** on that consumer containing Keycloak's RSA public key
3. The credential's `key` must match the JWT `iss` claim (i.e., the Keycloak realm URL)

### Step 1: Check if JWT KongPlugins exist

```bash
kubectl get kongplugins -n components -l oda.tmforum.org/type=apiauthentication
```

If no JWT plugins exist, `apiKeyVerification` is not enabled on any ExposedAPIs. Offer to enable it first (see View ExposedAPIs > Enable Authentication).

### Step 2: Check for existing KongConsumers and JWT credentials

```bash
kubectl get kongconsumers -n components
kubectl get secrets -n components -l konghq.com/credential=jwt
```

If a JWT credential secret already exists with a key matching the Keycloak issuer URL, the bridge is already configured. Verify by inspecting:

```powershell
# PowerShell
kubectl get secret <SECRET_NAME> -n components -o jsonpath='{.data.key}' | python -c "import sys,base64; print(base64.b64decode(sys.stdin.read()).decode())"
```

The key should be: `http://localhost:8083/auth/realms/odari`

### Step 3: If no integration exists — troubleshooting

The KongConsumer and JWT credential resources are created **automatically** by the API Operator when `apiKeyVerification.enabled` is set to `true` on any ExposedAPI. You should **not** create these resources manually.

If `apiKeyVerification` is enabled on an ExposedAPI but the KongConsumer or JWT credential does not exist:

1. **Check the API Operator logs** for errors:
   ```bash
   kubectl logs -n canvas -l app=api-operator-kong --tail=30
   ```

2. **Check that the ExposedAPI has `apiKeyVerification.enabled: true`**:
   ```bash
   kubectl get exposedapi <name> -n components -o jsonpath='{.spec.apiKeyVerification}'
   ```

3. **Trigger a reconciliation** by annotating the ExposedAPI:
   ```bash
   kubectl annotate exposedapi <name> -n components reconcile=$(date +%s) --overwrite
   ```

4. **Verify** the resources were created:
   ```bash
   kubectl get kongconsumers -n components
   kubectl get secrets -n components -l konghq.com/credential=jwt
   ```

If the API Operator is not running or has persistent errors, investigate the operator deployment in the `canvas` namespace.

### Step 4: Test the integration

Test with a valid JWT token (should return 200 OK):

```powershell
# Get token via Client Credentials
$tokenResponse = Invoke-RestMethod -Uri "http://localhost:8083/auth/realms/odari/protocol/openid-connect/token" `
  -Method POST -ContentType "application/x-www-form-urlencoded" `
  -Body "grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>"
$jwt = $tokenResponse.access_token

# Call API with token (expect 200)
Invoke-RestMethod -Uri "https://localhost/<API_PATH>" `
  -Headers @{Authorization="Bearer $jwt"} -SkipCertificateCheck
```

Test without a token (should return 401 Unauthorized):

```powershell
try {
    Invoke-RestMethod -Uri "https://localhost/<API_PATH>" -SkipCertificateCheck
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode) -- expected 401 Unauthorized"
}
```

**Note on PowerShell versions:** The `-SkipCertificateCheck` parameter requires **PowerShell 7+** (`pwsh`). If using **Windows PowerShell 5.1** (`powershell.exe`), use the SSL bypass workaround described in the Keycloak UI Access section.

### Explaining the Bridge

After verifying the integration, explain:
- **Kong JWT plugin** validates the token's signature using the RSA public key and checks the `exp` claim
- The `iss` claim in the Keycloak JWT matches the `key` in the KongConsumer's JWT credential -- this is how Kong finds the right public key
- Any valid Keycloak JWT from the `odari` realm will be accepted, regardless of which Keycloak client issued it
- **No** role-based authorization is enforced at the Kong level -- Kong only verifies the token is valid and not expired
- If the Keycloak RSA key is rotated, the Kong credential must be updated with the new public key
## Generate a Postman Collection

When the user selects this option, generate a Postman collection file that includes requests to obtain a JWT token via **Client Credentials flow** and call the component's ExposedAPI.

### Interactive Workflow

**Step 1: Identify the client and API**

Ask which Keycloak client and ExposedAPI to use:

```bash
kubectl get exposedapis -n components -o json | python <scripts>/parse_exposedapis.py
```

**Step 2: Gather parameters**

Collect:
- **Keycloak URL** (default: `http://localhost:8083/auth/realms/odari`)
- **Client ID** (ask the user or list available clients)
- **Client Secret** (retrieve using the helper script or ask the user)
- **API Base URL** (from the ExposedAPI's `.status.apiStatus.url`)

**Step 3: Generate the collection**

```bash
python <scripts>/generate_postman_collection.py \
  --keycloak-url "http://localhost:8083/auth/realms/odari" \
  --client-id <CLIENT_ID> \
  --client-secret <CLIENT_SECRET> \
  --api-base-url <API_BASE_URL> \
  --api-name "<API_NAME>" \
  --output postman_collection.json
```

The script generates a Postman collection with:

1. **Get JWT Token** -- POST to Keycloak token endpoint using Client Credentials grant. A test script automatically saves the `access_token` to a collection variable.
2. **List Resources** -- GET request to the API's root resource. Uses the `{{access_token}}` variable in the `Authorization: Bearer` header.
3. **Create Resource** -- POST request to create a new resource with a sample body.

**Step 4: Import instructions**

After generating, explain:
1. **Import**: File > Import > select the generated JSON file
2. **SSL**: Go to Settings > General > turn **off** "SSL certificate verification" (Kong uses a self-signed cert on localhost)
3. **Run in order**: Execute "Get JWT Token" first -- the test script auto-saves the token. Then run the API requests.
4. **Token refresh**: The token expires after 300 seconds. Re-run the token request if you get a 401.
5. **Collection Runner**: Use Postman's Collection Runner to execute all requests in sequence.
## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **View IdentityConfig resources** -- List and inspect identity configurations |
| 2 | **View Keycloak UI** -- Open the Keycloak admin console |
| 3 | **Add component roles** -- Define roles through the component (static or dynamic) |
| 4 | **Create a Keycloak client** -- Set up an external client for the Client Credentials flow |
| 5 | **Check Keycloak-Kong JWT integration** -- Verify token validation works end-to-end |
| 6 | **Generate a Postman collection** -- Create authenticated API test collection |
| 7 | **View ExposedAPIs** -- Check API access control settings (apiKeyVerification) |
| 8 | **View deployed components** -- See component status and security configuration |
| 9 | **Return to main menu** |
