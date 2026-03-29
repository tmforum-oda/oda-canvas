# Vault Secrets Management Operator

## Overview

The Vault Secrets Management Operator is a component of the ODA Canvas that integrates with HashiCorp Vault to provide secure secrets management for ODA Components. It is built using the Kopf Kubernetes operator framework to manage SecretsManagement custom resources, ensuring that sensitive configuration — such as passwords, API keys, and certificates — is securely stored in and retrieved from Vault.

## Components

This implementation consists of two parts:

- **[Operator](./docker/)**: A Kopf-based Python operator that watches for SecretsManagement custom resources and manages the corresponding secrets lifecycle in HashiCorp Vault.
- **[Sidecar](./sidecar/)**: A Go-based sidecar service that runs alongside ODA Components, providing a local API for components to access their secrets from Vault.

## Key Features

- **Vault Integration**: Manages secrets in HashiCorp Vault using the `hvac` Python client library.
- **Lifecycle Management**: Automates creation, update, and deletion of secrets in response to SecretsManagement custom resource events.
- **Sidecar Access**: Provides a local REST API sidecar for components to retrieve secrets without direct Vault access.

## Build and Release

The build and release process for docker images is described in [work-with-dockerimages.md](../../../docs/developer/work-with-dockerimages.md).

## Testing KOPF module from workstation

It uses the config file present in `$HOME/.kube/config` to run from a local workstation.

Run: `kopf run docker/secretsmanagementOperatorHC.py`
