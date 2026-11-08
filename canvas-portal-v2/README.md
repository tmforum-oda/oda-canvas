# Canvas Portal v2

Canvas Portal v2 is a web portal for managing and observing an ODA Canvas. It has a React + Vite frontend (`frontend/`) and a FastAPI backend (`backend/`) that reads the cluster through the Kubernetes API. Its Helm chart is in `helm/canvas-portal/`.

## Operators page: how operators are discovered

The **Operators** page (`/operators`, backed by `GET /api/operators`) shows one card per Canvas operator. The backend scans the Deployments it can read and decides which ones are operators:

1. **Labels (preferred).** A Deployment that carries the opt-in label `oda.tmforum.org/operator: "true"` or an `oda.tmforum.org/operatorId` label is listed as one operator.
2. **Built-in signatures (fallback).** Otherwise, the backend matches the container names, images and Deployment name against a built-in list of known Canvas operators (`OPERATOR_SIGNATURES` in `backend/k8s/resources/operators.py`). A Deployment that hosts several known operators produces one card per operator.
3. Deployments that match neither are ignored.

Labelled operators therefore appear on the page as soon as they are installed. The portal needs no code change and no rebuild.

### Label contract

All keys go on the Deployment's own `metadata`, not on the Pod template.

| Key | Kind | Meaning |
|---|---|---|
| `oda.tmforum.org/operator` | label | `"true"` (any case) opts the Deployment in. |
| `oda.tmforum.org/operatorName` | label | Display name on the card. Defaults to the Deployment name. |
| `oda.tmforum.org/operatorId` | label | TMF operator ID shown as a badge (for example `TMFOP001`). Also opts the Deployment in. The badge tooltip shows the full TMF name when the portal knows the operator under that ID, else the `operatorName` value. |
| `oda.tmforum.org/operatorContainer` | annotation | Container used for the image and readiness when the Deployment has several containers. Defaults to the container named after the operator or the Deployment, else the first container. |

Label values must be 63 characters or fewer and may contain only letters, digits, `-`, `_` and `.`. Use a slug such as `Acme-Operator` for `operatorName`; the card shows the value as written.

### Example

Add the labels to the operator's Deployment template in its Helm chart:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: acme-operator
  labels:
    oda.tmforum.org/operator: "true"
    oda.tmforum.org/operatorName: Acme-Operator
    oda.tmforum.org/operatorId: TMFOP0xx   # optional badge
  annotations:
    oda.tmforum.org/operatorContainer: acme-operator   # optional
```

To try it on a running operator without changing its chart:

```bash
kubectl label deployment acme-operator -n canvas oda.tmforum.org/operator=true
```

### Notes

- The labels affect only what the portal displays. They grant no privileges, and the backend reads Deployments with its usual credentials.
- The backend first lists Deployments in all namespaces. If it isn't allowed to (403/404), it scans only a built-in list of Canvas namespaces (`CANVAS_OPERATOR_NAMESPACES` in `backend/k8s/resources/operators.py`). An operator in any other namespace then stays hidden until the backend's service account can list Deployments cluster-wide.
- Label discovery covers Deployments only. Operators that run as a StatefulSet or DaemonSet are not listed.
- Operators that share a single Deployment should keep relying on the built-in signatures, because the label path produces one card per Deployment.
- The detail page, pod list and logs work the same way for operators found by either path.

## Backend tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```
