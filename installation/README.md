﻿
# ODA Canvas installation

The Reference Implementation of the ODA Canvas is a set of Helm charts that can be used to install and configure a fully working Canvas. The Reference Implementation is built on top of Kubernetes and Istio.

## Software Versions

For each release, we will support a min and max Kubernetes version.

| ODA Component version | Min Kubernetes version | Max Kubernetes version |
| --------------------- | ---------------------- | ---------------------- |
| v1alpha4              | 1.20                   | 1.22                   |
| v1beta1               | 1.22                   | 1.25                   |
| v1beta2               | 1.22                   | 1.27                   |
| v1beta3               | 1.22                   | 1.29                   |

If you are connected to an ODA Canvas, to test what version of Canvas it is, use the command:

```bash
kubectl get crd components.oda.tmforum.org -o jsonpath='{.spec.versions[?(@.served==true)].name}'
```

It will return the versions of components the canvas supports. A canvas should support N-2 versions of a component i.e. for the `v1beta3` canvas, it will support components that are v1beta3, v1beta2, v1beta1 (and v1alpha4 with a deprecation warning).

We will test the Reference Implementation Canvas against a range of kubernetes versions and on a number of different deployments.

| Kubernetes deployment | Tested | Notes                                                                                                                     |
| --------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------- |
| AWS EKS | yes | EKS 1.29
| Rancher on AWS        | Yes    | [Open Digital Lab environment]                                                                                            |
| Azure AKS             | Yes    |                                                                                                                           |
| GCP GKE               | Yes    | [Innovation Hub environment]                                                                                              |
| Microk8s              | Yes    |                                                                                                                           |
| MiniKube              | Yes    |                                                                                                                           |
| Docker Desktop        | Yes    | see also [devcontainer.md](../devcontainer.md)                                                                            |
| Kind                  |        | Using [Canvas-in-a-bottle](canvas-in-a-bottle/README.md)                                                                  |
| K3s                   | Yes    |                                                                                                                           |
| (other)               |        | To suggest additional environments please add to this [issue](https://github.com/tmforum-oda/oda-canvas-charts/issues/52) |

The environment where the chart has been tested has the following
| Software | Version |
| -------- | ------- |
| Istio    | 1.16.1  |
| Helm     | 3.10    |

The helm chart installs the following updated versions of third party to

| Software     | Version |
| ------------ | ------- |
| Cert-Manager | 1.20    |
| Keycloak     | 20.0.3  |
| Postgress    | 15.0.1  |

## Configuration values

The values used [here](https://github.com/tmforum-oda/oda-canvas/blob/master/charts/canvas-oda/README.md)

## Environment installation

### 1. Kubernetes distribution

**Prerequisites**: a running K8S distribution.

The procedure has been tested

- local k3s distribution, rancher desktop or similar
- AWS [Kops](https://kops.sigs.k8s.io/) with AmazonVPC as network and with and without cert-manager managed by kops

We assume there is a ```kubeconfig``` file available with adequate permissions on the K8s cluster to:

- Manage namespaces
- Install [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- Manage resources in namespaces

Run the following to check that you have the required Kubernetes permissions to run the install (or run `./installation/precheck.sh`):

```bash
kubectl auth can-i create namespaces --all-namespaces
kubectl auth can-i create customresourcedefinitions --all-namespaces  
kubectl auth can-i create clusterroles --all-namespaces
kubectl auth can-i create clusterrolebindings --all-namespaces
kubectl auth can-i create mutatingwebhookconfigurations --all-namespaces
kubectl auth can-i create validatingwebhookconfigurations --all-namespaces
kubectl auth can-i create clusterissuers  --all-namespaces
kubectl auth can-i create serviceaccounts
kubectl auth can-i create secrets
kubectl auth can-i create configmaps
kubectl auth can-i create roles
kubectl auth can-i create rolebindings
kubectl auth can-i create services
kubectl auth can-i create deployments
kubectl auth can-i create statefulsets
kubectl auth can-i create gateways  
kubectl auth can-i create jobs
kubectl auth can-i create certificates  
kubectl auth can-i create issuers
```

### 2. Helm

A [Helm 3.0+ installation](https://helm.sh/docs/intro/install/#through-package-managers) is needed.

Helm currently has an issue with the dependencies declared, the **helm dependency update** command only takes care of the dependencies at the first level preventing the correct installation. It supposes to be addressed in a future (May'23) 3.12 version

Until that version is released, we can use a plugin to sort it out this
<https://github.com/Noksa/helm-resolve-deps>

````bash
helm plugin install --version "main" https://github.com/Noksa/helm-resolve-deps.git
````

The charts used need the following repositories

```
helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
```

### 3. Istio

We follow the helm steps provided by [Istio](https://istio.io/latest/docs/setup/install/helm/)

``` bash
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system
helm install istiod istio/istiod -n istio-system --wait
kubectl create namespace istio-ingress
kubectl label namespace istio-ingress istio-injection=enabled
helm install istio-ingress istio/gateway -n istio-ingress --set labels.app=istio-ingress --set labels.istio=ingressgateway --wait
```

### 4. HashiCorp Vault

A setup script to deploy and configure HashiCorp Vault into the cluster and configure it to trust 
the Service-Account-Issuer of this cluster is provided in CanvasVault/setup_CanvasVault.sh.

If HashiCorp Vault is **NOT** installed, everything works fine, only if a component requests Secrets-Management,
it will get stuck in state "InProgress-SecretsConfig".


### 4. Reference implementation

1. Add oda-canvas helm repo

   ```bash
   helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
   helm repo update
   ```

2. Install the reference implementation

    Install the canvas using the following command.

    ```bash
    helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace 
    ```

## Troubleshooting

### Error instaling: BackoffLimitExceeded

The installation can fail with an error

```bash
Error: INSTALLATION FAILED: failed post-install: job failed: BackoffLimitExceeded
```

There are two major causes of this error

1. An error on the Job for configuring keycloak

```bash
kubectl get pods -n canvas
```

```bash
NAME                                        READY   STATUS      RESTARTS   AGE
canvas-keycloak-0                           1/1     Running     0          4m43s
canvas-keycloak-keycloak-config-cli-5k6h7   0/1     Error       0          2m50s
canvas-keycloak-keycloak-config-cli-fq5ph   1/1     Running     0          30s
canvas-postgresql-0                         1/1     Running     0          4m43s
compcrdwebhook-658f4868b8-48cvx             1/1     Running     0          4m43s
job-hook-postinstall-6bm99                  0/1     Completed   0          4m43s
oda-controller-d5c495bbb-crt4t      2/2     Running     0          4m43s
```

Checking the logs of the failed Job

```bash
2023-02-01 15:23:19.488  INFO 1 --- [           main] d.a.k.config.provider.KeycloakProvider   : Wait 120 seconds until http://canvas-keycloak-headless:8083/auth/ is available ...
2023-02-01 15:25:19.511 ERROR 1 --- [           main] d.a.k.config.KeycloakConfigRunner        : Could not connect to keycloak in 120 seconds: HTTP 403 Forbidden
```

That means that your k8s cluster assign IPs to PODs that [Keycloak consider public ones and forced to use HTTPS](https://www.keycloak.org/docs/latest/server_admin/#_ssl_modes)
The ranges valid are the following
`localhost`, `127.0.0.1`, `10.x.x.x`, `192.168.x.x`, and `172.16.x.x`

2. An Error in the Job but caused because the canvas-keycloak-0 that is in CrashLoopBackOff

```bash
kubectl get pods -A
```

```
NAMESPACE       NAME                                              READY   STATUS             RESTARTS      AGE
canvas          canvas-keycloak-0                                 0/1     CrashLoopBackOff   4 (89s ago)   6m11s
canvas          canvas-keycloak-keycloak-config-cli-9ks9d         0/1     Error              0             2m28s
canvas          canvas-keycloak-keycloak-config-cli-cd2gv         0/1     Error              0             4m38s
canvas          canvas-postgresql-0                               1/1     Running            0             6m11s
canvas          compcrdwebhook-658f4868b8-v9sc2                   1/1     Running            0             6m11s
canvas          job-hook-postinstall-v56pt                        0/1     Completed          0             6m10
```

Checking the logs `kubectl logs -n canvas sts/canvas-postgresql`  we can see an error

```bash
FATAL:  password authentication failed for user "bn_keycloak"
```

In that case, a previous installation left a PVC reused by the Postgres pod.

To solve that issue

- Uninstall the helm chart
- Delete the PVC with `kubectl delete pvc -n canvas data-canvas-postgresql-0`
- reinstall the canvas

### Error installing : Failed post-install

The installation could fail with this error

```bash
failed post-install: warning: Hook post-install canvas-oda/charts/cert-manager-init/templates/issuer.yaml failed: Internal error occurred:
failed calling webhook "webhook.cert-manager.io": failed to call webhook: Post "https://canvas-cert-manager-webhook.cert-manager.svc:443/mutate?timeout=10s":
x509: certificate signed by unknown authority
```

That error arises when Cert-Manager is not ready to accept Issuers

Try first to uninstall the chart

```bash
helm uninstall -n canvas canvas
```

Delete persistence volume claim used  for Keycloak

```bash
kubectl delete pvc -n canvas data-canvas-postgresql-0
```

Then manually delete the Lease object that causes the problem (Cert Manager relies on this object to select a leader)

```bash
kubectl get lease -n kube-system
```

Force the release of the lease without waiting for a timeout

```bash
kubectl delete lease cert-manager-cainjector-leader-election -n kube-system
```

The installation has a configurable wait time *cert-manager.leaseWaitTimeonStartup*
Increase `leaseWaitTimeonStartup` value btw 80-100 in `canvas-oda/values.yaml`

Reinstall it with the new time.

## Changes

The Helm chart has been refactored to move all the different subcharts to the same level to improve readability. A new chart, oda-ca has been created as an umbrella to simplify the deployment.

| OLD                     | NEW               | DESCRIPTION                                                                     |
| ----------------------- | ----------------- | ------------------------------------------------------------------------------- |
| shell script            | oda-ca            | Chart of chart.                                                                 |
| shell script            | cert-manager-init | Install cert-manager Deploy Issuer and generate Certificate used by CRD webhook |
| canvas/chart/keycloak   | Bitnami/keycloak  | Direct remote dependency  on oda-ca                                             |
| canvas/                 | canvas-namespaces | Namespaces                                                                      |
| canvas/chart/controller | controller        | ODA ingress controller                                                          |
| canvas/chart/crds       | oda-crds          | ODA crds                                                                        |
| canvas/chart/weebhooks  | oda-webhook       | ODA mutating webhook to handle conversion among versions                        |

## oda-canvas helm chart uninstallation

To  uninstall the oda-canvas chart:

```bash
helm uninstall oda-canvas -n canvas
```
