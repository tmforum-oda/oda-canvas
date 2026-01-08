#!/bin/sh
# cd /mnt/c/Users/A307131/git/oda-canvas/source/operators/dependentApiSimpleOperator/docker
export VERSION=0.1.4
docker build -t ocfork/depapi:$VERSION --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy .
docker push ocfork/depapi:$VERSION