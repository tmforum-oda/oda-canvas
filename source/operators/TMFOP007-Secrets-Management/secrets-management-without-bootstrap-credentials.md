# Secrets management without bootstrap credentials

A component that keeps its secrets in a vault, such as database passwords or API keys for other systems, needs a credential to log in to the vault. That first credential is the **bootstrap credential**, and storing it safely is the hard part: put it in a Kubernetes secret, an environment variable or the image, and anyone who can read that can read every secret behind it.

The Canvas removes the bootstrap credential. Each component pod proves who it is with the token that Kubernetes already gives it, and the Canvas's HashiCorp Vault trusts the cluster to vouch for that token. The component asks the Canvas for a secrets store in its component specification, and reads and writes secrets through a sidecar on `localhost`, with no credential of its own.

This page explains how that works, how to use it in a component, and what to watch out for. The design is in [use case UC014, Secrets Management](../../../usecase-library/UC014-Secrets-Management-JWT-based.md).

## How it works

1. **Kubernetes issues each pod a signed token** (a JWT) that names its namespace, pod and service account. The cluster publishes the keys to check these tokens, as an OpenID Connect issuer.
2. **The Canvas's Vault trusts that issuer.** When the Canvas is installed, the [`canvas-vault`](../../../charts/canvas-vault/README.md) chart installs Vault in the `canvas-vault` namespace and enables a JWT login method at `jwt-k8s-sman`, pointed at the cluster's issuer.
3. **A component asks for secrets management** in `securityFunction.secretsManagement`. The Component Management operator creates a `SecretsManagement` resource, and the Secrets Management operator sets up, for that component only:
   - a key-value store (KV version 2) named `kv-sman-<namespace>-<component>`;
   - a policy that allows create, read, update, delete and patch on secrets in that store, but not listing them;
   - a login role that accepts only tokens whose pod name, namespace and service account match the component's `podSelector`, and gives a Vault token valid for one hour.
4. **The operator injects a sidecar** into each of the component's pods that matches the selector. The sidecar logs in to Vault with the pod's own token, and offers a small secrets API on `localhost`.
5. **The component reads and writes its secrets** through that API. It needs no Vault address, store name or credential.

The Secrets Management operator itself does hold a Vault credential: the Vault root token, which the `canvas-vault` chart stores in the `canvas-vault-hc-secrets` secret. That is a platform credential, managed by the Canvas platform team. Components never see it.

## Use it in a component

### 1. Ask for a secrets store

Add `secretsManagement` to the component's `securityFunction`:

```yaml
apiVersion: oda.tmforum.org/v1
kind: Component
metadata:
  name: demo-productcatalogmanagement
  labels:
    oda.tmforum.org/componentName: demo-productcatalogmanagement
spec:
  securityFunction:
    secretsManagement:
      type: sideCar
      sideCar:
        port: 5000
      podSelector:
        namespace: components
        name: "demo-productcatalogmanagement-*"
        serviceaccount: default
```

- `type` must be `sideCar`, the only type implemented.
- `podSelector` decides which pods can use the store. Each field is a glob pattern, matched against the pod's namespace, name and service account. Leave a field out to match any value. Make `name` match only the pods that need the secrets.
- `sideCar.port` is required, but the sidecar always listens on `127.0.0.1:5000`, so use `5000`.

### 2. Label the deployments that need secrets

Give each Deployment that needs the secrets these two labels:

```yaml
metadata:
  labels:
    oda.tmforum.org/componentName: demo-productcatalogmanagement
    oda.tmforum.org/secretsmanagement: sidecar
```

The operator copies them to the pod template, and its admission webhook adds a container named `smansidecar` to each new pod. If a pod starts before the store is ready, the operator restarts it when the store is set up.

### 3. Read and write secrets

From any container in the pod, call the sidecar on `localhost:5000`. Each secret is a key and a string value:

```bash
# Create or update a secret
curl -X POST localhost:5000/api/v3/secret \
  -H "Content-Type: application/json" \
  -d '{"key": "db-password", "value": "s3cr3t-demo"}'

# Read it
curl localhost:5000/api/v3/secret/db-password
# {"key":"db-password","value":"s3cr3t-demo"}
```

| Request | Does |
|---|---|
| `POST /api/v3/secret` | Creates or updates a secret, from `{"key": ..., "value": ...}` |
| `PUT /api/v3/secret/{key}` | The same as `POST`: the key comes from the body, not the path |
| `GET /api/v3/secret/{key}` | Returns `{"key": ..., "value": ...}`, or 404 if there's no such secret |
| `DELETE /api/v3/secret/{key}` | Deletes a secret. It returns 200 even if the delete fails, with `ERROR 403: forbidden` in the body |

There is no request to list secrets: the policy doesn't allow listing, so a component has to know its secrets' keys.

### Check it

```bash
# The store is set up when READY is true
kubectl get secretsmanagements -n components

# The pod has the sidecar
kubectl get pod <pod> -n components -o jsonpath='{.spec.containers[*].name}'
```

If a pod has no `smansidecar` container, check its labels, and check that its name, namespace and service account match the `podSelector`. A pod that doesn't match starts **without** the sidecar, and no error is shown on the pod. The reason is in the operator's log:

```bash
kubectl logs -n canvas deployment/canvas-smanop --tail=100
```

If a component stays at `In-Progress-SecretMan`, see [A component is stuck at In-Progress](https://tmforum-oda.github.io/oda-ca-docs/docs/TroubleshootingGuide/Component-Stuck-In-Progress.html).

## What was tested

On a local kind Canvas (`canvas-oda` 1.2.6-rc9, Vault 1.14.8, sidecar 0.1.0), with secrets management added to the Product Catalog component:

- the operator created the store, policy and role, and the `SecretsManagement` resource became ready;
- a labelled deployment whose pods matched the selector got the sidecar, and the app container created and read a secret through it;
- a labelled deployment whose pods didn't match got no sidecar, and Vault refused its pod's token: `claim "/kubernetes.io/pod/name" does not match any associated bound claim values`;
- deleting the `SecretsManagement` resource removed the store from Vault.

## Things to know

- **Deleting the component deletes its secrets.** The `SecretsManagement` resource belongs to the component. When it is deleted, the operator disables the component's store, which destroys every secret in it. Back up anything you need to keep before you uninstall.
- **Removing `secretsManagement` from a component doesn't remove the store.** The Component Management operator looks for the resource under the wrong name (`sman_<component>`), so the `SecretsManagement` resource and the store stay. Delete the resource yourself: `kubectl delete secretsmanagement <component> -n <namespace>`.
- **The pod is the security boundary.** Every container in a matching pod can call the sidecar, and can also log in to Vault directly with the pod's token. Anyone who can open a shell in the pod can read its secrets. The optional token negotiation described in UC014, to protect the `localhost` API, isn't implemented.
- **The sidecar logs secret values.** Version 0.1.0 writes each key and value it creates to its log. Restrict who can read the component's pod logs.
- **One selector, full access.** A component has one `podSelector`, and every matching pod can create, read, update and delete all its secrets.
- **Vault's certificate isn't checked.** The operator and the sidecar connect to Vault with `VAULT_SKIP_VERIFY=true`, the chart default.

## Related pages

- [UC014 Secrets Management](../../../usecase-library/UC014-Secrets-Management-JWT-based.md), with the sequence diagram
- [Vault Secrets Management operator](vault/README.md)
- [`canvas-vault` chart](../../../charts/canvas-vault/README.md) and [`secretsmanagement-operator` chart](../../../charts/secretsmanagement-operator/README.md)
- [HashiCorp Vault: use Kubernetes as an OIDC provider](https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes)
