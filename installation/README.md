
# ODA Canvas installation

The Reference Implementation of the ODA Canvas is a set of Helm charts that can be used to install and configure a fully working Canvas. The Reference Implementation is built on top of Kubernetes and Istio. 

## Software Versions

For each release, we will support a min and max Kubernetes version. 

| ODA Component version | Min Kubernetes version | Max Kubernetes version  |
| --------------------- | ---------------------- | ----------------------- |
| v1alpha4              | 1.20                   | 1.22                    |
| v1beta1               | 1.22                   | 1.25                    |

We will test the Reference Implementation Canvas against a range of kubernetes versions and on a number of different deployments.

| Kubernetes deployment     | Tested | Notes             |
| ------------------------- | ------ | ----------------- |
| Rancher on AWS            |        | [Open Digital Lab environment]                   | 
| Azure AKS                 |        |                   | 
| Microk8s                  |        |                   | 
| MiniKube                  |        |                   |
| Docker Desktop            |        |                   |
| Kind                      |        | Using [Canvas-in-a-bottle](canvas-in-a-bottle/README.md) |
| K3s                       |        |                   |  
| (other)                   |        | To suggest additional environments please add to this [issue](https://github.com/tmforum-oda/oda-canvas-charts/issues/52)                  |

The environment where the chart has been tested has the following
|Software|Version  |
|--|--|
|Istio  | 1.16.1  |
|Helm | 3.10 |

The helm chart installs the following updated versions of third party to

|Software|Version  |
|--|--|
|Cert-Manager  |1.20  |
|Keycloak  |  20.0.3|
|Postgress| 15.0.1 |

## Changes

The Helm chart has been refactored to move all the different subcharts to the same level to improve rreadabilityA new chart, oda-ca has been create as an umbrella for others allowing to have a centralised configuration
|OLD| NEW | DESCRIPTION
|--|--|--|
| shell script  | oda-ca  | Chart of chart.
| shell script | cert-manager-init  | Install cert-manager Deploy Issuer and generate Certificate used by CRD webhook
| canvas/chart/keycloak | Bitnami/keycloak  | Direct remote dependency  on oda-ca
| canvas/| canvas-namespaces  | Namespaces
| canvas/chart/controller| controller  | ODA ingress controller
| canvas/chart/crds| oda-crds| ODA crds
| canvas/chart/weebhooks | oda-webhook| ODA mutating webhook to handle conversion among versions

## Configuration values

The values used [here](canvas-oda/README.md)

## Environment installation

### 1. Kubernetes distribution

**Prerequisites**: a running K8S distribution.
The procedure has been tested

- local k3s distribution, rancher desktop or similar
- AWS [Kops](https://kops.sigs.k8s.io/) with AmazonVPC as network and with and without cert-manager managed by kops
We assume

- There is a ```kubeconfig``` file available with adequate permissions on the K8s cluster to:

- Manage namespaces
- Install [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- Manage resources in namespaces

### 2. Helm

A Helm 3.0+ installation is needed. Depending on your
<https://helm.sh/docs/intro/install/#through-package-managers>

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

### 4. Reference implementation

1. Move to *canvas-oda*
2. Update the dependencies using the plugin installed

````bash
$ helm resolve-deps
Fetching updates from all helm repositories, attempt #1 ...
  * Updates have been fetched, took 2.146s
Resolving dependencies in canvas-oda chart ...
  * Dependencies have been resolved, took 8.672s
````

If we prefer not to use the plugin, we have to manually update the subchart which has dependencies, in this case *cert-manager-init*

````bash
cd ..\cert-manager-init
helm dependency update
````

and then do the same with the umbrella helm *canvas-oda*

````bash
cd ..\canvas-oda
helm dependency update
````

3. Install the reference implementation

Install the canvas using the following command.

````bash
helm install canvas -n canvas --create-namespace . 
NAME: canvas
 Feb  7 09:35:38 2023
NAMESPACE: canvas
STATUS: deployed
REVISION: 1
TEST SUITE: None
````

## Troubleshooting

### Error instaling: BackoffLimitExceeded

The installation can fail with an error

````bash
Error: INSTALLATION FAILED: failed post-install: job failed: BackoffLimitExceeded
````

There are two major causes of this error

1. An error on the Job for configuring keycloak

````bash
 kubectl get pods -n canvas
NAME                                        READY   STATUS      RESTARTS   AGE
canvas-keycloak-0                           1/1     Running     0          4m43s
canvas-keycloak-keycloak-config-cli-5k6h7   0/1     Error       0          2m50s
canvas-keycloak-keycloak-config-cli-fq5ph   1/1     Running     0          30s
canvas-postgresql-0                         1/1     Running     0          4m43s
compcrdwebhook-658f4868b8-48cvx             1/1     Running     0          4m43s
job-hook-postinstall-6bm99                  0/1     Completed   0          4m43s
oda-controller-ingress-d5c495bbb-crt4t      2/2     Running     0          4m43s
````

Checking the logs of the failed Job

````bash
2023-02-01 15:23:19.488  INFO 1 --- [           main] d.a.k.config.provider.KeycloakProvider   : Wait 120 seconds until http://canvas-keycloak-headless:8083/auth/ is available ...
2023-02-01 15:25:19.511 ERROR 1 --- [           main] d.a.k.config.KeycloakConfigRunner        : Could not connect to keycloak in 120 seconds: HTTP 403 Forbidden
````

That means that your k8s cluster assign IPs to PODs that [Keycloak consider public ones and forced to use HTTPS](https://www.keycloak.org/docs/latest/server_admin/#_ssl_modes)
The ranges valid are the following
`localhost`, `127.0.0.1`, `10.x.x.x`, `192.168.x.x`, and `172.16.x.x`

2. An Error in the Job but caused because the canvas-keycloak-0 that is in CrashLoopBackOff

````bash
$ kubectl get pods -A
NAMESPACE       NAME                                              READY   STATUS             RESTARTS      AGE
canvas          canvas-keycloak-0                                 0/1     CrashLoopBackOff   4 (89s ago)   6m11s
canvas          canvas-keycloak-keycloak-config-cli-9ks9d         0/1     Error              0             2m28s
canvas          canvas-keycloak-keycloak-config-cli-cd2gv         0/1     Error              0             4m38s
canvas          canvas-postgresql-0                               1/1     Running            0             6m11s
canvas          compcrdwebhook-658f4868b8-v9sc2                   1/1     Running            0             6m11s
canvas          job-hook-postinstall-v56pt                        0/1     Completed          0             6m10
````

Checking the logs `kubectl logs -n canvas sts/canvas-postgresql`  we can see an error

````bash
 FATAL:  password authentication failed for user "bn_keycloak"
 ````

In that case, a previous installation left a PVC reused by the Postgress
To solve that issue

- Uninstall the helm chart
- Delete the PVC with `kubectl delete pvc -n canvas data-canvas-postgresql-0`
- reinstall the canvas

### Error installing : Failed post-install

The installation could fail with this error

````bash
failed post-install: warning: Hook post-install canvas-oda/charts/cert-manager-init/templates/issuer.yaml failed: Internal error occurred:
failed calling webhook "webhook.cert-manager.io": failed to call webhook: Post "https://canvas-cert-manager-webhook.cert-manager.svc:443/mutate?timeout=10s":
x509: certificate signed by unknown authority
````
That error arises when Cert-Manager is not ready to accept Issuers

Try first to uninstall the chart
````bash
helm uninstall -n canvas canvas
 ````
Delete persistence volume claim used  for Keycloak
````bash
 kubectl delete pvc -n canvas data-canvas-postgresql-0
 ````
Then manually delete the Lease object that causes the problem (Cert Manager relies on this object to select a leader)
````bash
kubectl get lease -n kube-system
 ````
Force the release of the lease without waiting for a timeout
````bash
 kubectl delete lease cert-manager-cainjector-leader-election -n kube-system
 ````

The installation has a configurable wait time
*cert-manager.leaseWaitTimeonStartup*
Increase leaseWaitTimeonStartup value btw 80-100 in canvas-oda\values.yaml

Reinstall it with the new time.


