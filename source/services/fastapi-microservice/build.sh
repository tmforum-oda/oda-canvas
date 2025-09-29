#!/bin/bash

docker build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t ocfork/component-registry .
docker push ocfork/component-registry
