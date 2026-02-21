# Webhook Deployment Guide

## Overview

The PDB Management Operator includes admission webhooks for validating and defaulting AvailabilityPolicy CRDs. This guide explains how to deploy webhooks with proper TLS configuration.

## Prerequisites

1. **cert-manager installed** in the cluster (optional - operator gracefully degrades without it)
2. **Kubernetes 1.21+** (for admissionregistration.k8s.io/v1)
3. **Proper RBAC** for webhook operations

## Graceful Degradation

The operator implements graceful degradation for webhook functionality. If cert-manager is not available or webhook setup fails, the operator continues running without webhook validation:

- **cert-manager not detected**: Operator logs a warning and continues without validation webhooks
- **Webhook setup failure**: Operator logs an error and continues without validation webhooks
- **Webhook status metric**: `pdb_management_webhook_status` tracks the current webhook state

This ensures the core PDB management functionality remains available even if webhook infrastructure is not properly configured.

```bash
# Check webhook status via metrics
curl -s http://localhost:8080/metrics | grep webhook_status
# pdb_management_webhook_status{reason="success",status="enabled"} 1
# OR
# pdb_management_webhook_status{reason="cert_manager_not_found",status="disabled"} 1
```

## Deployment Options

### Option 1: Basic Deployment (No Webhooks)

For development or testing environments where webhook validation is not required:

```bash
# Deploy without webhooks
kubectl apply -k config/default/

# Verify deployment
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management
```

### Option 2: Production Deployment (With Webhooks)

For production environments with proper TLS certificates:

#### Step 1: Install cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
```

#### Step 2: Deploy certificates

```bash
# Deploy certificate configuration
kubectl apply -k config/certmanager/

# Verify certificate creation
kubectl get certificate -n canvas
kubectl describe certificate serving-cert -n canvas
```

#### Step 3: Deploy webhook resources

```bash
# Deploy webhook service and configurations
kubectl apply -k config/webhook/

# Verify webhook configurations
kubectl get validatingwebhookconfiguration
kubectl get mutatingwebhookconfiguration
```

#### Step 4: Deploy operator with webhooks enabled

```bash
# Patch deployment to enable webhooks
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/4", "value": "--enable-webhook=true"}]'

# Restart operator to pick up webhook configuration
kubectl rollout restart deployment controller-manager -n canvas

# Verify webhook is working
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i webhook
```

### Option 3: Development with Self-Signed Certificates

For development environments without cert-manager:

#### Step 1: Generate self-signed certificates

```bash
# Create certificate directory
mkdir -p /tmp/certs

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout /tmp/certs/tls.key -out /tmp/certs/tls.crt -days 365 -nodes -subj "/CN=webhook-service.canvas.svc"

# Create secret
kubectl create secret tls webhook-server-cert -n canvas --cert=/tmp/certs/tls.crt --key=/tmp/certs/tls.key
```

#### Step 2: Deploy with TLS configuration

```bash
# Patch deployment to use TLS certificates
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "add", "path": "/spec/template/spec/volumes/0", "value": {"name": "webhook-certs", "secret": {"secretName": "webhook-server-cert"}}}]'

kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/volumeMounts/0", "value": {"name": "webhook-certs", "mountPath": "/tmp/certs", "readOnly": true}}]'

# Enable webhooks
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/4", "value": "--enable-webhook=true"}]'

# Restart operator
kubectl rollout restart deployment controller-manager -n canvas
```

## Verification

### Test Webhook Functionality

```bash
# Test validation webhook
kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: test-policy
  namespace: canvas
spec:
  availabilityClass: invalid-class  # This should be rejected
  componentSelector:
    namespaces: ["default"]
EOF

# Check for validation error
kubectl get events -n canvas --sort-by='.lastTimestamp' | grep -i "availabilitypolicy"
```

### Check Webhook Status

```bash
# Check webhook configurations
kubectl get validatingwebhookconfiguration availabilitypolicy-validating-webhook-configuration -o yaml

# Check webhook service
kubectl get svc webhook-service -n canvas

# Check certificate status
kubectl get certificate serving-cert -n canvas -o yaml
```

## Troubleshooting

### Common Issues

#### 1. Certificate Not Found

**Error**: `open /tmp/certs/tls.crt: no such file or directory`

**Solution**:

```bash
# Check if certificate secret exists
kubectl get secret webhook-server-cert -n canvas

# If using cert-manager, check certificate status
kubectl describe certificate serving-cert -n canvas

# If certificate is not ready, check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/name=cert-manager
```

#### 2. Webhook Connection Refused

**Error**: `connection refused` when applying CRDs

**Solution**:

```bash
# Check webhook service
kubectl get svc webhook-service -n canvas

# Check webhook endpoints
kubectl get endpoints webhook-service -n canvas

# Check operator logs for webhook errors
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i webhook
```

#### 3. Certificate Validation Failed

**Error**: `x509: certificate signed by unknown authority`

**Solution**:

```bash
# For cert-manager, check if CA is properly injected
kubectl get validatingwebhookconfiguration -o yaml | grep -A5 -B5 "cert-manager.io/inject-ca-from"

# For self-signed certificates, ensure the certificate is properly configured
kubectl get secret webhook-server-cert -n canvas -o yaml
```

### Debug Mode

Enable debug logging for webhook troubleshooting:

```bash
# Enable debug logging
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/2", "value": "--log-level=debug"}]'

# Restart operator
kubectl rollout restart deployment controller-manager -n canvas

# Check debug logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management -f
```

## Security Considerations

### TLS Configuration

The webhook server supports the following TLS configurations:

- **Minimum TLS Version**: 1.2
- **Cipher Suites**: ECDHE-RSA-AES256-GCM-SHA384, ECDHE-RSA-CHACHA20-POLY1305, ECDHE-ECDSA-AES256-GCM-SHA384
- **Certificate Rotation**: Automatic with cert-manager

### Network Policies

Consider implementing network policies to restrict webhook access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: webhook-network-policy
  namespace: canvas
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: pdb-management
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: TCP
          port: 9443
```

## Rollback Procedures

### Disable Webhooks

If webhook issues occur, disable them temporarily:

```bash
# Disable webhooks
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/4", "value": "--enable-webhook=false"}]'

# Delete webhook configurations
kubectl delete validatingwebhookconfiguration availabilitypolicy-validating-webhook-configuration
kubectl delete mutatingwebhookconfiguration availabilitypolicy-mutating-webhook-configuration

# Restart operator
kubectl rollout restart deployment controller-manager -n canvas
```

### Remove Certificates

```bash
# Remove certificate resources
kubectl delete -k config/certmanager/

# Remove webhook resources
kubectl delete -k config/webhook/
```

## Performance Considerations

### Resource Requirements

Webhook servers require additional resources:

```yaml
resources:
  limits:
    memory: "1Gi" # Increased for webhook processing
    cpu: "500m"
  requests:
    memory: "512Mi"
    cpu: "200m"
```

### Concurrency

Webhook servers handle admission requests synchronously. Consider:

- **Timeout**: 10 seconds (configurable)
- **Failure Policy**: Fail (reject invalid requests)
- **Side Effects**: None (no external side effects)

## Monitoring

### Key Metrics

Monitor webhook performance and status:

```bash
# Check webhook status metric
curl -s http://localhost:8080/metrics | grep webhook_status

# Check webhook metrics
curl -k https://localhost:8443/metrics | grep -i webhook

# Check admission request latency
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i "admission"
```

### Webhook Status Metric

The `pdb_management_webhook_status` gauge tracks the current webhook state:

| Status     | Reason                    | Description                          |
| ---------- | ------------------------- | ------------------------------------ |
| `enabled`  | `success`                 | Webhook is running normally          |
| `disabled` | `cert_manager_not_found`  | cert-manager CRDs not detected       |
| `failed`   | `setup_error`             | Webhook setup failed                 |
| `disabled` | `not_enabled`             | Webhook disabled via CLI flag        |

### Alerts

Set up alerts for:

- Webhook certificate expiration
- High admission request latency
- Webhook failures
- Certificate validation errors
- Unexpected webhook status changes (`pdb_management_webhook_status{status!="enabled"} == 1`)
