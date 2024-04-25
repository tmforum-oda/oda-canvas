# Demo for Dependent API Operator

# !!! install prometheus !!!

```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack --namespace grafana --create-namespace prometheus-community/kube-prometheus-stack

# after istio:

kubectl apply -f ../oda-canvas-component-vault/source/component-vault/custom/virtualservices/grafana-vs.yaml

https://grafana.ihc-dt.cluster-3.de/
admin / prom-operator
```


## connect kubectl to cluster ihc-dt

```
gcloud auth login
gcloud container clusters get-credentials ihc-dt --region europe-west3 --project tmforum-oda-component-cluster
kubectl get ns zz-ihc-dt
```

## install canvas

### install canvas from helm chart

```
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update

helm upgrade --install canvas oda-canvas/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-depapi  --set=controller.configmap.loglevel=10 --set=controller.deployment.dataDog.enabled=false

```

### install crd for dependentapi

```
kubectl apply -f charts/oda-crds/templates/oda-dependentapi-crd.yaml
```

### patch ClusterRole odacomponent-role-cluster

```
$ kubectl edit clusterrole odacomponent-role-cluster
```

```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: odacomponent-role-cluster
  ...
rules:
- ...
  ...
- apiGroups: [oda.tmforum.org]
  resources: [dependentapis]
  verbs: [list, watch, patch, get, create, update, delete]    
```

### patch deployment oda-controller-ingress

```
kubectl edit deployment -n canvas oda-controller-ingress

apiVersion: apps/v1
kind: Deployment
metadata:
  name: oda-controller-ingress
  namespace: canvas
  ...
spec:
  ...
        image: mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-depapi        
[*]     imagePullPolicy: Always
```

### patch gateway

```
kubectl edit gateway -n components   component-gateway

apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  namespace: components
  name: component-gateway
  ...
spec:
  - ...
[+++]  
  - hosts:
    - '*.ihc-dt.cluster-3.de'
    port:
      name: https
      number: 443
      protocol: HTTPS
    tls:
      credentialName: wc-ihc-dt-cluster-3-de-tls
      mode: SIMPLE
```

#### create tls secret

```
kubectal apply -f -

apiVersion: v1
kind: Secret
metadata:
  name: wc-ihc-dt-cluster-3-de-tls
  namespace: istio-ingress
type: kubernetes.io/tls
data:
  tls.crt: LS0t...0tCg==
  tls.key: LS0t...LS0K
```


# DependentAPI Operator

## deploy DependentAPI Operator

```
helm upgrade --install depapi-operator -n canvas source/operators/dependentApiSimpleOperator/helmcharts/dependentApiSimpleOperator
```


# Showcase

## show info 

UseCase Discover dependent APIs for Component use-case:

https://github.com/ODA-CANVAS-FORK/oda-canvas-dependent-apis/blob/master/usecase-library/UC003-Discover-dependent-APIs-for-Component.md

Story ODAA-63 "Dependent APIs"
https://projects.tmforum.org/jira/browse/ODAA-63

5 Sub-Tasks

## open logfile terminals

```
kubectl logs -n canvas deployment/oda-controller-ingress --tail 100 -f
```

```
kubectl logs -n canvas deployment/depapi-operator --tail 100 -f
```

## set default to components

```
kubectl config set-context --current --namespace=components
```

## deploy product catalog

```
cd git\oda-canvas-dependent-apis
#helm upgrade --install prodcat -n components compliance-test-kit/BDD-and-TDD/testData/productcatalog-v1beta3
helm upgrade --install prodcat -n components TEMP/INSTALL/helmcharts/productcatalog-component
```

## show dependentapis

```
kubectl get dependentapis -A
```

Details:

```
kubectl get dependentapis -n components   prodcat-productcatalog-dapi-party -oyaml
```

compare with component yaml:

https://github.com/ODA-CANVAS-FORK/oda-canvas-dependent-apis/blob/master/compliance-test-kit/BDD-and-TDD/testData/productcatalog-v1beta3/templates/component-productcatalog.yaml#L31


## increase loglevel to DEBUG (10)

```
helm upgrade --install depapi-operator -n canvas source/operators/dependentApiSimpleOperator/helmcharts/dependentApiSimpleOperator --set=loglevel=10
```

depapi-operator logger quits. Restart it after a few seconds

## undeploy product catalog

```
helm uninstall -n components prodcat
```

## Logfiles of DependentAPI-Operator

```
kubectl logs -n canvas deployment/depapi-operator
[2024-04-24 20:40:46,725] DependentApiSimpleOp [INFO    ] Logging set to 10
[2024-04-24 20:40:46,726] DependentApiSimpleOp [INFO    ] CICD_BUILD_TIME=2024-04-24T20:38:30Z
[2024-04-24 20:40:46,726] DependentApiSimpleOp [INFO    ] GIT_COMMIT_SHA=84214722
/usr/local/lib/python3.12/site-packages/kopf/_core/reactor/running.py:179: FutureWarning: Absence of either namespaces or cluster-wide flag will become an error soon. For now, switching to the cluster-wide mode for backward compatibility.
  warnings.warn("Absence of either namespaces or cluster-wide flag will become an error soon."
[2024-04-24 20:40:46,731] kopf.activities.star [INFO    ] Activity 'configure' succeeded.
[2024-04-24 20:40:46,732] kopf._core.engines.a [INFO    ] Initial authentication has been initiated.
[2024-04-24 20:40:46,734] kopf.activities.auth [INFO    ] Activity 'login_via_client' succeeded.
[2024-04-24 20:40:46,734] kopf._core.engines.a [INFO    ] Initial authentication has finished.
[2024-04-24 20:40:47,347] kopf._core.engines.a [INFO    ] Reconfiguring the validating webhook depapi.mutate.kopf.
[2024-04-24 20:40:47,357] kopf._core.engines.a [INFO    ] Reconfiguring the mutating webhook depapi.mutate.kopf.
[2024-04-24 20:43:18,654] root                 [INFO    ] Create/Update  called with name prodcat-productcatalog-dapi-party in namespace components
[2024-04-24 20:43:18,655] kopf.objects         [INFO    ] [components/prodcat-productcatalog-dapi-party] Handler 'dependentApiCreate' succeeded.
[2024-04-24 20:43:18,655] kopf.objects         [INFO    ] [components/prodcat-productcatalog-dapi-party] Creation is processed: 1 succeeded; 0 failed.
[2024-04-24 20:53:42,426] root                 [INFO    ] Delete         called with name prodcat-productcatalog-dapi-party in namespace components
[2024-04-24 20:53:42,426] kopf.objects         [INFO    ] [components/prodcat-productcatalog-dapi-party] Handler 'dependentApiDelete' succeeded.
[2024-04-24 20:53:42,427] kopf.objects         [INFO    ] [components/prodcat-productcatalog-dapi-party] Deletion is processed: 1 succeeded; 0 failed.
```

## Buildprocess

https://gitlab.devops.telekom.de/magenta-canvas/github-sync/oda-canvas-dependent-apis-cicd/-/pipelines


# Cleanup 

## undeploy DependentAPI Operator

```
helm uninstall -n canvas depapi-operator 
```




# installed helm charts

```
helm list -n components           
helm list -n canvas               
helm list -n canvas-vault         
helm list -n code-server          
helm list -n istio-system         
helm list -n istio-ingress        


$ helm list -n components
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
demo-a          components      2               2024-04-11 11:23:20.287751 +0200 CEST   deployed        productcatalog-0.1.0    1.16.0
prodca2         components      2               2024-04-17 16:48:04.7060091 +0200 CEST  deployed        productcatalog-0.1.0    1.16.0
prodcat         components      7               2024-04-16 18:15:12.8252791 +0200 CEST  deployed        productcatalog-0.1.0    1.16.0
prodcat2        components      1               2024-04-17 16:46:57.6003335 +0200 CEST  failed          productcatalog-0.1.0    1.16.0

$ helm list -n canvas
NAME                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                           APP VERSION
canvas                  canvas          2               2024-04-11 10:50:12.6459128 +0200 CEST  deployed        canvas-oda-1.1.0                v1beta3
componentvault-operator canvas          1               2024-04-11 11:01:37.3677071 +0200 CEST  deployed        componentvaultoperator-0.1.1    0.1.1"
oda-cv-crds             canvas          1               2024-04-11 10:40:29.4080245 +0200 CEST  deployed        oda-cv-crds-0.1.0               0.1.0


$ helm list -n canvas-vault
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
canvas-vault-hc canvas-vault    22              2024-03-13 15:31:57.599788469 +0000 UTC deployed        vault-0.24.0    1.13.1

$ helm list -n code-server
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
code-server     code-server     1               2024-03-06 09:30:28.3912304 +0100 CET   deployed        code-server-3.18.0      4.22.0


$ helm list -n istio-ingress
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
istio-ingress   istio-ingress   1               2024-02-29 14:59:46.656923137 +0000 UTC deployed        gateway-1.20.3  1.20.3

$ helm list -n istio-system
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
istio-base      istio-system    1               2024-02-29 14:58:12.506977926 +0000 UTC deployed        base-1.20.3     1.20.3
istiod          istio-system    1               2024-02-29 14:58:48.595351513 +0000 UTC deployed        istiod-1.20.3   1.20.3
```

## uninstall

```
helm uninstall -n components demo-a
helm uninstall -n components prodca2
helm uninstall -n components prodcat
helm uninstall -n components prodcat2

helm uninstall -n canvas componentvault-operator
helm uninstall -n canvas canvas
helm uninstall -n canvas oda-cv-crds 
```




