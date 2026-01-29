#!/bin/sh
# cd /mnt/c/Users/A307131/git/oda-canvas/source/tmf-services/TMF639_Resource_Inventory
export VERSION=0.1.3
export CICD_BUILD_TIME=$(date -Iseconds)"
docker build -t ocfork/tmf639:$VERSION --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg CICD_BUILD_TIME=$CICD_BUILD_TIME .
docker push ocfork/tmf639:$VERSION