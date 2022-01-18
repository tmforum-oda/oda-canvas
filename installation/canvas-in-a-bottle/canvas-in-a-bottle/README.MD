# Canvas in a bottle

# Introduction

This repository contains the scripts necessary for quickly deploying and interacting with TM Forum Open Digital Architecture Canvas.

There are multiple ways to deploy Kubernetes and The TM Forum Canvas. Don't see the scripts here as a complete solution, a reference for deploying or being used in the Production. Use the scripts as a quick way to deploy Kubernetes, TM Forum Canvas and a few TM Forum compatible components.

# Quick Start

If you just need to copy the command

## Mac and Linux

```sh
git clone https://github.com/tmforum-oda/canvas-in-a-bottle && cd canvas-in-a-bottle && docker run --rm --name tmf-canvas-in-a-bottle -p 30303:8001 -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -it tmforumodacanvas:canvas-in-a-bottle
```

## Windows

It is necessary to prevent path Expansion on windows with // on the volume, the command becomes:

```sh
git clone https://github.com/tmforum-oda/canvas-in-a-bottle && cd canvas-in-a-bottle && docker run --rm --name tmf-canvas-in-a-bottle -p 30303:8001 -p 3000:3000 -v //var/run/docker.sock:/var/run/docker.sock -it tmforumodacanvas:canvas-in-a-bottle
```

# 
 
# FAQ

The name of the container matters, keep --name tmf-canvas-in-a-bottle