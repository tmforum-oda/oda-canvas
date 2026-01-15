#!/bin/sh
# cd /mnt/c/Users/A307131/git/oda-canvas/source/services/ComponentRegistry
export VERSION=1.0.30
export CICD_BUILD_TIME=$(date -Iseconds)
docker build -t ocfork/compreg-tmf639:$VERSION --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg CICD_BUILD_TIME=$CICD_BUILD_TIME .
docker push ocfork/compreg-tmf639:$VERSION