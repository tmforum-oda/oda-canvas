# apisix-gateway

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v1](https://img.shields.io/badge/AppVersion-v1-informational?style=flat-square)

A Helm chart for Kubernetes

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://charts.apiseven.com | apisix(apisix) | 2.7.0 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| apisixistiooperatordeploymentnamespace | string | `"canvas"` |  |
| apisixoperatorimage.pullPolicy | string | `"IfNotPresent"` |  |
| apisixoperatorimage.repository | string | `"tmforumodacanvas/api-operator-apisix:1.0.0"` |  |
| apisixoperatorreplicaCount | int | `1` |  |
| gateway.type | string | `"LoadBalancer"` |  |
| ingress-controller.config.apisix.adminAPIVersion | string | `"v3"` |  |
| ingress-controller.enabled | bool | `true` |  |
| ingress-controller.serviceNamespace | string | `"ingress-apisix"` |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)