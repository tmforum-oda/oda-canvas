# ODA Component Validation

The Reference Implementation uses Kubernetes Custom Resource Definitions to validate the Components (and sub resources) using Open-API v3 schema validation

## Installation

Install the CRDs (Custom Resource Definitions):

```bash
kubectl apply -f oda-component-crd.yaml
kubectl apply -f oda-api-crd.yaml
```
