# Credentials Management Operator

![Version: 1.0.1](https://img.shields.io/badge/Version-1.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v1](https://img.shields.io/badge/AppVersion-v1-informational?style=flat-square)

The credentials management operator is intended only for the ODA Canvas Reference Implementation. Its function is to simulate the behind-the-scenes process of providing client credentials and secrets to running components from the identity platform.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| deployment.operatorname | string | credentialsmanagement-operator ||
| deployment.credopImage | string | tmforumodacanvas/credentialsmanagement-operator ||
| deployment.credopVersion | string | 1.0.1 |
| deployment.credopPrereleaseSuffix |string |||
| deployment.imagePullPolicy | string | IfNotPresent ||
| deployment.istioGateway | bool | true ||
| deployment.monitoredNamespaces | string | components | comma separated list of namespaces |
| deployment.ingressClass.enabled | bool | false ||
| deployment.ingressClass.name | string | nginx ||
| deployment.dataDog.enabled | bool | false ||
| deployment.keycloak.port | int | 8080 ||
| deployment.hostName | string | * ||
| deployment.httpsRedirect | bool | true ||
| deployment.credentialName | string | istio-ingress-cert ||
| credentials.client_id | string | credentialsmanagement-operator | clientId of Credentials-Management-Operator client in Keycloak, created during Keycloak installation |
| credentials.client_secret | string || secret of Credentials-Management-Operator client in Keycloak, needs to be manually retrieved from Keycloak and add it before installing the operator |
| configmap.kcbase | string | http://canvas-keycloak-headless.canvas:8083/auth | Keycloak's base url, configured according to : "http://\<oda-canvas release name\>-keycloak-headless.\<oda-canvas release namespace\>:\<keycloak http port\>/auth" |
| configmap.kcrealm | string | odari | Keycloak's realm, configured during Keycloak installation |
| configmap.loglevel | string | 20 |