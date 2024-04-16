# ODA Canvas installation with DependentAPI


## deploy from modified charts

```
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace 


cd charts/cert-manager-init
helm dependency update
cd ../..

helm dependency update
helm upgrade --install canvas -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-depapi --set=controller.configmap.loglevel=10 oda-canvas/canvas-oda
```



## patch ClusterRole odacomponent-role-cluster

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

## patch deployment oda-controller-ingress

```
$ kubectl edit deployment -n canvas oda-controller-ingress
```

```
        image: mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-depapi
[*]     imagePullPolicy: Always
```
