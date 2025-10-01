#!/bin/bash

VERSION=0.1.4
docker build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t ocfork/custom-resource-collector:$VERSION .
docker push ocfork/custom-resource-collector:$VERSION
