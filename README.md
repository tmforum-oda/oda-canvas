# Open Digital Architecture Canvas
## What is this?
This repo will install and configure a fully working [TMForum Open Digital Architecture](https://www.tmforum.org/collaboration/open-digital-architecture-oda-project/) (ODA) compliant canvas for instantiating ODA components.
## Prerequisites
The installation assumes the following:
* There is a pre-existing [Kubernetes](https://kubernetes.io/) (K8s) cluster with an ingress controller configured
* The cluster is managed by [Rancher](https://rancher.com/) (not strictly necessary for the Canvas installation, but used post-installation by components)
* There is a ```kubeconfig``` file available with adequate permissions on the K8s cluster to:
    * Manage namespaces
    * Install [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
    * Manage resources in namespaces
* [Helm 3](https://helm.sh/) is available and configured to use the ```kubeconfig```. An example script (```install_helm.sh```) is provided to install Helm.
* For manual installation (the method described in this README), a command shell (```bash``` is preferred) that can call Helm from shell scripts.
## Running locally with Microk8s
Install microk8s with ```sudo snap install microk8s --classic```. Once it is installed, ```microk8s enable ingress dns storage dashboard``` is the minimum configuration for using the canvas deployment script.
## Installing the Canvas
There is an example script (```install_canvas.sh```) that will install the Canvas using the chart locally. It does the following:
* Configure the correct Helm repositories
* Install the canvas itself (CRDs, namespaces, component controller)
* Install the canvas-specific components in the canvas namespace
### Notes
* It is possible to enable or disable creation of namespaces in the ```values.yaml``` file.
* Names of namespaces are set to ```canvas``` and ```components``` unless overridden.