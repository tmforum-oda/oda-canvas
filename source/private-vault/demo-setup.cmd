helm upgrade --install oda-pv-crd installation/oda-pv-crds --namespace privatevault-system --create-namespace

helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc hashicorp/vault --version 0.24.0 --namespace canvas-vault --create-namespace --values installation/canvas-vault-hc/values.yaml

kubectl apply -f installation/canvas-vault-hc/public-route-for-testing.yaml

timeout 5
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-pv jwt
timeout 1
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-pv/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

helm upgrade --install kopf-framework operators/privatevaultoperator-hc/helmcharts/kopf-framework --namespace privatevault-system --create-namespace

helm upgrade --install privatevault-operator operators/privatevaultoperator-hc/helmcharts/pvop --namespace privatevault-system --create-namespace

kubectl apply -f test/privatevault-demoa-comp-one.yaml
kubectl apply -f test/privatevault-demob-comp-two.yaml
kubectl get privatevaults

helm upgrade --install demoa test/helm-charts/demoa -n demo-comp --create-namespace
helm upgrade --install demob test/helm-charts/demob -n demo-comp --create-namespace
helm upgrade --install democ test/helm-charts/democ -n demo-comp --create-namespace
