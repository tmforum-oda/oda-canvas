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
## Running locally with K3S
* Installation of K3s itself is documented [here](https://rancher.com/docs/k3s/latest/en/).
* K3s uses the ```traefik``` ingress instead of ```nginx``` therefore you will need to add ```--set controller.deployment.ingressClass.name=traefik,controller.deployment.ingressClass.enabled=true``` to the canvas base install in ```install_canvas_cert-manager.sh```.
## Installing Prerequisites into the cluster
_Prerequisites, like CRDs and namespaces will be split out into separate charts in a future sprint._
## Installing Reference Implementation services
* Install cert-manager to handle certificate creation and signing for the webhook using ```bash ReferenceImplementation/cert-manager```
## Installing the Canvas
There is an example script (```install_canvas_cert-manager.sh```) that will install the Canvas using the chart locally. It does the following:
* Configure the correct Helm repositories
* Create certificates for the oda.tmforum.org CRD webhook using cert-manager
* Update the dependencies in subcharts (currently just for Keycloak)
* Install the canvas itself (CRDs, namespaces, component controller)
* Install the canvas-specific components in the canvas namespace
### Notes
* It is possible to enable or disable creation of namespaces in the ```values.yaml``` file.
* Names of namespaces are set to ```canvas``` and ```components``` unless overridden.