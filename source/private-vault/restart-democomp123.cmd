helm uninstall -n demo-comp-123 demo-comp-123
helm upgrade --install demo-comp-123 test/helm-charts/democomp -n demo-comp-123 --create-namespace