#!/bin/bash

export CERTNS="canvas"
export CMNS="cert-manager"

echo "#####"
echo "#"
echo "# Preparing Helm"
echo "#"
echo "#####"
echo ""

helm repo add jetstack https://charts.jetstack.io
helm repo update

echo "#####"
echo "#"
echo "# Installing cert-manager in namespace ${CMNS}"
echo "#"
echo "#####"
echo ""

kubectl create namespace ${CMNS}
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.3.1/cert-manager.crds.yaml
sleep 1
helm install --wait cert-manager jetstack/cert-manager --namespace ${CMNS} --create-namespace --version v1.3.1


echo "#####"
echo "#"
echo "# Creating ClusterIssuer and ${CERTNS} namespace Issuer"
echo "#"
echo "#####"
echo ""

# There seems to be a timing issue between cert-manager running
# and the authority to be recognised. If you get this, increase sleep:
#
# Error from server (InternalError): error when creating "STDIN":
# Internal error occurred: failed calling webhook
# "webhook.cert-manager.io": Post
# "https://cert-manager-webhook.cert-manager.svc:443/mutate?timeout=10s":
# x509: certificate signed by unknown authority

sleep 4
sed "s/<namespace>/${CERTNS}/g" issuers.yaml | kubectl apply -f -