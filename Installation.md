# Installation

## Step 1: Installing cluster enablers

The only enabler at the moment is the canvas ```namespace```.  Install it using:

```
helm install oda-ri-enablers clusterenablers/ 
```

## Step 2: Installing Reference Implementation services
Install cert-manager to handle certificate creation and signing for the webhook using:
```
pushd ReferenceImplementation/cert-manager
bash install_cert-manager.sh
popd
```
## Step 3: Installing the Canvas
There is an example script (```install_canvas_cert-manager.sh```) that will install the Canvas using the chart locally. It does the following:
- Configure the correct Helm repositories
- Create certificates for the oda.tmforum.org CRD webhook using cert-manager
- Update the dependencies in subcharts (currently just for Keycloak)
- Install the canvas itself (CRDs, namespaces, component controller)
- Install the canvas-specific components in the canvas namespace

Install it using:
```
bash install_canvas_cert-manager.sh
```

## Step 4: Configuring Keycloak

Finally, you will also need to configure Keycloak as follows:
- Log in to the admin console. Unless you changed it manually, the default credentials we've set are in the [Keycloak values.yaml file](https://github.com/tmforum-oda/oda-canvas-charts/blob/master/canvas/charts/keycloak/values.yaml)
- [Create a new realm](https://www.keycloak.org/docs/latest/server_admin/#_create-realm) called ```myrealm```
- [Create a user in myrealm](https://www.keycloak.org/docs/latest/server_admin/#_create-new-user) called ```seccon```
### Notes
- It is possible to enable or disable creation of namespaces in the ```values.yaml``` file.
- Names of namespaces are set to ```canvas``` and ```components``` unless overridden.