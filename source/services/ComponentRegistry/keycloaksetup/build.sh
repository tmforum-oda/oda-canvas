#!/bin/sh
# cd /mnt/c/Users/A307131/git/oda-canvas/source/services/ComponentRegistry
export VERSION=1.0.2
docker build -t ocfork/kc-init:$VERSION --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy .
docker push ocfork/kc-init:$VERSION