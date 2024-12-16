# Kubernetes Kong API Lifecycle Management Operator

## Overview

The Kubernetes Kong API Lifecycle Management Operator is a component of the ODA Canvas, optimized for environments that utilize the Kong API Gateway. It is built using the Kopf Kubernetes operator framework to effectively manage API custom resources. This operator ensures seamless integration with the Kong API Gateway, facilitating the creation, management, and exposure of APIs through HTTPRoute configurations.

This operator also uses Istio to control traffic between components and from the components to the API Gateway. This is a zero-trust model where internal traffic within the Canvas is controlled and communication is only allowed if it is explicitly declared in the Component specification.

## Key Features

Lifecycle Management: Automates the creation, update, and deletion of ODA ExposedAPI resources and their corresponding HTTPRoute configurations.
Plugin Management: Manages KongPlugin resources to enforce various policies and plugins on APIs, enhancing security and functionality.

## Usage
This operator should be deployed within Kubernetes clusters that use the Kong API Gateway for API exposure. It simplifies API management tasks, focusing on security and efficiency, and is an integral part of the ODA Canvas.


![Kong API Operator](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/source/operators/apiOperatorKong/sequenceDiagrams/KongAPIOperator.puml)
[plantUML code](sequenceDiagrams/KongAPIOperator.puml)


## Testing KOPF module from workstation

It uses to config file present in $HOME/.kube/config to run from local workstation
Run: `kopf run apiOperatorKong.py`

## Installing Konga (Unofficial GUI for Kong)

Konga is an unofficial, community-supported graphical user interface (GUI) for managing Kong Gateway. It provides an intuitive dashboard to monitor and configure Kong resources such as routes, services, plugins, and consumers.

Steps to Install Konga: Use konga-install.yaml to deploy konga for testing purpose. 
    ```
    kubectl apply -f konga-install.yaml
    ```

