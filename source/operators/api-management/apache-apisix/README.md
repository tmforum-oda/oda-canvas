# Kubernetes Kong API Lifecycle Management Operator

## Overview

The Kubernetes Apisix API Lifecycle Management Operator is a component of the ODA Canvas, optimized for environments that utilize the Apisix API Gateway. It is built using the Kopf Kubernetes operator framework to effectively manage API custom resources. This operator ensures seamless integration with the Apisix API Gateway, facilitating the creation, management, and exposure of APIs through ApisixRoute and putting policies in place using ApisixPluginconfig configurations.

## Key Features

Lifecycle Management: Automates the creation, update, and deletion of ODA ExposedAPI resources and their corresponding ApisixRoute configurations.
Plugin Management: Manages ApisixPluginConfig resources to enforce various policies and plugins on APIs, enhancing security and functionality.

## Usage
This operator should be deployed within Kubernetes clusters that use the Apisix API Gateway for API exposure. It simplifies API management tasks, focusing on security and efficiency, and is an integral part of the ODA Canvas.


![Apisix API Operator](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/RJ-acc/oda-canvas-api-gateway/master/source/operators/apiOperatorApisix/sequenceDiagrams/ApisixAPIOperator.puml)
[plantUML code](sequenceDiagrams/ApisixAPIOperator.puml)


## Testing KOPF module from workstation

It uses kube config file present in $HOME/.kube/config to run from local workstation
Run: `kopf run apiOperatorKong.py`



