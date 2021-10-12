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
* If the canvas is relying on other underlying services (e.g. Service Mesh) then these should be deployed in advance of the canvas itself.
## Running locally with Microk8s
Install microk8s with ```sudo snap install microk8s --classic```. Once it is installed, ```microk8s enable ingress dns storage dashboard``` is the minimum configuration for using the canvas deployment script.
## Running locally with K3S
* Installation of K3s itself is documented [here](https://rancher.com/docs/k3s/latest/en/).
* K3s uses the ```traefik``` ingress instead of ```nginx``` therefore you will need to add ```--set controller.deployment.ingressClass.name=traefik,controller.deployment.ingressClass.enabled=true``` to the canvas base install in ```install_canvas_cert-manager.sh```.
## Four-step install
 There are three stages to the installation of the full Reference Implementation before components can be deployed:
 * Step 1: cluster enablers that allow the installation of the canvas.
 * Step 2: Reference Implementation services that the canvas relies on.
 * Step 3: the canvas itself.
### Step 1: Installing cluster enablers
The only enabler at the moment is the canvas ```namespace```.  Install it using:

```
helm install oda-ri-enablers clusterenablers/ 
```

### Step 2: Installing Reference Implementation services
Install cert-manager to handle certificate creation and signing for the webhook using:
```
pushd ReferenceImplementation/cert-manager
bash install_cert-manager.sh
popd
```
### Step 3: Installing the Canvas
There is an example script (```install_canvas_cert-manager.sh```) that will install the Canvas using the chart locally. It does the following:
* Configure the correct Helm repositories
* Create certificates for the oda.tmforum.org CRD webhook using cert-manager
* Update the dependencies in subcharts (currently just for Keycloak)
* Install the canvas itself (CRDs, namespaces, component controller)
* Install the canvas-specific components in the canvas namespace

Install it using:
```
bash install_canvas_cert-manager.sh
```

### Step 4: Configuring Keycloak

Finally, you will also need to configure Keycloak as follows:
* Log in to the admin console. Unless you changed it manually, the default credentials we've set are in the [Keycloak values.yaml file](canvas/charts/keycloak/values.yaml)
* [Create a new realm](https://www.keycloak.org/docs/latest/server_admin/#_create-realm) called ```myrealm```
* [Create a user in myrealm](https://www.keycloak.org/docs/latest/server_admin/#_create-new-user) called ```seccon```
### Notes
* It is possible to enable or disable creation of namespaces in the ```values.yaml``` file.
* Names of namespaces are set to ```canvas``` and ```components``` unless overridden.