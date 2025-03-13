#!/bin/sh
export VERSION=0.1.1-dev
docker build --build-arg https_proxy=$https_proxy -t ocfork/oa2envf:$VERSION .
docker push ocfork/oa2envf:$VERSION
 