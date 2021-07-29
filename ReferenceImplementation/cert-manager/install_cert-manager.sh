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
echo "# Creating namespace ${CMNS}"
echo "#"
echo "#####"
echo ""

kubectl create namespace ${CMNS}

echo "#####"
echo "#"
echo "# Installing cert-manager CRDs"
echo "#"
echo "#####"
echo ""

kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.4.0/cert-manager.crds.yaml

# TODO: these four lines are a hacky fix for a bug - watch the issue then remove the hack
# There is a bug in kubectl (https://github.com/kubernetes/kubernetes/issues/44165)
# to avoid kubectl apply failing, I'll just wait and apply it again.
sleep 1
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.4.0/cert-manager.crds.yaml

# ...then wait for them to be applied correctly. We'll quit here if it still fails.
set -e
kubectl wait --for=condition=established -f  https://github.com/jetstack/cert-manager/releases/download/v1.4.0/cert-manager.crds.yaml
set +e

echo "#####"
echo "#"
echo "# Installing cert-manager in namespace ${CMNS}"
echo "#"
echo "#####"
echo ""

helm install --wait cert-manager jetstack/cert-manager --namespace ${CMNS} --create-namespace --version v1.4.0


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