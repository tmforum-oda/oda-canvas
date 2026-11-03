# AGENTS.md — source/operators/

Kubernetes operators that form the management plane of the ODA Canvas. Each operator manages a specific aspect of the ODA Component lifecycle.

## Operators

Operators are grouped by the TMF operator catalogue (`TMFOPnnn-Name`). Each group has a `README.md` and one
subdirectory per implementation.

| Directory | Implementation(s) | Purpose | Language |
|-----------|-------------------|---------|----------|
| `TMFOP001-Component-Management/` | `component-management/componentOperator.py` | Component lifecycle, decomposition into sub-resources | Python/KOPF |
| `TMFOP002-API-Management/` | `kong/`, `apache-apisix/`, `istio/`, `apigee/`, `azure-apim/`, `whalecloud-apim/` | API Gateway/Service Mesh configuration (one implementation per gateway) | Python/KOPF |
| `TMFOP003-Identity-Config/` | `keycloak/identityConfigOperatorKeycloak.py` | Identity Management Services configuration | Python/KOPF |
| `TMFOP004-Credentials-Management/` | `credentials-management/credentialsManagementOperator.py` | Writes component client credentials into Kubernetes secrets | Python/KOPF |
| `TMFOP005-Dependency-Management/` | `simple-dependency-management/`, `dependency-management-using-keycloak-authorization/` (code in `docker/src/`) | Dependent API discovery (simple, or resolved through Keycloak authorization) | Python/KOPF |
| `TMFOP006-Event-Management/` | README only | Event management | Planned |
| `TMFOP007-Secrets-Management/` | `vault/docker/secretsmanagementOperatorHC.py` (plus a Go sidecar in `vault/sidecar/`) | Secrets management (HashiCorp Vault) | Python/KOPF |
| `TMFOP008-OAuth2-Config/` | `envoy-filter/docker/src/oauth2EnvoyfilterOperator.py` | OAuth2 configuration through an Envoy filter (prototype) | Python/KOPF |
| `TMFOP009-Model-as-a-Service/` | README only | Model-as-a-Service | Planned |
| `TMFOP010-Disruption-Budget-Management/` | `pdb-management/` | Pod Disruption Budget management | **Go/kubebuilder** |
| `TMFOP011-Carbon-Management/` | `carbon-management/src/main.py` | Carbon-aware scaling (KEDA) | Python |

The operators are deployed by Helm charts in `charts/` (for example `component-operator`, `api-operator-istio`,
`identityconfig-operator-keycloak`, `pdb-management-operator`), mostly through the `canvas-oda` umbrella chart.

## Python/KOPF Operator Pattern

### Directory Structure (per operator)

```
TMFOPnnn-<Name>/<implementation>/
  <operatorName>.py          # Main kopf handler file
  log_wrapper.py             # Structured logging helper
  <operator>-dockerfile      # Dockerfile (NOT named "Dockerfile")
  README.md
  sequenceDiagrams/          # PlantUML diagrams
  test/                      # Tests and testdata_* fixtures
```

Newer operators put their code in `docker/src/` with a `docker/Dockerfile` (for example TMFOP005 and
TMFOP008). Follow the layout of the operator you are changing.

### Code Conventions

- Use `kopf` decorators: `@kopf.on.create`, `@kopf.on.update`, `@kopf.on.resume`, `@kopf.on.delete`
- CRD group is always `"oda.tmforum.org"`, version `"v1"`
- Handler functions must be **async** (`async def`)
- Use `kopf.TemporaryError` for retryable errors with `retries=5`
- Use `LogWrapper` from local `log_wrapper.py` for structured logging
- Include comprehensive docstrings with Args/Returns sections
- Configuration via environment variables: `LOGGING`, `COMPONENT_NAMESPACE`, `COMPONENTNAME_LABEL`, `CICD_BUILD_TIME`, `GIT_COMMIT_SHA`

### Example Handler Pattern

```python
@kopf.on.create('oda.tmforum.org', 'v1', 'components', retries=5)
async def component_create(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handle component creation.

    Args:
        meta: Kubernetes object metadata
        spec: Component specification
        ...
    """
    log = LogWrapper(handler_name='component_create', resource_name=name)
    # ... handler logic
```

### API Management — Special Structure

The API management operators have one subdirectory per gateway implementation:

```
TMFOP002-API-Management/
  kong/apiOperatorKong.py                 # also apiOperatorIstiowithKong.py
  apache-apisix/apiOperatorApisix.py      # also apiOperatorIstiowithApisix.py
  istio/apiOperatorIstio.py
  apigee/apiOperatorApigee.py
  azure-apim/apiOperatorAzureAPIM.py
  whalecloud-apim/apiOperatorApig.py
```

Only one API operator is enabled in a Canvas at a time.

## Do

- Follow the existing KOPF handler pattern for new operators
- Put a new operator type in a new `TMFOPnnn-Name/` group (next free number, Title-Case name), with a kebab-case implementation subdirectory (e.g., `TMFOP012-My-Operator/my-implementation/`)
- Include a `log_wrapper.py` in each operator directory
- Name Dockerfiles descriptively: `<operator-name>-dockerfile` (or `docker/Dockerfile` in the newer layout)
- Work on a `feature/*` (or `odaa-*`) branch: only those branch names build the prerelease image the tests pull (see CI in the root `AGENTS.md`)
- Add PlantUML sequence diagrams in a `sequenceDiagrams/` subdirectory
- Write tests that load fixture data from `test/testdata_*` folders

## Don't

- Do not use camelCase for new directory names (legacy inconsistency exists)
- Do not import `log_wrapper` from another operator — each operator has its own copy
- Do not assume all operators are Python — `TMFOP010-Disruption-Budget-Management/pdb-management/` is Go/kubebuilder
- Do not hardcode namespaces — use `COMPONENT_NAMESPACE` environment variable

## Commands

```bash
# Install the shared dependencies (from source/operators/)
pip install -r requirements.txt

# Run an operator locally against the cluster in your kubeconfig (from source/operators/; example: component operator)
cd TMFOP001-Component-Management/component-management
kopf run --namespace=components componentOperator.py

# Run the component operator tests (from source/operators/; they talk to the cluster in your kubeconfig)
cd TMFOP001-Component-Management/component-management/test
pytest componentOperatorTest_DEPAPI.py
```

## Dependencies

Shared Python dependencies are in `requirements.txt` at the operators root: `kopf`, `kubernetes`, `pykube-ng`, `pyyaml`.
