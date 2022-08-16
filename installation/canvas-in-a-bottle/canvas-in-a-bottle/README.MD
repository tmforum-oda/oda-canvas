# Canvas in a bottle

# Introduction

This repository contains the scripts necessary for quickly deploying and interacting with TM Forum Open Digital Architecture Canvas.

There are multiple ways to deploy Kubernetes and The TM Forum Canvas. Don't see the scripts here as a complete solution, a reference for deploying or being used in the Production. Use the scripts as a quick way to deploy Kubernetes, TM Forum Canvas and a few TM Forum compatible components.

# Pre requisites

You only need Docker that you can get from:
https://docs.docker.com/desktop/


# Quick Start



```sh
docker run --rm --name tmf-canvas-in-a-bottle -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -it tmforumodacanvas/canvas-in-a-bottle:gui
```
The previous command will install the Canvas in a Bottle but without the capacity of installing any APIs. You will still be able to install Use Cases.

If you need the Reference APIs and work for a company that is a member of TM Forum, follow the step bellow.

# For TM Forum Members

TM Forum member have access to pre generated reference implementations of the APIs defined by TMF Open API Program

And can use the following commands to have those APIs accessible on Runtime:

```sh
git clone https://github.com/tmforum-rand/Reference-Implementations-Pack.git apis
```

if your company is member from TM Forum and you need access to the repository contact "Henrique Rodrigues" at TM Forum.

After having the apis download and at the apis folder:

```sh
docker run --rm --name tmf-canvas-in-a-bottle -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}/apis:/apis -it tmforumodacanvas/canvas-in-a-bottle:gui
```


# FAQ

The name of the container matters, keep --name tmf-canvas-in-a-bottle



When you close the terminal attached to the image, issuing "exit" command for example, the cluster will be deleted and data will be lost, this is by design as we wanted a cluster that cleared after itself.

If a proxy is needed follow the Client proxy here: https://docs.docker.com/network/proxy/

