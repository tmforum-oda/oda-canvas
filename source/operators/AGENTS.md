# AGENTS.md — source/operators/

Kubernetes operators that form the management plane of the ODA Canvas. Each operator manages a specific aspect of the ODA Component lifecycle.

## Operators

| Directory | Purpose | Language |
|-----------|---------|----------|
| `component-management/` | Component lifecycle, decomposition into sub-resources | Python/KOPF |
| `api-management/` | API Gateway/Service Mesh configuration (multiple gateway variants) | Python/KOPF |
| `identity-config/` | Identity Management Services configuration | Python/KOPF |
| `credentials-management/` | Credential management | Python/KOPF |
| `dependentApiSimpleOperator/` | Dependent API discovery | Python/KOPF |
| `secretsmanagementOperator-hc/` | Secrets management (HashiCorp) | Python/KOPF |
| `pdb-management/` | Pod Disruption Budget management | **Go/kubebuilder** |

## Python/KOPF Operator Pattern

### Directory Structure (per operator)

```
<operator-name>/
  <operatorName>.py          # Main kopf handler file
  log_wrapper.py             # Structured logging helper
  <operator>-dockerfile      # Dockerfile (NOT named "Dockerfile")
  README.md
  sequenceDiagrams/          # PlantUML diagrams
  test/                      # Tests with testdata/ subdirectory
```

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

The API management operator has subdirectories per gateway implementation:

```
api-management/
  kong/apiOperatorKong.py
  apache-apisix/apiOperatorApisix.py
  istio/
  apigee/
  azure-apim/
  whalecloud-apim/
```

## Do

- Follow the existing KOPF handler pattern for new operators
- Use kebab-case for new operator directory names (e.g., `my-new-operator/`)
- Include a `log_wrapper.py` in each operator directory
- Name Dockerfiles descriptively: `<operator-name>-dockerfile`
- Add PlantUML sequence diagrams in a `sequenceDiagrams/` subdirectory
- Write tests that load fixture data from `test/testdata/`

## Don't

- Do not use camelCase for new directory names (legacy inconsistency exists)
- Do not import `log_wrapper` from another operator — each operator has its own copy
- Do not assume all operators are Python — `pdb-management/` is Go/kubebuilder
- Do not hardcode namespaces — use `COMPONENT_NAMESPACE` environment variable

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run an operator locally (example: component operator)
cd component-management
python componentOperator.py

# Run tests
cd component-management/test
pytest
```

## Dependencies

Shared Python dependencies are in `requirements.txt` at the operators root: `kopf`, `kubernetes`, `pykube-ng`, `pyyaml`.
