# Example Product Inventory component (including Security_role)

This is an example component that implements a TM Forum Product Inventory interface.

As part of the component implementation, it exposes role information to the Canvas using the TM Forum PartyRole API.

The component implements 4 micro-services:

* Product Inventory Microservice that implements the TMF637 Product Inventory Management API (based on the NodeJs reference implementation). This is deployed as a Kubernetes Deployment.
* Party Role Microservice that implements the TMF669 Party Role Management API (based on the NodeJs reference implementation). This is deployed as a Kubernetes Deployment.
* Role Initialization Microservice that bootstraps the initial Party Role interface. This is deployed as a Kubernetes Job that runs once when the component is initialised.
* a standard deployment of a mongoDb. This is deployed as a Kubernetes Deployment with a PersistentVolumeClaim.

The component envelope exposes the ProductInventory as a CoreFunction API and the PartyRole as a Security/PartyRole API.

The Kubernetes services adopt the Istio naming convention for the Port names.

## Installation

Install this component (assuming the kubectl config is connected to a Kubernetes cluster with an operational ODA Canvas) using:

```
helm install r1 .\productinventory -n components
```

You can test the component has deployed successfully using

```
kubectl get components -n components
```

You should get an output like

```
NAME                          DEPLOYMENT_STATUS
r1-productinventory           Complete
```

(The DEPLOYMENT_STATUS will cycle through a number of interim states as part of the deployment). If the deployment fails, refer to the [Troubleshooting-Guide](https://github.com/tmforum-oda/oda-ca-docs/tree/master/Troubleshooting-Guide).
 
