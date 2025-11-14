#!/bin/sh
# cd /mnt/c/Users/A307131/git/oda-canvas/source/services/ComponentRegistry
export VERSION=1.0.23
docker build -t ocfork/compreg-tmf639:$VERSION --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy .
docker push ocfork/compreg-tmf639:$VERSION