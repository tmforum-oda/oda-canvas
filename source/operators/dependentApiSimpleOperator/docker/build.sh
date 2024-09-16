#!/bin/sh
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t depapiop .
docker build --build-arg FROM_IMAGE=depapiop --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t testdepapiop -f DockerfileTest .
docker run testdepapiop  