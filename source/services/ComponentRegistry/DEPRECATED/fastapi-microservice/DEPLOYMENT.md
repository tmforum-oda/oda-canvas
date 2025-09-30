# Component Registry Service - Kubernetes Deployment

This directory contains the Dockerfile and Helm chart for deploying the ODA Canvas Component Registry microservice to a Kubernetes cluster.

## Structure

```
├── Dockerfile                    # Container image definition
├── helm/
│   └── component-registry/
│       ├── Chart.yaml           # Helm chart metadata
│       ├── values.yaml          # Default configuration values
│       └── templates/
│           ├── _helpers.tpl     # Template helpers
│           ├── deployment.yaml  # Kubernetes Deployment
│           ├── service.yaml     # Kubernetes Service
│           ├── serviceaccount.yaml # Service Account
│           ├── ingress.yaml     # Ingress (optional)
│           ├── hpa.yaml         # Horizontal Pod Autoscaler
│           ├── persistentvolumeclaim.yaml # Storage for SQLite
│           └── NOTES.txt        # Post-installation instructions
```

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t component-registry:latest .
```

### 2. Deploy with Helm

```bash
# Install the chart
helm install component-registry ./helm/component-registry

# Or install with custom values
helm install component-registry ./helm/component-registry -f custom-values.yaml
```

### 3. Access the Service

```bash
# Port forward to access locally
kubectl port-forward svc/component-registry 8080:80

# Access the API
curl http://localhost:8080/health
curl http://localhost:8080/docs  # Swagger UI
```

## Configuration

### Key Configuration Options in values.yaml:

- **image**: Container image configuration
- **replicaCount**: Number of pod replicas
- **service**: Service exposure configuration
- **ingress**: External access configuration
- **persistence**: Storage for SQLite database
- **resources**: CPU/Memory limits and requests
- **autoscaling**: HPA configuration
- **odaCanvas.labels**: ODA Canvas specific labels

### Environment Variables:

- `DATABASE_URL`: Database connection string
- `ENVIRONMENT`: Runtime environment (production/development)

## Production Considerations

1. **Database**: For production, consider using an external PostgreSQL database instead of SQLite
2. **Security**: Review and adjust security contexts and pod security policies
3. **Resources**: Tune resource requests and limits based on your workload
4. **Monitoring**: Add monitoring and alerting for the service
5. **Backup**: Implement backup strategy for persistent data

## ODA Canvas Integration

This chart includes ODA Canvas specific labels and follows TM Forum ODA Canvas deployment patterns:

- Component labeling for Canvas discovery
- Health checks for Canvas monitoring
- Service mesh compatibility
- Security context following Canvas standards

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -l app.kubernetes.io/name=component-registry
```

### View Logs
```bash
kubectl logs -l app.kubernetes.io/name=component-registry
```

### Access Pod Shell
```bash
kubectl exec -it <pod-name> -- /bin/bash
```

## Examples

### Development Deployment
```bash
helm install comp-reg ./helm/component-registry \
  --set image.tag=dev \
  --set replicaCount=1 \
  --set resources.requests.cpu=50m \
  --set resources.requests.memory=64Mi
```

### Production Deployment with Ingress
```bash
helm install comp-reg ./helm/component-registry \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=component-registry.yourdomain.com \
  --set persistence.size=10Gi \
  --set autoscaling.enabled=true
```