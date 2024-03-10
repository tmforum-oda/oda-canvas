# ODA Canvas installation with ComponentValut

```
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update

helm upgrade --install canvas oda-canvas/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-compvault
```

