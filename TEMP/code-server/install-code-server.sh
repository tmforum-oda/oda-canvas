#!/bin/bash

set -xev
cd $(dirname -- $0)

test -n "$CODE_SERVER_PASSWORD"

kubectl create ns code-server || true
kubectl create secret generic -n code-server code-server-secret --from-literal=password="$CODE_SERVER_PASSWORD" --dry-run=client -oyaml | kubectl apply -f - 

git clone https://github.com/coder/code-server
cd code-server
helm upgrade --install -n code-server --create-namespace code-server --set existingSecret=code-server-secret ci/helm-chart \
    --set image.repository=mtr.devops.telekom.de/magenta_canvas/public \
    --set image.tag=code-server-with-helm-4.22.0
cd ..

kubectl create clusterrolebinding code-server-cluster-admin-rb --clusterrole=cluster-admin --serviceaccount=code-server:code-server --dry-run=client -oyaml | kubectl apply -f -

kubectl apply -f virtualservice/code-server-vs.yaml

