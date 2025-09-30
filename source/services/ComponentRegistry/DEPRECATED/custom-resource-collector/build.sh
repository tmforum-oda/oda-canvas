#!/bin/bash

docker build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t ocfork/custom-resource-collector .
docker push ocfork/custom-resource-collector
