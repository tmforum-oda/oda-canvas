#!/bin/sh
kubectl delete -f test/privatevault-demoa-comp-one.yaml
kubectl delete -f test/privatevault-demob-comp-two.yaml
helm uninstall -n demo-comp demoa demob democ
helm uninstall -n canvas-vault canvas-vault-hc
helm uninstall -n privatevault-system privatevault-operator 
helm uninstall -n privatevault-system oda-pv-crd
helm uninstall -n privatevault-system kopf-framework 
kubectl delete ns demo-comp
kubectl delete ns privatevault-system 
