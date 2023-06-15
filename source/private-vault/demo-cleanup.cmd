kubectl delete -f test/privatevault-vault-one.yaml
kubectl delete -f test/privatevault-vault-two.yaml
helm uninstall -n demo-comp demo-comp
helm uninstall -n canvas-vault canvas-vault-hc
helm uninstall -n privatevault-system privatevault-operator 
helm uninstall -n privatevault-system oda-pv-crd
helm uninstall -n privatevault-system kopf-framework 
kubectl delete ns demo-comp
kubectl delete ns privatevault-system 
