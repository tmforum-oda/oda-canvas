# Demo for Dependent API Operator

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

helm upgrade --install canvas oda-canvas/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-depapi  --set=controller.configmap.loglevel=10
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
helm upgrade --install dependentapi-simple-operator -n canvas source/operators/dependentApiSimpleOperator/helmcharts/dependentApiSimpleOperator
```


# showcase

## open logfile terminals

```
kubectl logs -n canvas deployment/oda-controller-ingress --tail 100 -f
```

```
kubectl logs -n canvas deployment/dependentapi-simple-operator --tail 100 -f
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




