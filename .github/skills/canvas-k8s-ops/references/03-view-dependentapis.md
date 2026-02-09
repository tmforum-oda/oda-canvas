# View DependentAPIs

## Table of Contents
- [Focus](#focus)
- [Handling Empty Results](#handling-empty-results)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Presentation](#presentation)

## Focus

DependentAPIs represent API dependencies that a component needs from other components. The key concern is whether dependencies are resolved.

**Important**: DependentAPIs only exist when a component declares them. For example, the `productcatalog` chart requires `--set component.dependentAPIs.enabled=true` at install time. If no DependentAPIs are found, inform the user that either no component has declared dependencies, or the feature was not enabled during deployment.

## Handling Empty Results

If `kubectl get dependentapis -n components` returns "No resources found", check whether any components are deployed:

```bash
kubectl get components -n components
```

### No components deployed

Report: "No DependentAPIs found — no components are deployed yet." Suggest deploying a component first (action 5).

### One or more components deployed, but no DependentAPIs

Report: "No DependentAPIs are currently declared in the components namespace."

Then check whether any deployed component is a **productcatalog**. If so, propose the **Federated Catalog** scenario:

> **Try a Federated Catalog**: Deploy a second Product Catalog instance with dependent APIs enabled. The second instance declares a dependency on the downstream Product Catalog Management API exposed by the first instance. The Canvas dependency operator will automatically discover and resolve this dependency, demonstrating cross-component API wiring.
>
> **Important**: Use a short release name (max 5 characters, e.g., `pc2`). Kubernetes port names must be 15 characters or fewer, and ODA component charts derive port names by combining the release name with internal suffixes. Long names like `prodcat2` or `prodinv` cause deployment failures.
>
> ```bash
> helm install pc2 oda-components/productcatalog -n components \
>   --set component.dependentAPIs.enabled=true
> ```
>
> Once deployed, repeat this action to see the DependentAPIs and their resolution status.

If the deployed component is not a productcatalog, suggest the general approach:
- Upgrade the existing release with `--set component.dependentAPIs.enabled=true`
- Or deploy a second component that declares dependencies

## Commands

```bash
# Summary table
kubectl get dependentapis -n components

# Structured summary with resolution status using helper script
kubectl get dependentapis -n components -o json | python <scripts>/parse_dependentapis.py

# Detail for a specific DependentAPI
kubectl describe dependentapi <name> -n components
```

## Key Fields

| Field | JSON Path | Description |
|-------|-----------|-------------|
| Name | `.metadata.name` | DependentAPI resource name |
| Namespace | `.metadata.namespace` | Namespace |
| Parent Component | `.metadata.ownerReferences[0].name` | Owning Component |
| API Name | `.spec.name` | Name of the API dependency |
| API Type | `.spec.apitype` | e.g., `openapi` |
| Version | `.spec.version` | Required API version |
| Ready | `.status.ready` | Boolean, is the dependency resolved |
| Resolved URL | `.status.url` | URL of the resolved upstream API |

## Presentation

Present DependentAPIs grouped by resolution status:
- **Resolved** (ready=true): Show name, resolved URL, parent component
- **Unresolved** (ready=false or no status): Highlight these prominently — they indicate missing upstream components

Offer to show full spec and status for any specific DependentAPI.

## Federated Catalog Example

When two `productcatalog` instances are deployed (e.g., `prodcat` and `pc2`) and the second has `component.dependentAPIs.enabled=true`, the DependentAPI output will show:

- **productcatalogmanagement** dependency (openapi, v4) — resolved against the first instance's ExposedAPI URL

This demonstrates the Canvas dependency operator automatically discovering and linking a downstream Product Catalog Management API. Highlight the resolved URL and explain that the second catalog can now federate queries to the first.

If the dependency shows as **unresolved**, suggest:
1. Check that the first component is fully deployed (`Complete` status)
2. Verify the ExposedAPI exists: `kubectl get exposedapis -n components`
3. Check dependency operator logs: `kubectl logs -l app=oda-controller-dependentapi -n canvas --tail=50`
