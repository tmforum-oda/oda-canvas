# Component Operator - Introduction

This is the reference implementaiton of a component controller that takes metadata from ODA Component and uses it to automatically configure the exposedAPIs, securityAPIs (and in the future other services). The diagram below shows how the component controller interacts with the different Kubernetes entities (via the Kubernetes API).


![Sequence diagram](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ODA-CANVAS-FORK/oda-canvas-component-vault/master/source/operators/componentOperator/sequenceDiagrams/componentOperator.puml)
[plantUML code](sequenceDiagrams//componentOperator.puml)

![Sequence diagram](sequenceDiagrams/componentOperator.png)



The component controller written in Python, using the [KOPF](https://kopf.readthedocs.io/) framework to listen for components being deployed in the ODA Canvas. 


**Testing KOPF module**

Run: `kopf run --namespace=components --standalone .\componentOperator.py`
