#!/bin/bash

VERSION=0.3.9
docker build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t ocfork/component-registry:$VERSION .
docker push ocfork/component-registry:$VERSION

