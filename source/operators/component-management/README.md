# Component Management Operator

This is the reference implementiton of a component operator that manages the overall lifecycle of an ODA Component. The component operator takes the `Component` custom resource and creates multiple sub-reaources for each part of the component specification. At present it creates sub-resources for `ExposedAPI`, `DependentAPI`, `PublishedNotification`, `SubscribedNotification` and `SecretsManagement`. In the near future it will also create custom resources for `IdentityConfig` and `ObservabilityConfig`.

Separate operators then process the sub-resources and manage the relavant services in the ODA Canvas. This allows technology-specific versions of these operators. For example, if you were using an open source Kong API Gateway, you install the kong-specific API Management operator which would take metadata from the `ExposedAPI` resource and use it to configure APIs in Kong.


## Sequence Diagram

The sequence diagram shows the overall lifecycle of deploying an ODA Component, with the component operator creating multiple sub-resources.

![manage-components-install](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/manage-components-install.puml)
[plantUML code](../../../usecase-library/pumlFiles/manage-components-install.puml)

There is more detail, including sequence diagrams for upgrade and deletion in use case [UC002-Manage-Components](../../../usecase-library/UC002-Manage-Components.md).



## Reference Implementation

The reference implementation of the component operator written in Python, using the [KOPF](https://kopf.readthedocs.io/) operator framework. You are free to re-use this implementation, extend or customize it, or develop your own component operator. Any custom component operator should use the same `Component` Custom Resource definition that is a foundational part of the ODA Canvas. To be compatible with other operators in the reference implementation, it should also use the `ExposedAPI`, `DependentAPI`, `PublishedNotification`, `SubscribedNotification` and `SecretsManagement` and (in the future)`IdentityConfig` and `ObservabilityConfig` custom resources. 


**Interactive development and Testing of operator using KOPF**

When deployed in an ODA Canvas, the operator will execute inside a Kubernetes Pod. For development and testing, it is possible to run the operator on the command-line (or inside a debugger). Kopf includes a `--standalone` attribute to allow the operator to execute in a standalone mode. This means that the operator will run independently, without relying on any external operators or frameworks. It is particularly useful for development and debugging purposes, as it allows you to run and test your operator locally on your machine.

Run locally in command-line: 
```
kopf run --namespace=components --standalone .\componentOperator.py
```

This mode will use the kubeconfig file (typically located at `$HOME/.kube/config`). As long as `kubectl` is correctly configured for your cluster, the operator should work. 

You need to ensure you turn-off the operator executing in Kubernetes (for example, by setting the replicas to 0 in the operator Deployment).

The command above will execute just the component operator. You will also need to execute the other operators relevant for your Canvas implementation - these can be executed in separate terminal command-lines.


## Build automation and versioning

The build and release process for docker images is described here:
[/docs/developer/work-with-dockerimages.md](../../../docs/developer/work-with-dockerimages.md)


  
