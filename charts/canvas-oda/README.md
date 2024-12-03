# canvas-oda

![Version: 1.1.8-lt4](https://img.shields.io/badge/Version-1.1.8--lt4-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v1beta4](https://img.shields.io/badge/AppVersion-v1beta4-informational?style=flat-square)

A Helm of helm to orchestrate the ODA installation

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| file://../api-operator-istio | api-operator-istio | 1.0.3 |
| file://../canvas-namespaces | canvas-namespaces | 1.0.1 |
| file://../canvas-vault | canvas-vault | 0.2.1 |
| file://../cert-manager-init | cert-manager-init | 1.0.2 |
| file://../component-operator | component-operator | 1.2.2 |
| file://../dependentapi-simple-operator | dependentapi-simple-operator | 0.2.4 |
| file://../identityconfig-operator-keycloak | identityconfig-operator-keycloak | 1.0.0 |
| file://../oda-crds | oda-crds | 1.1.4 |
| file://../oda-webhook | oda-webhook | 1.1.4 |
| file://../secretsmanagement-operator | secretsmanagement-operator | 0.1.3 |
| https://charts.bitnami.com/bitnami | keycloak | 13.0.2 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| api-operator-istio.configmap.loglevel | string | `"20"` |  |
| api-operator-istio.deployment.apiopImage | string | `"tmforumodacanvas/api-operator-istio"` |  |
| api-operator-istio.deployment.apiopPrereleaseSuffix | string | `"223-refact-2"` |  |
| api-operator-istio.deployment.apiopVersion | string | `"0.2.0"` |  |
| api-operator-istio.deployment.credentialName | string | `"istio-ingress-cert"` |  |
| api-operator-istio.deployment.dataDog.enabled | bool | `true` |  |
| api-operator-istio.deployment.hostName | string | `"*"` |  |
| api-operator-istio.deployment.httpsRedirect | bool | `true` |  |
| api-operator-istio.deployment.imagePullPolicy | string | `"IfNotPresent"` |  |
| api-operator-istio.deployment.ingressClass.enabled | bool | `false` |  |
| api-operator-istio.deployment.ingressClass.name | string | `"nginx"` |  |
| api-operator-istio.deployment.istioGateway | bool | `true` |  |
| api-operator-istio.deployment.monitoredNamespaces | string | `"components"` |  |
| api-operator-istio.deployment.operatrorName | string | `"api-operator-istio"` |  |
| canvas-namespaces.certManagerNamespace | string | `"cert-manager"` |  |
| canvas-namespaces.componentNamespace | string | `"components"` |  |
| canvas-namespaces.enabled | bool | `true` |  |
| canvas-namespaces.istio.labelEnabledComponent | bool | `true` | Add Istion instrumentation label to the components namespace |
| canvas-vault.auth_path | string | `"jwt-k8s-sman"` |  |
| canvas-vault.cacert | string | `nil` |  |
| canvas-vault.enabled | bool | `true` |  |
| canvas-vault.issuer | string | `nil` |  |
| canvas-vault.vault.csi.agent.image.tag | string | `"1.14.8"` |  |
| canvas-vault.vault.global.namespace | string | `"canvas-vault"` |  |
| canvas-vault.vault.global.tlsDisable | bool | `false` |  |
| canvas-vault.vault.injector.agentImage.tag | string | `"1.14.8"` |  |
| canvas-vault.vault.injector.enabled | bool | `false` |  |
| canvas-vault.vault.nameOverride | string | `"vault-hc"` |  |
| canvas-vault.vault.server.dataStorage.accessMode | string | `"ReadWriteOnce"` |  |
| canvas-vault.vault.server.dataStorage.annotations | object | `{}` |  |
| canvas-vault.vault.server.dataStorage.enabled | bool | `true` |  |
| canvas-vault.vault.server.dataStorage.mountPath | string | `"/vault/data"` |  |
| canvas-vault.vault.server.dataStorage.size | string | `"128M"` |  |
| canvas-vault.vault.server.dataStorage.storageClass | string | `nil` |  |
| canvas-vault.vault.server.debug | bool | `true` |  |
| canvas-vault.vault.server.dev.enabled | bool | `false` |  |
| canvas-vault.vault.server.extraEnvironmentVars.VAULT_CACERT | string | `"/vault/userconfig/canvasvault-tls/ca.crt"` |  |
| canvas-vault.vault.server.extraEnvironmentVars.VAULT_TLSCERT | string | `"/vault/userconfig/canvasvault-tls/tls.crt"` |  |
| canvas-vault.vault.server.extraEnvironmentVars.VAULT_TLSKEY | string | `"/vault/userconfig/canvasvault-tls/tls.key"` |  |
| canvas-vault.vault.server.image.tag | string | `"1.14.8"` |  |
| canvas-vault.vault.server.standalone.config | string | `"ui = true\nlistener \"tcp\" {\n  tls_disable = 0\n  address = \"[::]:8200\"\n  cluster_address = \"[::]:8201\"\n  tls_cert_file = \"/vault/userconfig/canvasvault-tls/tls.crt\"\n  tls_key_file  = \"/vault/userconfig/canvasvault-tls/tls.key\"\n  tls_client_ca_file = \"/vault/userconfig/canvasvault-tls/ca.crt\"\n}\nstorage \"file\" {\n  path = \"/vault/data\"\n}\n"` |  |
| canvas-vault.vault.server.standalone.enabled | bool | `true` |  |
| canvas-vault.vault.server.statefulSet.securityContext.container.allowPrivilegeEscalation | bool | `false` |  |
| canvas-vault.vault.server.statefulSet.securityContext.container.capabilities.drop[0] | string | `"ALL"` |  |
| canvas-vault.vault.server.statefulSet.securityContext.container.privileged | bool | `false` |  |
| canvas-vault.vault.server.statefulSet.securityContext.container.readOnlyRootFilesystem | bool | `true` |  |
| canvas-vault.vault.server.statefulSet.securityContext.pod.fsGroup | int | `1000` |  |
| canvas-vault.vault.server.statefulSet.securityContext.pod.runAsGroup | int | `1000` |  |
| canvas-vault.vault.server.statefulSet.securityContext.pod.runAsNonRoot | bool | `true` |  |
| canvas-vault.vault.server.statefulSet.securityContext.pod.runAsUser | int | `100` |  |
| canvas-vault.vault.server.statefulSet.securityContext.pod.supplementalGroups[0] | int | `1000` |  |
| canvas-vault.vault.server.volumeMounts[0].mountPath | string | `"/tmp"` |  |
| canvas-vault.vault.server.volumeMounts[0].name | string | `"tmpvol"` |  |
| canvas-vault.vault.server.volumeMounts[1].mountPath | string | `"/vault/userconfig/canvasvault-tls"` |  |
| canvas-vault.vault.server.volumeMounts[1].name | string | `"userconfig-canvasvault-tls"` |  |
| canvas-vault.vault.server.volumeMounts[1].readOnly | bool | `true` |  |
| canvas-vault.vault.server.volumes[0].emptyDir | object | `{}` |  |
| canvas-vault.vault.server.volumes[0].name | string | `"tmpvol"` |  |
| canvas-vault.vault.server.volumes[1].name | string | `"userconfig-canvasvault-tls"` |  |
| canvas-vault.vault.server.volumes[1].secret.defaultMode | int | `420` |  |
| canvas-vault.vault.server.volumes[1].secret.secretName | string | `"canvasvault-tls"` |  |
| cert-manager-init.cert-manager.enabled | bool | `true` |  |
| cert-manager-init.cert-manager.installCRDs | bool | `true` |  |
| cert-manager-init.cert-manager.namespace | string | `"cert-manager"` |  |
| cert-manager-init.certificateDuration | string | `"21600h"` | Duration of the certificates generate for the webhook in hours | |
| cert-manager-init.fullnameOverride | string | `""` |  |
| cert-manager-init.leaseWaitTimeonStartup | int | `80` | Time to wait CertManager to be ready to prevent issuer creation errors |
| cert-manager-init.nameOverride | string | `""` |  |
| cert-manager-init.namespace | string | `"canvas"` |  |
| component-operator.deployment.compopImage | string | `"tmforumodacanvas/component-operator"` |  |
| component-operator.deployment.compopPrereleaseSuffix | string | `"223-refact-2"` |  |
| component-operator.deployment.compopVersion | string | `"0.7.0"` |  |
| component-operator.deployment.credentialName | string | `"istio-ingress-cert"` |  |
| component-operator.deployment.httpsRedirect | bool | `true` |  |
| component-operator.deployment.imagePullPolicy | string | `"IfNotPresent"` |  |
| component-operator.deployment.istioGateway | bool | `true` |  |
| component-operator.deployment.monitoredNamespaces | string | `"components"` |  |
| component-operator.deployment.operatrorName | string | `"component-operator"` |  |
| dependentapi-simple-operator.enabled | bool | `true` |  |
| dependentapi-simple-operator.image | string | `"tmforumodacanvas/dependentapi-simple-operator"` |  |
| dependentapi-simple-operator.imagePullPolicy | string | `"IfNotPresent"` |  |
| dependentapi-simple-operator.loglevel | string | `"20"` |  |
| dependentapi-simple-operator.prereleaseSuffix | string | `nil` |  |
| dependentapi-simple-operator.serviceInventoryAPI.enabled | bool | `true` |  |
| dependentapi-simple-operator.serviceInventoryAPI.image | string | `"tmforumodacanvas/tmf638-service-inventory-api"` |  |
| dependentapi-simple-operator.serviceInventoryAPI.imagePullPolicy | string | `"IfNotPresent"` |  |
| dependentapi-simple-operator.serviceInventoryAPI.mongodb.database | string | `"svcinv"` |  |
| dependentapi-simple-operator.serviceInventoryAPI.mongodb.port | int | `27017` |  |
| dependentapi-simple-operator.serviceInventoryAPI.prereleaseSuffix | string | `nil` |  |
| dependentapi-simple-operator.serviceInventoryAPI.serverUrl | string | `"http://info.canvas.svc.cluster.local"` |  |
| dependentapi-simple-operator.serviceInventoryAPI.version | string | `"0.1.1"` |  |
| dependentapi-simple-operator.version | string | `"0.2.4"` |  |
| global.certificate.appName | string | `"compcrdwebhook"` | Name of the certificate and webhook | |
| identityconfig-operator-keycloak.configmap.kcrealm | string | `"odari"` |  |
| identityconfig-operator-keycloak.configmap.loglevel | string | `"20"` | Log level [python] (https://docs.python.org/3/library/logging.html |
| identityconfig-operator-keycloak.credentials.pass | string | `"adpass"` |  |
| identityconfig-operator-keycloak.credentials.user | string | `"admin"` |  |
| identityconfig-operator-keycloak.deployment.credentialName | string | `"istio-ingress-cert"` |  |
| identityconfig-operator-keycloak.deployment.hostName | string | `"*"` |  |
| identityconfig-operator-keycloak.deployment.httpsRedirect | bool | `true` |  |
| identityconfig-operator-keycloak.deployment.idkopImage | string | `"tmforumodacanvas/identityconfig-operator-keycloak"` |  |
| identityconfig-operator-keycloak.deployment.idkopPrereleaseSuffix | string | `"223-refact-2"` |  |
| identityconfig-operator-keycloak.deployment.idkopVersion | string | `"0.1.0"` |  |
| identityconfig-operator-keycloak.deployment.idlistkeyImage | string | `"tmforumodacanvas/identity-listener-keycloak"` |  |
| identityconfig-operator-keycloak.deployment.idlistkeyPrereleaseSuffix | string | `"223-refact-2"` |  |
| identityconfig-operator-keycloak.deployment.idlistkeyVersion | string | `"0.7.2"` |  |
| identityconfig-operator-keycloak.deployment.imagePullPolicy | string | `"IfNotPresent"` |  |
| identityconfig-operator-keycloak.deployment.istioGateway | bool | `true` |  |
| identityconfig-operator-keycloak.deployment.keycloak.http | int | `8083` |  |
| identityconfig-operator-keycloak.deployment.keycloak.https | int | `8443` |  |
| identityconfig-operator-keycloak.deployment.monitoredNamespaces | string | `"components"` |  |
| identityconfig-operator-keycloak.deployment.operatrorName | string | `"identityconfig-operator-keycloak"` |  |
| istioCert.certificate.duration | string | `"21600h"` |  |
| istioCert.certificate.renewBefore | string | `"360h"` |  |
| istioCert.namespace | string | `"istio-ingress"` |  |
| keycloak.auth.adminPassword | string | `"adpass"` |  |
| keycloak.auth.adminUser | string | `"admin"` |  |
| keycloak.containerPorts | object | `{"http":8083,"https":8443}` | Keycloak HTTP container port |
| keycloak.enabled | bool | `true` |  |
| keycloak.httpRelativePath | string | `"/auth/"` | Since keycloak 17+, default to / but the controllers work with older versions |
| keycloak.image.tag | string | `"20.0.5-debian-11-r2"` |  |
| keycloak.ingress.enabled | bool | `false` |  |
| keycloak.ingress.hosts[0].name | string | `"keycloak.local"` |  |
| keycloak.ingress.hosts[0].path | string | `"/"` |  |
| keycloak.ingress.hosts[0].tls | bool | `false` |  |
| keycloak.ingress.ingressClassName | string | `"traefik"` |  |
| keycloak.keycloakConfigCli | object | `{"backoffLimit":1,"command":["java","-jar","/opt/keycloak-config-cli.jar"],"configuration":{"odari.json":"{\n  \"enabled\": true,\n  \"realm\": \"odari\",\n  \"users\": [\n    {\n    \"username\": \"canvassystem\",\n    \"email\": \"canvassystem@oda.tmforum.org\",\n    \"enabled\": true,\n    \"firstName\": \"Canvas\",\n    \"lastName\": \"User\",\n    \"clientRoles\": {\n      \"realm-management\": [\n        \"manage-clients\"\n      ]\n     }\n    }\n  ]\n}\n"},"enabled":true,"image":{"tag":"5.5.0-debian-11-r35"}}` | Create a odari realm with an canvassystem user |
| keycloak.postgresql.auth.database | string | `"keycloak"` |  |
| keycloak.postgresql.auth.password | string | `"keycloakdbuser"` |  |
| keycloak.postgresql.auth.username | string | `"keycloak"` |  |
| keycloak.postgresql.enabled | bool | `true` |  |
| keycloak.postgresql.image.tag | string | `"15.2.0-debian-11-r31"` |  |
| keycloak.service | object | `{"ports":{"http":8083,"https":8443}}` | Keycloak LoadBalancer and Headless ClusterIp service port |
| keycloak.tls.autoGenerated | bool | `true` |  |
| keycloak.tls.enabled | bool | `true` |  |
| oda-crds.enabled | bool | `true` |  |
| oda-webhook.image | string | `"tmforumodacanvas/compcrdwebhook"` |  |
| oda-webhook.imagePullPolicy | string | `"IfNotPresent"` |  |
| oda-webhook.prereleaseSuffix | string | `nil` |  |
| oda-webhook.version | string | `"0.11.0"` |  |
| secretsmanagement-operator.auth_path | string | `"jwt-k8s-sman"` |  |
| secretsmanagement-operator.autodetectAudience | bool | `true` |  |
| secretsmanagement-operator.hvacTokenSecret.key | string | `"rootToken"` |  |
| secretsmanagement-operator.hvacTokenSecret.name | string | `"canvas-vault-hc-secrets"` |  |
| secretsmanagement-operator.image | string | `"tmforumodacanvas/secretsmanagement-operator"` |  |
| secretsmanagement-operator.imagePullPolicy | string | `"IfNotPresent"` |  |
| secretsmanagement-operator.logLevel | int | `20` |  |
| secretsmanagement-operator.login_role_tpl | string | `"sman-{0}-role"` |  |
| secretsmanagement-operator.policy_name_tpl | string | `"sman-{0}-policy"` |  |
| secretsmanagement-operator.prereleaseSuffix | string | `nil` |  |
| secretsmanagement-operator.secrets_base_path_tpl | string | `"sidecar"` |  |
| secretsmanagement-operator.secrets_mount_tpl | string | `"kv-sman-{0}"` |  |
| secretsmanagement-operator.sidecarImage | string | `"tmforumodacanvas/secretsmanagement-sidecar"` |  |
| secretsmanagement-operator.sidecarImagePullPolicy | string | `"IfNotPresent"` |  |
| secretsmanagement-operator.sidecarPrereleaseSuffix | string | `nil` |  |
| secretsmanagement-operator.sidecarVersion | string | `"0.1.0"` |  |
| secretsmanagement-operator.vault_addr | string | `"https://canvas-vault-hc.canvas-vault.svc.cluster.local:8200"` |  |
| secretsmanagement-operator.vault_skip_verify | string | `"true"` |  |
| secretsmanagement-operator.version | string | `"0.1.3"` |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
