#!/bin/sh

set -xev

cd $(dirname -- $0)

GIT_COMMIT_SHA=$(git rev-parse --short HEAD)
NOW=$(date -Iseconds)
      
sudo docker build -t mtr.devops.telekom.de/magenta_canvas/public:componentvault-controller-0.1.0-rc \
	--build-arg "GIT_COMMIT_SHA=$GIT_COMMIT_SHA" \
    --build-arg "CICD_BUILD_TIME=$NOW" \
	.
sudo docker push mtr.devops.telekom.de/magenta_canvas/public:componentvault-controller-0.1.0-rc

kubectl rollout restart deployment -n canvas componentvault-operator

