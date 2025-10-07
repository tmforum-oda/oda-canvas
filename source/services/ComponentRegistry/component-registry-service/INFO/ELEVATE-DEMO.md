# Live-Demo Dependent API Resolution in a Multi-Canvas Scenario

## Setup Environment

### Cluster IHC-DT-A (green)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-a
set DOMAIN=ihc-dt-b.cluster-2.de
set COMPREG_EXTNAME=compreg-a
set TLS_SECRET_NAME=domain-tls-secret
tmfihcdta
```

### Cluster IHC-DT-B (magenta)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-b
set DOMAIN=ihc-dt-b.cluster-2.de
set COMPREG_EXTNAME=compreg-b
set TLS_SECRET_NAME=domain-tls-secret
tmfihcdtb
```

### Cluster IHC-DT (blue)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt
set DOMAIN=ihc-dt.cluster-2.de
tmfihcdt
```

as canvas was deinstalled reinstall the canvas component-gateway standalone

```
helm upgrade --install component-gateway -n canvas --create-namespace %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service/helm/canvas-somponent-gateway

```


## Cleanup

### [blue] - IHC-DT

```
# [blue] - IHC-DT
helm uninstall -n compreg global-compreg
```

### [green] - IHC-DT-A

```
# [green] - IHC-DT-A
kubectl rollout restart -n canvas deployment canvas-depapi-op
```

### [green] - IHC-DT-B

```
# [green] - IHC-DT-B
kubectl rollout restart -n canvas deployment canvas-depapi-op
```



## Show state of IHC-DT-A [GREEN]

```
helm list -A
```

plain canvas installation (from branch)

```
kubectl get deployments -n canvas
```

new: canvas-compreg

```
kubectl canvaslogs depapi
```

new: `COMPONENT_REGISTRY_URL=http://canvas-compreg.canvas.svc.cluster.local`

```
kubectl get vs -n canvas
```

additional public routes have been installed to expose internal services

* https://canvas-compreg.ihc-dt-a.cluster-2.de
* https://canvas-info.ihc-dt-a.cluster-2.de/api-docs/

### show COMPREG-A

https://canvas-compreg.ihc-dt-a.cluster-2.de

Show info:

* NAME "compreg-a"
* Component-Registries (only self)
* Registered Components (empty
* Links - Swagger-UI



## Show state of IHC-DT-B [MAGENTA]

same as ihc-dt-a

https://canvas-compreg.ihc-dt-b.cluster-2.de



## Show state of IHC-DT [BLUE]

```
helm list -A
```



## Install Global Component-Registry

```
# [blue] - IHC-DT
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service
helm upgrade --install global-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 
```

open in browser:

* http://global-compreg.ihc-dt.cluster-2.de/



## Linkregistries (in Browser)




# Links

* Clusters in GCP
  https://console.cloud.google.com/kubernetes/list/overview?project=tmforum-oda-component-cluster
* COMPREG-A
  https://canvas-compreg.ihc-dt-a.cluster-2.de/
* COMPREG-B
  https://canvas-compreg.ihc-dt-b.cluster-2.de/
* GLOBAL COMPREG
  https://global-compreg.ihc-dt.cluster-2.de/
* Canvas-Info_Service IHC-DT-A
  https://canvas-info.ihc-dt-a.cluster-2.de/api-docs/
