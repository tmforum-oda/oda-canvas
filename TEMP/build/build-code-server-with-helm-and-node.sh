#!/bin/sh

set -xev

cd $(dirname -- $0)

GIT_COMMIT_SHA=$(git rev-parse --short HEAD)
NOW=$(date -Iseconds)
      
cd ../../TEMP/code-server/code-server-with-helm-and-node
docker build -t mtr.devops.telekom.de/magenta_canvas/public:code-server-with-helm-and-node-4.22.0 \
	--build-arg "GIT_COMMIT_SHA=$GIT_COMMIT_SHA" \
    --build-arg "CICD_BUILD_TIME=$NOW" \
    --build-arg http_proxy=$http_proxy \
    --build-arg https_proxy=$https_proxy \
    --build-arg no_proxy=$no_proxy \
	-f Dockerfile .
docker push mtr.devops.telekom.de/magenta_canvas/public:code-server-with-helm-and-node-4.22.0

kubectl rollout restart deployment -n code-server code-server || true
