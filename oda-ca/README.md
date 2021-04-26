# ODA Component accelerator source code

This repo contains the source code (and dockerfiles) for the controllers that form part of the ODA Canvas.

The custom resource definitions (CRDs) and controller docker images are used in the Helm charts in the [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts) repository.


The folder contains a sub-folder for:
* controllers - the source code of the controller (operators).
* webhooks - webhooks that help Kubernetes convert between versions of the CRD's
* utilities - useful utilities

