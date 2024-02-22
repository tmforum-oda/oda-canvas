#!/bin/bash

for res in namespaces customresourcedefinitions clusterroles clusterrolebindings mutatingwebhookconfigurations validatingwebhookconfigurations clusterissuers
do 
  echo "Can I create ${res} in all namespaces?"
  kubectl auth can-i create ${res} --all-namespaces
done

for res in serviceaccounts secrets configmaps roles rolebindings services deployments statefulsets gateways jobs certificates issuers
do 
  echo "Can I create ${res}?"
  kubectl auth can-i create ${res} 
done

