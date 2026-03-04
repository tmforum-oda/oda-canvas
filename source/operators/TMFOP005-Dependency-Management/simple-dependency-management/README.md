# Simple Dependency Management Operator

## Overview

The Simple Dependency Management Operator is a component of the ODA Canvas that resolves API dependencies between ODA Components at runtime. It is built using the Kopf Kubernetes operator framework to manage DependentAPI custom resources. When a component declares an API dependency, this operator discovers matching ExposedAPI resources and wires the connection automatically.

This is a reference implementation suitable for testing and development. Production deployments will typically replace this with an implementation specific to the Service Provider's processes and policies for granting API access.

## Key Features

- **Dependency Resolution**: Automatically discovers and connects ODA Components to the APIs they depend on by matching DependentAPI resources to ExposedAPI resources.
- **Service Inventory Integration**: Queries the Canvas Service Inventory to locate available API endpoints.
- **Lifecycle Management**: Responds to creation, update, and deletion of DependentAPI resources using Kopf event handlers.

## Usage

This operator should be deployed within Kubernetes clusters running the ODA Canvas. It watches for DependentAPI custom resources and resolves them against available ExposedAPI resources.

## Build and Release

The build and release process for docker images is described in [work-with-dockerimages.md](../../../docs/developer/work-with-dockerimages.md).

## Testing KOPF module from workstation

It uses the config file present in `$HOME/.kube/config` to run from a local workstation.

Run: `kopf run docker/src/dependentApiSimpleOperator.py`
