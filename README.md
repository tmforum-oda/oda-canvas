# Open Digital Architecture Canvas

## What is this?

This repo will install and configure a fully working [TMForum Open Digital Architecture](https://www.tmforum.org/collaboration/open-digital-architecture-oda-project/) (ODA) compliant canvas for instantiating ODA components.

## What is the ODA Reference Implementation

For details on the specification of the environment requirements and specific ODA Reference Implementation, see the [specification guide](Specification.md).

## Prerequisites

The installation assumes the following:
* There is a pre-existing [Kubernetes](https://kubernetes.io/) (K8s) cluster with an ingress controller configured
* There is a ```kubeconfig``` file available with adequate permissions on the K8s cluster to:
    * Manage namespaces
    * Install [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
    * Manage resources in namespaces
* [Helm 3](https://helm.sh/) is available and configured to use the ```kubeconfig```. An example script (```install_helm.sh```) is provided to install Helm.
* For manual installation (the method described in this README), a command shell (```bash``` is preferred) that can call Helm from shell scripts.
* If the canvas is relying on other underlying services (e.g. Service Mesh) then these should be deployed in advance of the canvas itself.

## Running locally with Microk8s

Install microk8s with ```sudo snap install microk8s --classic```. Once it is installed, ```microk8s enable ingress dns storage dashboard``` is the minimum configuration for using the canvas deployment script.

## Running locally with K3S

* Installation of K3s itself is documented [here](https://rancher.com/docs/k3s/latest/en/).
* K3s uses the ```traefik``` ingress instead of ```nginx``` therefore you will need to add ```--set controller.deployment.ingressClass.name=traefik,controller.deployment.ingressClass.enabled=true``` to the canvas base install in ```install_canvas_cert-manager.sh```.

## Installing the full reference implementation

 There are three stages to the installation of the full Reference Implementation before components can be deployed:
 * Step 1: cluster enablers that allow the installation of the canvas.
 * Step 2: Reference Implementation services that the canvas relies on.
 * Step 3: the canvas itself.
 * Step 4: configure the supplementary services required to emulate services usually provided outside the ODA

 Full installation instrations are available in the [installation guide](Installation.md).

