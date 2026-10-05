# PDB Management Operator - Complete Demo Presentation Script

## Opening (2 minutes)

### Slide 1: Introduction

**Say:** Good afternoon, and thank you for the invitation. 
My name is Nikos Nikolakakis, and I am the SRE Chapter Lead at Vodafone Greece. 
I have been working in the telecom industry for over 10+ years. 
Today I am here to present the PDB Management Operator, a Kubernetes Operator designed for the ODA Canvas.

**The PDB Management Operator is notable because it is:**
- **The first Go-based operator** in the ODA Canvas ecosystem, all previous operators were written in other languages (Python by using KOPF)
- **The first to use native Kubernetes leader election**, providing true high availability by safely coordinating multiple active operator replicas.
- **The first with enterprise-grade observability**, featuring unified structured logging, OpenTelemetry tracing, and metrics.

For those unfamiliar with Pod Disruption Budgets, they are Kubernetes resources that limit how many pods can be down simultaneously during voluntary disruptions like node maintenance or cluster upgrades. 
Managing these manually across hundreds of deployments is error-prone and time-consuming.

The PDB operator solves this with intelligent, policy-based automation including enforcement modes, maintenance windows, adaptive circuit breaker, and a unified observability system.

As the first Go operator in ODA Canvas, this is a complete redesign of operator architecture. Here is what that means in practice:

- **Adaptive Intelligence**: Circuit breakers that learn and adjust to your cluster's characteristics
- **Zero-Downtime Operations**: Leader election with graceful failover and 30-second shutdown sequences
- **Enterprise Observability**: Unified logging system that solves industry-wide correlation problems
- **Production Resilience**: Three-layer intelligent caching with adaptive performance tuning


### Slide 2: Agenda

**Say:** Here's what we'll cover today:

1. Basic annotation-based PDB creation, the simplest way to get started
2. Component function intelligence, how the operator automatically adjusts availability for security components
3. Policy-based management with three enforcement modes
4. Maintenance windows for scheduled downtime
5. Edge cases and error handling
6. Our comprehensive observability features, including unified logging innovation
7. Performance optimizations with adaptive circuit breakers and three-layer caching
8. High availability with leader election and graceful shutdown
9. Advanced error handling and production resilience

Let’s start with a live demo.

## Demo Setup (3 minutes)

### Terminal Setup

**Say:** "First, let me verify our operator is running properly in the canvas namespace."

**Type:**

```bash
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management
```

**Expected Output:**

```
NAME                                                 READY   STATUS    RESTARTS   AGE
pdb-management-controller-manager-85464cc897-bplcf   1/1     Running   0          5m
pdb-management-controller-manager-85464cc897-k66cf   1/1     Running   0          5m
```

**Say:** "Perfect! The operator is running and ready. Now I'll create a demo namespace and enable debug logging so we can see exactly what the operator is doing."

**Type:**

```bash
kubectl create namespace pdb-demo

kubectl -n canvas set env deployment/pdb-management-controller-manager LOG_LEVEL=debug
```

**Say:** "I'm also going to open a second terminal to monitor the operator logs in real-time. This will help us see the operator's decision-making process."

**In second terminal, type:**

```bash
# Monitor logs with error handling for mixed JSON/text output
kubectl logs -n canvas deployment/pdb-management-controller-manager -f | jq -R 'try fromjson catch .' 2>/dev/null
```

## Section 1: Basic Annotation-Based PDB Creation (8 minutes)

### Understanding the Availability Annotation System

**Say:** "Before we dive into the demos, let me explain our annotation system. The PDB Management Operator uses a simple but powerful annotation-based approach for basic PDB creation:

**The Key Annotation: `oda.tmforum.org/availability-class`**

This single annotation controls automatic PDB creation with predefined availability classes:
- **`mission-critical`**: 90% minAvailable - For services where even minimal disruption is unacceptable
- **`high-availability`**: 75% minAvailable - For critical production services  
- **`standard`**: 50% minAvailable - For typical production workloads
- **`non-critical`**: 20% minAvailable - For batch jobs and non-critical services
- **`custom`**: Requires additional configuration via AvailabilityPolicy CRD

The beauty of this system is its simplicity, just add one annotation to your deployment and the operator handles everything else. The annotation follows ODA Canvas naming conventions with the `oda.tmforum.org/` prefix for consistency across the ecosystem.

**Additional ODA Annotations Supported:**
- **`oda.tmforum.org/component-function`**: Identifies component role (core, security, observability, etc.)
- **`oda.tmforum.org/componentName`**: ODA component name and version
- **`oda.tmforum.org/description`**: Human-readable description for audit logs
- **`oda.tmforum.org/sla-requirement`**: SLA percentage requirement (e.g., "99.9%")
- **`oda.tmforum.org/maintenance-window`**: Deployment-specific maintenance schedule
- **`oda.tmforum.org/override-reason`**: Justification when overriding policies

**Quick Examples:**

```yaml
# Minimal - just availability class
annotations:
  oda.tmforum.org/availability-class: "standard"

# Production service with full context
annotations:
  oda.tmforum.org/availability-class: "high-availability"
  oda.tmforum.org/component-function: "core"
  oda.tmforum.org/componentName: "TMF622-ProductOrdering-v4.0"
  oda.tmforum.org/sla-requirement: "99.95%"

# Batch job with override
annotations:
  oda.tmforum.org/availability-class: "non-critical"
  oda.tmforum.org/override-reason: "Batch processing - runs during off-hours"
```

### Demo 1.1: Standard Availability

**Say:** "Let's start with the simplest use case. We have a standard web application that needs basic availability protection. We just add one annotation to specify the availability class."

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: standard-app
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 4
  selector:
    matchLabels:
      app: standard
  template:
    metadata:
      labels:
        app: standard
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Say:** "Watch the logs - you'll see the operator immediately detect this deployment."

**Point to logs:** "See here? The operator recognized the 'standard' availability class and is creating a PDB with 50% minAvailable. Let's verify"

**Type:**

```bash
kubectl get pdb -n pdb-demo standard-app-pdb -o yaml | grep -A2 spec:
```

**Expected Output:**

```yaml
spec:
  minAvailable: 50%
  selector:
```

**Say:** "Perfect! The PDB ensures at least 2 of our 4 pods (50%) must remain available during any voluntary disruption. This prevents accidental service outages during maintenance."

### Demo 1.2: High Availability

**Say:** "Now let's deploy a more critical service - perhaps our payment processing system. This needs higher availability."

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-gateway
  namespace: pdb-demo
  labels:
    app.kubernetes.io/name: payment-gateway
    app.kubernetes.io/component: payment
    environment: production
    tier: critical
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
    oda.tmforum.org/component-function: "core"
    oda.tmforum.org/componentName: "PaymentGateway-v4.2.1"
    oda.tmforum.org/description: "Critical payment processing service - handles all customer transactions"
    oda.tmforum.org/sla-requirement: "99.9%"
spec:
  replicas: 8
  selector:
    matchLabels:
      app: payment-gateway
  template:
    metadata:
      labels:
        app: payment-gateway
        version: v4.2.1
    spec:
      containers:
      - name: payment-gateway
        image: nginx:alpine
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
EOF
```

**Say:** "Notice the comprehensive labeling and annotation strategy. The 'oda.tmforum.org' prefix follows ODA Canvas conventions, and I've included component versioning, SLA requirements, and detailed descriptions. All of this appears in our audit logs."

**Type:**

```bash
kubectl get pdb -n pdb-demo payment-gateway-pdb -o yaml | grep minAvailable
```

**Expected Output:**

```yaml
minAvailable: 75%
```

**Say:** "Excellent - 75% availability. With 8 replicas, at least 6 pods must remain running. This gives us higher protection for critical services."

### Demo 1.3: Mission Critical

**Say:** "For our most critical services - like authentication or real-time trading - we can use mission-critical class:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"
spec:
  replicas: 10
  selector:
    matchLabels:
      app: auth
  template:
    metadata:
      labels:
        app: auth
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Type:**

```bash
kubectl get pdb -n pdb-demo auth-service-pdb -o yaml | grep minAvailable
```

**Expected Output:**

```yaml
minAvailable: 90%
```

**Say:** "90% availability - only 1 pod can be disrupted at a time. This provides maximum protection for services where even brief outages are unacceptable."

## Section 2: Component Function Intelligence (5 minutes)

### Demo 2.1: Security Component Auto-Upgrade

**Say:** "Here's where our operator gets smart. Security components are critical for compliance, so the operator automatically upgrades their availability class. Watch this:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: pdb-demo
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/component: authentication
    security-tier: critical
  annotations:
    oda.tmforum.org/availability-class: "standard"  # Note: will be auto-upgraded
    oda.tmforum.org/component-function: "security"
    oda.tmforum.org/componentName: "TMF669-PartyRole-OAuth2Proxy"
    oda.tmforum.org/description: "OAuth2 authentication proxy for all API access"
    oda.tmforum.org/compliance-required: "GDPR,SOX,PCI-DSS"
    security.oda.tmforum.org/auth-provider: "Azure-AD"
spec:
  replicas: 6
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
        security-component: "true"
    spec:
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:latest
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        env:
        - name: OAUTH2_PROXY_PROVIDER
          value: "azure"
EOF
```

**Say:** "I specified 'standard' availability, but watch the logs..."

**Point to logs:** "See this? 'Upgrading availability class for security component'. The operator recognized this is a security component and automatically upgraded it from standard (50%) to high-availability (75%)."

**Type:**

```bash
kubectl get pdb -n pdb-demo oauth2-proxy-pdb -o yaml | grep minAvailable
```

**Expected Output:**

```yaml
minAvailable: 75%
```

**Say:** "This intelligence prevents configuration mistakes. Even if a developer forgets to set high availability for security components, the operator ensures compliance automatically."

## Section 3: Policy-Based Management (15 minutes)

### Understanding the AvailabilityPolicy CRD

**Say:** "Annotations are great for simple cases, but for enterprise environments, we need policies. Let me explain our AvailabilityPolicy Custom Resource Definition (CRD):

**The AvailabilityPolicy CRD** provides enterprise-grade policy management with these key features:

**Core Fields:**
- **`availabilityClass`**: Same classes as annotations (mission-critical, high-availability, standard, non-critical, custom)
- **`componentSelector`**: Advanced selection using namespaces, labels, and label expressions
- **`enforcement`**: Three modes - advisory, flexible, or strict
- **`priority`**: Numeric value for conflict resolution (higher wins)

**Advanced Features:**
- **`customPDBConfig`**: Define custom PDB parameters for the 'custom' class
- **`maintenanceWindows`**: Schedule automatic PDB suspension
- **`minimumClass`**: Set floor for flexible enforcement
- **`allowOverride`**: Control whether annotations can override policy
- **`overrideRequiresReason`**: Require justification for overrides

The CRD enables sophisticated scenarios like:
- Organization-wide compliance policies
- Environment-specific rules (dev/staging/prod)
- Time-based maintenance windows
- Multi-criteria component selection
- Policy inheritance and precedence

This is how large organizations can manage PDB policies at scale while maintaining flexibility for individual teams."

### Demo 3.1: Creating an AvailabilityPolicy

**Say:** "Now let me show you how to create and use an AvailabilityPolicy:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: frontend-policy
  namespace: canvas
spec:
  availabilityClass: high-availability
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      tier: frontend
  priority: 100
  enforcement: advisory  # Default - we'll explore this
EOF
```

**Say:** "This policy says: any deployment in pdb-demo namespace with label 'tier: frontend' should have high availability. The priority field helps when multiple policies match."

**Type:**

```bash
kubectl get availabilitypolicy -n canvas
```

### Demo 3.2: Policy Application

**Say:** "Now let's deploy a frontend service WITHOUT any availability annotations:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-service
  namespace: pdb-demo
  labels:
    tier: frontend  # This matches our policy
spec:
  replicas: 4
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Say:** "Watch the logs - the operator will detect this matches our policy..."

**Point to logs:** "There! 'Applying policy frontend-policy'. Even though we didn't add any annotations, the PDB was created based on the policy."

**Type:**

```bash
kubectl get pdb -n pdb-demo frontend-service-pdb -o yaml | grep minAvailable
```

**Expected Output:**

```yaml
minAvailable: 75%
```

## Section 4: Enforcement Modes (12 minutes)

### Demo 4.1: Strict Enforcement

**Say:** "Now let's explore enforcement modes. This is crucial for compliance scenarios. Strict mode means the policy ALWAYS wins, even if developers try to override with annotations."

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: production-strict
  namespace: canvas
spec:
  availabilityClass: mission-critical
  enforcement: strict  # Policy always wins
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      env: production
  priority: 200
EOF
```

**Say:** "Now watch what happens when a developer tries to deploy a production service with lower availability:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-app
  namespace: pdb-demo
  labels:
    env: production
  annotations:
    oda.tmforum.org/availability-class: "standard"  # Developer wants 50%
spec:
  replicas: 10
  selector:
    matchLabels:
      app: prod
  template:
    metadata:
      labels:
        app: prod
        env: production
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Say:** "The developer annotated this with 'standard' availability, but watch..."

**Point to logs:** "See this warning? 'Annotation override blocked by strict policy'. The operator is enforcing the policy's mission-critical setting."

**Type:**

```bash
kubectl get pdb -n pdb-demo production-app-pdb -o yaml | grep minAvailable
kubectl get events -n pdb-demo | grep PolicyEnforced | tail -1
```

**Expected Output:**

```yaml
minAvailable: 90%
```

**Say:** "90% availability, not the 50% the developer requested. This ensures production services always meet compliance requirements, regardless of configuration mistakes."

### Demo 4.2: Flexible Enforcement

**Say:** "Flexible mode is more specific, it allows teams to choose HIGHER availability but prevents them from going lower than a minimum threshold."

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: backend-flexible
  namespace: canvas
spec:
  availabilityClass: high-availability  # Default is 75%
  enforcement: flexible
  minimumClass: standard  # But allow nothing less than 50%
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      tier: backend
  priority: 150
EOF
```

**Say:** "Let's test with a backend service that wants mission-critical availability:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-critical
  namespace: pdb-demo
  labels:
    tier: backend
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"  # Higher than policy
spec:
  replicas: 8
  selector:
    matchLabels:
      app: backend-critical
  template:
    metadata:
      labels:
        app: backend-critical
        tier: backend
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Type:**

```bash
kubectl get pdb -n pdb-demo backend-critical-pdb -o yaml | grep minAvailable
```

**Expected Output:**

```yaml
minAvailable: 90%
```

**Say:** "Perfect - 90% was accepted because it's higher than the policy's 75%. Now let's try going lower:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-batch
  namespace: pdb-demo
  labels:
    tier: backend
  annotations:
    oda.tmforum.org/availability-class: "non-critical"  # Only 20%
spec:
  replicas: 6
  selector:
    matchLabels:
      app: backend-batch
  template:
    metadata:
      labels:
        app: backend-batch
        tier: backend
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Point to logs:** "See the warning? 'Annotation non-critical below minimum standard'. The operator rejected the low availability and applied the policy's default."

**Type:**

```bash
kubectl get pdb -n pdb-demo backend-batch-pdb -o yaml | grep minAvailable
kubectl get events -n pdb-demo | grep BelowMinimum | tail -1
```

**Expected Output:**

```yaml
minAvailable: 75%
```

**Say:** "75% - the policy's default. This gives teams flexibility to increase protection while preventing accidental under-provisioning."

### Demo 4.3: Advisory Enforcement

**Say:** "Advisory mode it respects developer choices but requires them to document their reasoning:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: default-advisory
  namespace: canvas
spec:
  availabilityClass: standard
  enforcement: advisory
  allowOverride: true
  overrideRequiresReason: true
  overrideRequiresAnnotation: "oda.tmforum.org/override-reason"
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      tier: web
  priority: 50
EOF
```

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
  namespace: pdb-demo
  labels:
    tier: web
  annotations:
    oda.tmforum.org/availability-class: "non-critical"
    oda.tmforum.org/override-reason: "Batch job - runs during off-hours"
spec:
  replicas: 5
  selector:
    matchLabels:
      app: batch
  template:
    metadata:
      labels:
        app: batch
        tier: web
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Say:** "Because we provided a reason, the override is accepted:"

**Type:**

```bash
kubectl get pdb -n pdb-demo batch-processor-pdb -o yaml | grep minAvailable
kubectl get events -n pdb-demo | grep AnnotationAccepted | tail -1
```

**Expected Output:**

```yaml
minAvailable: 20%
```

**Say:** "This mode is perfect for teams that need freedom but want to maintain an audit trail of decisions."

## Section 5: Maintenance Windows (8 minutes)

### Demo 5.1: Deployment-Level Maintenance

**Say:** "Let's talk about maintenance windows. Sometimes you need to suspend PDB protection for maintenance. Here's how:"

**Type:**

```bash
# First, let's create a deployment with a maintenance window in 1 minute
CURRENT_TIME=$(date +%H:%M)
WINDOW_START=$(date -v+1M +%H:%M 2>/dev/null || date -d "+1 minute" +%H:%M)
WINDOW_END=$(date -v+5M +%H:%M 2>/dev/null || date -d "+5 minutes" +%H:%M)

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintenance-demo
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
    oda.tmforum.org/maintenance-window: "${WINDOW_START}-${WINDOW_END} UTC"
spec:
  replicas: 6
  selector:
    matchLabels:
      app: maintenance
  template:
    metadata:
      labels:
        app: maintenance
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Say:** "I've set a maintenance window starting in 1 minute. Let's watch what happens. First, the PDB is created normally:"

**Type:**

```bash
kubectl get pdb -n pdb-demo maintenance-demo-pdb -o yaml | grep minAvailable
```

**Say:** "Now let's wait for the maintenance window to start..."

**Wait 1 minute, then type:**

```bash
# Check logs for maintenance activation
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=20 | jq 'select(.msg | contains("maintenance"))'

# Check PDB status
kubectl get pdb -n pdb-demo maintenance-demo-pdb -o yaml | grep -A5 metadata:
```

**Say:** "See the maintenance-mode annotation? During this window, the PDB enforcement is relaxed to allow necessary maintenance operations."

### Demo 5.2: Policy-Level Maintenance Windows

**Say:** "You can also define maintenance windows at the policy level, affecting all matching deployments:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: weekend-maintenance
  namespace: canvas
spec:
  availabilityClass: mission-critical
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      maintenance: scheduled
  maintenanceWindows:
  - start: "02:00"
    end: "04:00"
    timezone: "UTC"
    daysOfWeek: [0, 6]  # Sunday and Saturday
  priority: 100
EOF
```

**Say:** "This policy automatically suspends PDB enforcement every weekend from 2-4 AM UTC. Perfect for scheduled maintenance windows."

## Section 6: Edge Cases and Error Handling (10 minutes)

### Demo 6.1: Policy Conflict Resolution

**Say:** "What happens when multiple policies match the same deployment? The operator uses a priority-based resolution system. Let me demonstrate:"

**Type:**

```bash
# Apply two conflicting policies for security services
kubectl apply -f security/19-security-policies-conflict.yaml

# Show both policies
kubectl get availabilitypolicy -n canvas | grep security-policy
```

**Say:** "We have two policies that both match deployments with label 'security-tier: critical':
- security-policy-high: priority 500, flexible enforcement, high-availability
- security-policy-mission: priority 800, strict enforcement, mission-critical

Let's deploy a security service and see which policy wins:"

**Type:**

```bash
kubectl apply -f services/20-security-service.yaml

# Check logs to see policy selection
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=50 | grep -E "security-service.*(Found matching|priority)"
```

**Point to logs:** "Notice 'Found matching AvailabilityPolicy' shows 'security-policy-mission' with priority 800. The highest priority policy always wins!"

**Type:**

```bash
# Verify the PDB configuration
kubectl get pdb -n pdb-demo security-service-pdb -o yaml | grep -E "(minAvailable|annotations)" -A3
```

**Expected Output:**
```yaml
annotations:
  oda.tmforum.org/policy-source: security-policy-mission
  oda.tmforum.org/enforcement: strict
spec:
  minAvailable: 90%
```

**Say:** "The PDB shows 90% (mission-critical) and references the winning policy. The priority system ensures predictable outcomes when policies overlap."

### Demo 6.2: Policy vs Annotation Conflicts

**Say:** "Now let's see what happens when a deployment annotation conflicts with a policy. The resolution depends on the enforcement mode:"

**Type:**

```bash
# Try to override with annotation on a strict policy deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-override-test
  namespace: pdb-demo
  labels:
    security-tier: critical
  annotations:
    oda.tmforum.org/availability-class: "standard"  # Trying to use lower availability
spec:
  replicas: 8
  selector:
    matchLabels:
      app: security-override
  template:
    metadata:
      labels:
        app: security-override
        security-tier: critical
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Point to logs:** "Watch the logs for 'PolicyEnforced' event:"

**Type:**

```bash
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=20 | grep -E "security-override.*PolicyEnforced"
kubectl get events -n pdb-demo | grep PolicyEnforced | tail -1
```

**Expected Output:**
```
Warning  PolicyEnforced  Annotation override blocked by strict policy security-policy-mission
```

**Say:** "The strict enforcement blocked the annotation override. The PDB uses the policy's mission-critical setting:"

**Type:**

```bash
kubectl get pdb -n pdb-demo security-override-test-pdb -o jsonpath='{.spec.minAvailable}'
```

**Expected Output:**
```
90%
```

**Say:** "This is how strict enforcement protects critical services from accidental downgrades."

### Demo 6.3: Priority Resolution Rules

**Say:** "Let me explain the complete conflict resolution hierarchy:"

**Type:**

```bash
# Create a visual demonstration with multiple policies
cat <<EOF
=== Policy Conflict Resolution Rules ===

1. PRIORITY (highest priority wins)
   - Policy A: priority 100
   - Policy B: priority 500  ← WINS
   - Policy C: priority 200

2. ENFORCEMENT MODE (when policy wins)
   Strict:   Policy always wins, annotations ignored
   Flexible: Annotations allowed if >= minimum class
   Advisory: Annotations allowed with reason

3. RESOLUTION FLOW
   Step 1: Find all matching policies
   Step 2: Select highest priority policy
   Step 3: Apply enforcement rules
   Step 4: Create PDB with resolved config

4. ANNOTATION CONFLICTS
   - No Policy: Annotation wins
   - Strict Policy: Policy wins
   - Flexible Policy: Higher of (annotation, minimum) wins
   - Advisory Policy: Annotation wins if reason provided
EOF
```

**Say:** "The operator logs every decision for full auditability. Let's clean up and look at one more edge case:"

**Type:**

```bash
# Clean up test deployments
kubectl delete deployment security-override-test -n pdb-demo
```

### Demo 6.4: Single Replica Handling

**Say:** "The operator is smart about edge cases. For example, single-replica deployments don't get PDBs because they can't maintain availability during disruptions anyway:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: single-replica
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"
spec:
  replicas: 1  # Only one replica
  selector:
    matchLabels:
      app: single
  template:
    metadata:
      labels:
        app: single
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Point to logs:** "See? 'Single replica, no PDB required'. The operator recognizes this edge case."

**Type:**

```bash
kubectl get pdb -n pdb-demo single-replica-pdb 2>&1 | grep -i "not found"
kubectl get events -n pdb-demo | grep SingleReplica | tail -1
```

**Say:** "No PDB was created, and we have an event explaining why. This prevents invalid PDB configurations."

### Demo 6.5: Deployment Deletion and Cleanup

**Say:** "The operator also handles cleanup properly. Let me create and then delete a deployment:"

**Type:**

```bash
# Create deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temp-deployment
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: temp
  template:
    metadata:
      labels:
        app: temp
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF

# Verify PDB exists
kubectl get pdb -n pdb-demo temp-deployment-pdb
```

**Say:** "PDB created. Now let's delete the deployment:"

**Type:**

```bash
kubectl delete deployment temp-deployment -n pdb-demo
```

**Point to logs:** "Watch the logs, you'll see 'Deployment is being deleted' followed by 'Deleting PDB'."

**Type:**

```bash
kubectl get pdb -n pdb-demo temp-deployment-pdb 2>&1 | grep -i "not found"
```

**Say:** "Perfect! The PDB was automatically cleaned up. No orphaned resources."

### Demo 6.6: Invalid Configuration Handling

**Say:** "Let's see how the operator handles invalid configurations:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invalid-class
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "super-critical"  # Not a valid class
spec:
  replicas: 3
  selector:
    matchLabels:
      app: invalid
  template:
    metadata:
      labels:
        app: invalid
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
```

**Point to logs:** "See the error? 'Invalid availability class: super-critical'."

**Type:**

```bash
kubectl get events -n pdb-demo --field-selector involvedObject.name=invalid-class
kubectl get pdb -n pdb-demo invalid-class-pdb 2>&1 | grep -i "not found"
```

**Say:** "The operator generated a warning event but didn't crash. It gracefully handled the error and continued processing other deployments."

### Demo 6.7: Webhook Validation

**Say:** "For policies, we have admission webhooks that prevent invalid configurations from being created:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: invalid-policy
  namespace: pdb-demo
spec:
  availabilityClass: custom  # Custom requires customPDBConfig
  componentSelector:
    namespaces: ["pdb-demo"]
  # Missing required customPDBConfig!
EOF
```

**Expected Output:**

```
error validating data: ValidationError(AvailabilityPolicy.spec): missing required field "customPDBConfig"
```

**Say:** "The webhook rejected this because custom availability class requires a customPDBConfig. This prevents misconfigurations at creation time."

## Section 7: Observability Features (10 minutes)

### Demo 7.1: Metrics

**Say:** "Now let's look at our comprehensive observability features. First, Prometheus metrics:"

**In a new terminal, type:**

```bash
kubectl port-forward -n canvas deployment/pdb-management-controller-manager 8443:8443
```

**In main terminal, type:**

```bash
# Get all operator metrics
curl -s http://localhost:8443/metrics | grep pdb_management | head -20
```

**Say:** "We expose detailed metrics for:

- Reconciliation duration and errors
- PDB creation counts by namespace and class
- Policy enforcement decisions
- Cache performance
- Circuit breaker state

Let me show you cache performance after all our demos:"

**Type:**

```bash
curl -s http://localhost:8443/metrics | grep -E "cache_(hits|misses|size)"
```

**Say:** "High cache hit rate means the operator is performing efficiently even with many deployments."

### Demo 7.2: Unified Structured Logging Innovation

**Say:** "This operator features a completely unified structured logging system, another industry first. Every log entry has a consistent structure with zero field duplication, a common problem that plagues most operators:"

**Type:**

```bash
# Show structured log entry from unified logging system
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=5 | jq -R 'try fromjson catch .' | head -30
```

**Say:** "Notice our unified structure - every log entry contains exactly these fields:
- **level, ts, msg**: Standard structured fields
- **controller**: Type, name, group, kind - full controller context
- **resource**: Type, name, namespace - complete resource identification
- **reconcileID**: Unique identifier for this specific reconciliation
- **correlationID**: Business correlation for request tracking across systems
- **trace**: OpenTelemetry trace_id and span_id for distributed tracing
- **details**: Context-specific information without field duplication

This was engineered to solve the common problem of duplicate fields and inconsistent logging formats. Let's see a complete trace correlation:"

**Type:**

```bash
# Extract a trace ID and follow the complete flow
TRACE_ID=$(kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -r 'select(.trace.trace_id) | .trace.trace_id' | head -1)

echo "Following trace: $TRACE_ID"

kubectl logs -n canvas deployment/pdb-management-controller-manager | \
  jq -R 'try fromjson catch .' | jq --arg trace "$TRACE_ID" \
  'select(.trace.trace_id == $trace)' | head -10
```

**Say:** "This unified system makes log correlation across distributed systems much more reliable and enables sophisticated debugging workflows."

### Demo 7.3: Audit Trail

**Say:** "For compliance, we maintain a complete audit trail of all decisions:"

**Type:**

```bash
kubectl logs -n canvas deployment/pdb-management-controller-manager | \
  jq 'select(.msg == "Audit log")' | jq '.details' | head -20
```

**Say:** "Every PDB creation, policy decision, and enforcement action is audited with:

- Action performed
- Result (success/failure)
- Duration
- Complete context

This is invaluable for compliance reporting and troubleshooting."

### Demo 7.4: Events

**Say:** "We also generate Kubernetes events for important actions:"

**Type:**

```bash
kubectl get events -n pdb-demo --sort-by='.lastTimestamp' | tail -20
```

**Say:** "Events provide a user-friendly view of what the operator is doing, perfect for kubectl users who don't have access to operator logs."

## Section 8: Performance and Resilience (8 minutes)

### Demo 8.1: Bulk Operations

**Say:** "Let's test the operator's performance with many deployments:"

**Type:**

```bash
# Create 30 deployments rapidly
for i in {1..30}; do
  kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perf-test-$i
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: perf-$i
  template:
    metadata:
      labels:
        app: perf-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
done
```

**Say:** "I just created 30 deployments. Let's check how quickly they were processed:"

**Type:**

```bash
# Count PDBs created
kubectl get pdb -n pdb-demo | grep perf-test | wc -l

# Check processing time in logs
kubectl logs -n canvas deployment/pdb-management-controller-manager | \
  jq 'select(.msg == "PDB created successfully") | select(.resource.name | startswith("perf-test"))' | \
  jq '.details.durationMs' | tail -10
```

**Say:** "All PDBs created in milliseconds! The operator handles bulk operations efficiently thanks to our caching layer and optimized reconciliation loop."

### Demo 8.2: Adaptive Circuit Breaker System

**Say:** "This isn't just any circuit breaker - it's **adaptive**. The operator learns your cluster's characteristics and adjusts thresholds automatically. It starts conservative and becomes more aggressive as it learns normal behavior patterns:"

**Type:**

```bash
# Check adaptive circuit breaker metrics and configuration
curl -s http://localhost:8443/metrics | grep -E "(circuit_breaker|adaptive)"

# Show the adaptive behavior
kubectl logs -n canvas deployment/pdb-management-controller-manager | \
  jq -R 'try fromjson catch .' | jq 'select(.msg | contains("circuit breaker")) | select(.msg | contains("adaptive"))' | tail -5
```

**Say:** "Notice the adaptive learning:
- **Cluster Profiling**: The breaker learns your cluster's normal response times
- **Dynamic Thresholds**: Failure thresholds adjust based on cluster performance  
- **Per-Operation Isolation**: Separate breakers for create/update/delete operations
- **Recovery Intelligence**: Smarter recovery timing based on learned patterns

This prevents the operator from overwhelming stressed API servers while maximizing throughput during normal operations."

**Type:**

```bash
# Show per-operation circuit breaker states
curl -s http://localhost:8443/metrics | grep circuit_breaker_state | \
  awk '{print $1 ": " $2}' | column -t
```

### Demo 8.3: Leader Election and High Availability

**Say:** "Now let me demonstrate one of our key innovations, this is the first operator in the ODA Canvas ecosystem to implement Kubernetes leader election. This enables true high availability."

**Type:**
```bash
# Show current operator replicas
kubectl get deployment pdb-management-controller-manager -n canvas -o wide

# Check leader election configuration
kubectl get configmap -n canvas | grep leader
kubectl get lease -n canvas | grep pdb-management
```

**Say:** "Let's see the leader election in action by scaling up our operator"

**Type:**
```bash
# Scale to 3 replicas for HA
kubectl scale deployment pdb-management-controller-manager -n canvas --replicas=3

# Watch the pods come up
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management -w
```

**Say:** "With leader election enabled, only one replica actively reconciles resources while others standby. If the leader fails, another replica automatically takes over. Let's check the leader election logs:"

**Type:**
```bash
# Check leader election logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management --tail=50 | grep -i "leader\|election" | head -10
```

**Say:** "This provides zero-downtime operator availability, which is crucial for production environments. The leader election ID 'oda.tmforum.org.pdb-management' ensures proper coordination between replicas."

### Demo 8.4: Graceful Shutdown System

**Say:** "Another major innovation is our custom graceful shutdown system with ordered pre-shutdown hooks. Watch this sophisticated shutdown sequence:"

**Type:**

```bash
# Show current operator pods
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management

# Get one pod name for demonstration
POD_NAME=$(kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management -o jsonpath='{.items[0].metadata.name}')
echo "Demonstrating graceful shutdown with pod: $POD_NAME"

# Trigger graceful shutdown (30-second grace period)
kubectl delete pod $POD_NAME -n canvas --grace-period=30 &

# Watch the graceful shutdown sequence in logs
kubectl logs -n canvas $POD_NAME -f | jq -R 'try fromjson catch .' | \
  jq 'select(.msg | contains("shutdown") or contains("hook") or contains("cache") or contains("metrics"))' &

# Show the ordered sequence
sleep 2
echo "Watch for the ordered shutdown sequence:"
echo "1. Signal received → Pre-shutdown hooks triggered"
echo "2. Metrics flushing → Cache clearing → State saving"  
echo "3. Manager shutdown → 30-second timeout"
```

**Say:** "Notice the sophisticated shutdown orchestration:
- **Signal Handling**: Graceful SIGTERM handling with timeout protection
- **Pre-shutdown Hooks**: Ordered execution of cleanup tasks
- **Resource Cleanup**: Metrics flush, cache clear, state preservation
- **Timeout Protection**: 30-second maximum shutdown time

This ensures zero data loss and clean operator restarts, critical for production environments."

### Demo 8.5: Three-Layer Caching System

**Say:** "Let me demonstrate our sophisticated three-layer caching system - another performance innovation:"

**Type:**

```bash
# Show all cache performance metrics
echo "=== Cache Performance Statistics ==="
curl -s http://localhost:8443/metrics | grep -E "cache_(hits|misses|entries|size)" | \
  sort | awk '{printf "%-50s %s\n", $1, $2}'

# Calculate hit ratios
echo -e "\n=== Cache Hit Ratios ==="
POLICY_HITS=$(curl -s http://localhost:8443/metrics | grep 'pdb_management_cache_hits_total{cache_type="policy"}' | awk '{print $2}')
POLICY_TOTAL=$(curl -s http://localhost:8443/metrics | grep 'pdb_management_cache_requests_total{cache_type="policy"}' | awk '{print $2}')
LIST_HITS=$(curl -s http://localhost:8443/metrics | grep 'pdb_management_cache_hits_total{cache_type="list"}' | awk '{print $2}')
LIST_TOTAL=$(curl -s http://localhost:8443/metrics | grep 'pdb_management_cache_requests_total{cache_type="list"}' | awk '{print $2}')

echo "Policy Cache Hit Ratio: $(echo "scale=2; $POLICY_HITS * 100 / $POLICY_TOTAL" | bc 2>/dev/null || echo "N/A")%"
echo "List Cache Hit Ratio: $(echo "scale=2; $LIST_HITS * 100 / $LIST_TOTAL" | bc 2>/dev/null || echo "N/A")%"
```

**Say:** "Our three-layer caching system provides:

1. **Policy Cache**: Individual policy lookups (5-minute TTL, 100 entries max)
2. **List Cache**: Bulk policy retrievals with optimized filtering  
3. **Maintenance Cache**: Fast maintenance window checks (1-minute TTL)

This architecture achieves >90% cache hit rates in production, dramatically reducing API server load."

### Demo 8.6: Advanced Policy Configuration

**Say:** "Finally, let me show you our sophisticated policy configuration capabilities with a complex real-world scenario:"

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: financial-services-policy
  namespace: canvas
  labels:
    policy-domain: financial-services
    compliance: PCI-DSS
spec:
  availabilityClass: custom
  enforcement: strict  # Financial compliance requires strict enforcement
  customPDBConfig:
    minAvailable: 3  # Absolute quorum for financial services
    unhealthyPodEvictionPolicy: "IfHealthyBudget"
  componentSelector:
    namespaces: ["pdb-demo"]
    matchLabels:
      financial-service: "true"
      compliance-tier: "pci-dss"
    matchExpressions:
      - key: "service-type"
        operator: In
        values: ["payment", "settlement", "risk-engine"]
      - key: "region"
        operator: NotIn
        values: ["dev", "test"]
  maintenanceWindows:
    # Financial markets closed
    - start: "22:00"
      end: "06:00" 
      timezone: "America/New_York"
      daysOfWeek: [5, 6]  # Friday night to Saturday
    - start: "18:00"
      end: "06:00"
      timezone: "America/New_York" 
      daysOfWeek: [0]     # Sunday evening to Monday
  priority: 1000
  enforceMinReplicas: true
  allowOverride: false  # No overrides for financial services
EOF
```

**Type:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-processor
  namespace: pdb-demo
  labels:
    financial-service: "true"
    compliance-tier: "pci-dss"
    service-type: "payment"
    region: "us-east-1"
    app.kubernetes.io/name: payment-processor
  annotations:
    oda.tmforum.org/component-function: "core"
    oda.tmforum.org/componentName: "PaymentProcessor-PCI"
    compliance.oda.tmforum.org/certification: "PCI-DSS-Level-1"
spec:
  replicas: 5
  selector:
    matchLabels:
      app: payment-processor
  template:
    metadata:
      labels:
        app: payment-processor
        financial-service: "true"
    spec:
      containers:
      - name: payment-processor
        image: nginx:alpine  # Placeholder for demo
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: COMPLIANCE_MODE
          value: "PCI_DSS_STRICT"
EOF
```

**Type:**

```bash
kubectl get pdb -n pdb-demo payment-processor-pdb -o yaml | grep -A10 spec:
```

**Expected Output:**

```yaml
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: payment-processor
  unhealthyPodEvictionPolicy: IfHealthyBudget
```

**Say:** "Perfect! This demonstrates enterprise-grade policy sophistication:

- **Absolute Quorum**: 3 pods minimum (not percentage) for financial quorum requirements
- **Compliance Integration**: PCI-DSS labeling and certification tracking  
- **Multi-criteria Selection**: Labels + expressions for precise targeting
- **Market-aware Maintenance**: Maintenance only when financial markets are closed
- **Strict Enforcement**: No annotation overrides allowed for compliance
- **Regional Exclusions**: Automatically excludes dev/test regions

This shows how the operator handles complex real-world enterprise requirements."

## Section 9: Advanced Error Handling and Production Resilience (8 minutes)

### Demo 9.1: Resource Constraint Handling

**Say:** "Let's see how the operator handles resource constraints gracefully:"

**Type:**

```bash
# Create a deployment that exceeds cluster capacity
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-hungry
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"
    oda.tmforum.org/description: "Testing resource constraint handling"
spec:
  replicas: 100  # More than cluster can handle
  selector:
    matchLabels:
      app: resource-test
  template:
    metadata:
      labels:
        app: resource-test
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            memory: "10Gi"  # Intentionally large
            cpu: "8000m"
EOF
```

**Say:** "Watch how the operator handles this intelligently:"

**Type:**

```bash
# Check the PDB creation and warning events
kubectl get pdb -n pdb-demo resource-hungry-pdb -o yaml | grep -A5 spec:

# Check for intelligent warnings
kubectl get events -n pdb-demo --field-selector involvedObject.name=resource-hungry \
  --sort-by='.firstTimestamp' | tail -5
```

**Say:** "The operator creates the PDB but generates intelligent warnings about resource constraints. It doesn't block operations but provides visibility into potential issues."

### Demo 9.2: Policy Conflict Resolution

**Say:** "Now let's demonstrate sophisticated policy conflict resolution:"

**Type:**

```bash
# Create conflicting policies
cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: security-policy-high
  namespace: canvas
spec:
  availabilityClass: high-availability
  enforcement: flexible
  componentSelector:
    matchLabels:
      security-tier: critical
  priority: 500
---
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: security-policy-mission
  namespace: canvas
spec:
  availabilityClass: mission-critical
  enforcement: strict
  componentSelector:
    matchLabels:
      security-tier: critical
  priority: 800  # Higher priority
EOF

# Create a deployment that matches both policies
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-service
  namespace: pdb-demo
  labels:
    security-tier: critical
  annotations:
    oda.tmforum.org/availability-class: "standard"  # Will be overridden
spec:
  replicas: 4
  selector:
    matchLabels:
      app: security-service
  template:
    metadata:
      labels:
        app: security-service
    spec:
      containers:
      - name: security
        image: nginx:alpine
EOF
```

**Say:** "Watch the conflict resolution in the logs and check the result:"

**Type:**

```bash
# Check which policy won
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=20 | \
  jq -R 'try fromjson catch .' | jq 'select(.resource.name == "security-service")'

# Verify the winning policy was applied
kubectl get pdb -n pdb-demo security-service-pdb -o yaml | grep minAvailable
```

**Say:** "The higher priority policy wins (priority 800), and the operator logs the complete decision process for audit purposes."

## Closing and Q&A (5 minutes)

### Summary Slide

**Say:** "Let's recap what we've seen today - this represents a new standard in Kubernetes operator engineering:

**Industry Firsts:**
- **First Go operator in ODA Canvas** - Leading the ecosystem evolution
- **First with leader election** - True high availability with zero-downtime failover
- **Unified structured logging** - Solving industry-wide log correlation problems

**Production Innovations:**
- **Adaptive Circuit Breakers** - Learning system that optimizes based on cluster behavior
- **Three-layer Caching** - Achieving >90% cache hit rates for maximum efficiency  
- **Graceful Shutdown System** - 30-second ordered shutdown with pre-shutdown hooks
- **Enterprise Policy Engine** - Complex multi-criteria selection with compliance integration

**Operational Excellence:**
- **Comprehensive Observability** - Full tracing correlation with zero field duplication
- **Intelligent Automation** - Security component auto-upgrade and maintenance windows
- **Production Resilience** - Circuit breakers, caching, graceful error handling
- **Flexible Enforcement** - Three modes supporting everything from development to financial compliance

This isn't just a PDB manager - it's a showcase of modern operator architecture that scales from small deployments to enterprise financial services with hundreds of critical workloads."

### Q&A Setup

**Say:** "Now I'd love to answer your questions or demonstrate any specific scenarios you're curious about.

For example, I can show you:

- How to troubleshoot when a PDB isn't created
- How to set up monitoring dashboards
- How to integrate with your CI/CD pipeline
- How to migrate from manual PDB management

What would you like to explore?"

### Common Questions and Answers

**Q: "What happens if the operator goes down?"**
**A:** "Great question! PDBs are separate Kubernetes resources. If the operator stops, existing PDBs continue protecting your workloads. You just won't get updates until the operator restarts. Plus, with leader election enabled, we support running multiple operator replicas for HA."

**Q: "How do we monitor policy violations?"**
**A:** "Let me show you..."

```bash
# Show policy enforcement metrics
curl -s http://localhost:8080/metrics | grep enforcement_decisions

# Show events
kubectl get events -n pdb-demo | grep -E "(PolicyEnforced|BelowMinimum)"
```

**Q: "Can we integrate this with our GitOps workflow?"**
**A:** "Absolutely! Both annotations and AvailabilityPolicy resources are declarative and work perfectly with GitOps. You can version control your policies and have them automatically applied through ArgoCD or Flux."

**Q: "What's the performance impact?"**
**A:** "Minimal. The operator uses caching extensively and only reconciles when changes occur. With our circuit breaker and rate limiting, it won't overload your API server even under heavy load. The metrics we saw showed sub-100ms reconciliation times."

**Q: "How do we handle different environments (dev/staging/prod)?"**
**A:** "Great question! You can use namespace-based policies or label selectors. Let me show a quick example..."

```bash
cat <<EOF
# Dev environment - flexible
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: dev-policy
spec:
  availabilityClass: standard
  enforcement: advisory
  componentSelector:
    namespaces: ["dev", "development"]
  priority: 10

---
# Production - strict
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: prod-policy
spec:
  availabilityClass: high-availability
  enforcement: strict
  componentSelector:
    namespaces: ["prod", "production"]
  priority: 100
EOF
```

### Final Cleanup

**Say:** "Let me clean up our demo environment:"

**Type:**

```bash
# Delete demo namespace
kubectl delete namespace pdb-demo

# Reset logging level
kubectl -n canvas set env deployment/pdb-management-controller-manager LOG_LEVEL=info

# Clean up bulk test deployments
for i in {1..30}; do
  kubectl delete deployment perf-test-$i -n pdb-demo 2>/dev/null
done

# Clean up enhanced examples
kubectl delete deployment payment-gateway oauth2-proxy payment-processor -n pdb-demo 2>/dev/null
kubectl delete availabilitypolicy financial-services-policy -n canvas 2>/dev/null

echo "Demo environment cleaned up successfully!"
```

**Say:** "Thank you for your time today! The operator is available at github.com/oda-canvas/pdb-management, and I'm happy to help with adoption in your environment.

Key resources:

- Documentation: docs.oda-canvas.org/pdb-management
- Helm charts: Available in the helm/ directory
- Example configurations: examples/ directory
- Grafana dashboards: config/grafana/

Feel free to reach out with any questions!"

## Appendix: Additional Demo Scenarios

### A1: Multi-Region Configuration

**If asked about multi-region setups:**

```bash
cat <<EOF | kubectl apply -f -
# APAC Policy
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: apac-policy
  namespace: canvas
spec:
  availabilityClass: high-availability
  enforcement: flexible
  minimumClass: standard
  componentSelector:
    matchLabels:
      region: apac
  maintenanceWindows:
  - start: "02:00"
    end: "04:00"
    timezone: "Asia/Singapore"
    daysOfWeek: [0, 6]
  priority: 100

---
# EU Policy (GDPR Compliance)
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: eu-policy
  namespace: canvas
spec:
  availabilityClass: mission-critical
  enforcement: strict  # GDPR requires strict control
  componentSelector:
    matchLabels:
      region: eu
      data-processing: "true"
  maintenanceWindows:
  - start: "03:00"
    end: "05:00"
    timezone: "Europe/London"
    daysOfWeek: [0]
  priority: 200
EOF
```

### A2: Integration with HPA

**If asked about HPA interaction:**

**Say:** "PDBs work alongside HPA (Horizontal Pod Autoscaler). As HPA scales your deployment, the PDB automatically applies to new pods:"

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autoscaling-app
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: autoscale
  template:
    metadata:
      labels:
        app: autoscale
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: 100m
          limits:
            cpu: 200m
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: autoscaling-app
  namespace: pdb-demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: autoscaling-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

**Say:** "The PDB percentage (75%) applies regardless of replica count. If HPA scales to 10 pods, at least 8 must remain available."

### A3: Gradual Rollout Example

**If asked about canary deployments:**

```bash
cat <<EOF | kubectl apply -f -
# Canary - relaxed availability
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "non-critical"
    oda.tmforum.org/override-reason: "Canary deployment - testing phase"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      version: canary
  template:
    metadata:
      labels:
        app: myapp
        version: canary
    spec:
      containers:
      - name: app
        image: myapp:v2.0

---
# Stable - high availability
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
  namespace: pdb-demo
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
spec:
  replicas: 8
  selector:
    matchLabels:
      app: myapp
      version: stable
  template:
    metadata:
      labels:
        app: myapp
        version: stable
    spec:
      containers:
      - name: app
        image: myapp:v1.0
EOF
```

**Say:** "This allows you to test new versions with relaxed availability while maintaining high availability for stable versions."

---

**End of Demo Script**

_Duration: Approximately 60-75 minutes_
_Audience: Platform Engineers, SREs, DevOps Teams_
_Prerequisites: Basic Kubernetes knowledge_
