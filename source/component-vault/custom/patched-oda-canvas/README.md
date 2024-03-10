# ODA Canvas installation with ComponentValut

```
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update

helm upgrade --install canvas oda-canvas/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-compvault
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
    resources: [componentvaults]
    verbs: [list, watch, patch, get, create, update, delete]    
```

## patch deployment oda-controller-ingress

```
        image: mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-compvault
[*]     imagePullPolicy: Always
```
