# Component Viewer utility

This is a simple kubectl utility to display information on the ODA Component deployment and lifecycle.

# Installation

```
npm install @lesterthomas/kubectl-component_info -g
```


Then, to run plugin within kubectl:

```
kubectl component-info
```


The utility will use the current kubeconfig to connect to the Kubernetes cluster. It will show 'No ODA Components to view' if there are no components being deployed. If there are components, you will get a screen like the one below:

![Screenshot](Screenshot.png)

To exit the utility, type `CTRL-C`



## Publishing

To publish a new version, update the version number in the package.json file and use the command

```
npm publish --access public
```