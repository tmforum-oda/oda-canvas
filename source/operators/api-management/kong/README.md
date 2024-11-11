# Kubernetes Kong API Lifecycle Management Operator

## Overview

The Kubernetes Kong API Lifecycle Management Operator is a component of the ODA Canvas, optimized for environments that utilize the Kong API Gateway. It is built using the Kopf Kubernetes operator framework to effectively manage API custom resources. This operator ensures seamless integration with the Kong API Gateway, facilitating the creation, management, and exposure of APIs through HTTPRoute configurations.

## Key Features

Lifecycle Management: Automates the creation, update, and deletion of ODA ExposedAPI resources and their corresponding HTTPRoute configurations.
Plugin Management: Manages KongPlugin resources to enforce various policies and plugins on APIs, enhancing security and functionality.

## Usage
This operator should be deployed within Kubernetes clusters that use the Kong API Gateway for API exposure. It simplifies API management tasks, focusing on security and efficiency, and is an integral part of the ODA Canvas.


![Kong API Operator](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/RJ-acc/oda-canvas-api-gateway/master/source/operators/apiOperatorKong/sequenceDiagrams/KongAPIOperator.puml)
[plantUML code](sequenceDiagrams/KongAPIOperator.puml)


## Testing KOPF module from workstation

It uses to config file present in $HOME/.kube/config to run from local workstation
Run: `kopf run apiOperatorKong.py`



