#!/bin/sh
export VERSION=0.1.1-dev
export CICD_BUILD_TIME=$(date -Iseconds)"
docker build --build-arg https_proxy=$https_proxy -t ocfork/oa2envf:$VERSION --build-arg CICD_BUILD_TIME=$CICD_BUILD_TIME .
docker push ocfork/oa2envf:$VERSION
 