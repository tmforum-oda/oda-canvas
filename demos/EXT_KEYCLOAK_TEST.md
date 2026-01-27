cd canvas-prerequisites
helm dependency update identity\keycloak
helm dependency update charts
helm upgrade --install -n canvas --create-namespace canvas-keycloak charts --set=keycloak.keycloak.service.type=ClusterIP
kubectl get secret -n canvas canvas-keycloak-credentials -o jsonpath='{.data.keycloak-admin-password}' | base64 --decode
                             ^^^^^^^

	 
set KC_ADMIN_PASSWORD=...

helm dependency update --skip-refresh charts/canvas-oda

helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace ^
  --set keycloak.enabled=false ^
  --set api-operator-istio.deployment.hostName=*.%DOMAIN% ^
  --set api-operator-istio.deployment.credentialName=%TLS_SECRET_NAME% ^
  --set api-operator-istio.configmap.publicHostname=components.%DOMAIN% ^
  --set api-operator-istio.deployment.httpsRedirect=false ^
  --set canvas-info-service.serverUrl=https://canvas-info.%DOMAIN% ^
  --set component-registry.ownRegistryName=%COMPREG_EXTNAME% ^
  --set component-registry.domain=%DOMAIN% ^
  --set component-registry.keycloak.setup.canvasKeycloakSecret=canvas-keycloak-credentials ^
  --set component-registry.keycloak.setup.adminPasswordKey=keycloak-admin-password ^
  --set component-registry.keycloak.setup.kcBaseUrl=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080 ^
  --set component-registry.keycloak.url=https://canvas-keycloak.%DOMAIN%/realms/odari ^
  --set component-registry.keycloak.validIssuers=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080/realms/odari ^
  --set component-registry.oauth2.tokenUrl=https://canvas-keycloak.%DOMAIN%/realms/odari/protocol/openid-connect/token ^
  --set dependentapi-simple-operator.oauth2.tokenUrl=https://canvas-keycloak.%DOMAIN%/realms/odari/protocol/openid-connect/token ^
  --set resource-inventory.serviceType=ClusterIP ^
  --set resource-inventory.serverUrl=https://canvas-resource-inventory.%DOMAIN%/tmf-api/resourceInventoryManagement/v5 ^
  --set identityconfig-operator-keycloak.credentials.pass=%KC_ADMIN_PASSWORD% ^
  --set identityconfig-operator-keycloak.configmap.kcbase=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080 ^
  --set api-operator-istio.deployment.apiopPrereleaseSuffix=feature-84 ^
  --set canvas-vault.enabled=false



helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace \
  --set keycloak.enabled=false \
  --set api-operator-istio.deployment.hostName=*.$DOMAIN \
  --set api-operator-istio.deployment.credentialName=$TLS_SECRET_NAME \
  --set api-operator-istio.configmap.publicHostname=components.$DOMAIN \
  --set api-operator-istio.deployment.httpsRedirect=false \
  --set canvas-info-service.serverUrl=https://canvas-info.$DOMAIN \
  --set component-registry.ownRegistryName=$COMPREG_EXTNAME \
  --set component-registry.domain=$DOMAIN \
  --set component-registry.keycloak.setup.canvasKeycloakSecret=canvas-keycloak-credentials \
  --set component-registry.keycloak.setup.adminPasswordKey=keycloak-admin-password \
  --set component-registry.keycloak.setup.kcBaseUrl=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080 \
  --set component-registry.keycloak.url=https://canvas-keycloak.$DOMAIN/realms/odari \
  --set component-registry.keycloak.validIssuers=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080/realms/odari \
  --set component-registry.oauth2.tokenUrl=https://canvas-keycloak.%DOMAIN%/realms/odari/protocol/openid-connect/token \
  --set dependentapi-simple-operator.oauth2.tokenUrl=https://canvas-keycloak.%DOMAIN%/realms/odari/protocol/openid-connect/token \
  --set resource-inventory.serviceType=ClusterIP \
  --set resource-inventory.serverUrl=https://canvas-resource-inventory.$DOMAIN/tmf-api/resourceInventoryManagement/v5 \
  --set identityconfig-operator-keycloak.credentials.pass=$KC_ADMIN_PASSWORD \
  --set identityconfig-operator-keycloak.configmap.kcbase=http://canvas-keycloak-keycloak.canvas.svc.cluster.local:8080 \
  --set api-operator-istio.deployment.apiopPrereleaseSuffix=feature-84 \
  --set canvas-vault.enabled=false


helm upgrade --install -n canvas canvas-vs ^
  %USERPROFILE%/git/oda-canvas-notes/virtualservices/canvas ^
  --set=keycloakVS.host=canvas-keycloak-keycloak ^
  --set=keycloakVS.port=8080 ^
  --set=keycloakVS.landigpagePrefix=/hint ^
  --set=keycloakVS.adminPwdSecretName=canvas-keycloak-credentials ^
  --set=keycloakVS.adminPwdSecretKey=keycloak-admin-password ^
  --set=keycloakVS.loginPath=/ ^
  --set=domain=%DOMAIN%
 


set KC_DOMAIN=ihc-dt-a.cluster-2.de
cd %USERPROFILE%/git/oda-canvas
helm upgrade --install -n compreg global-compreg --create-namespace charts/component-registry --set=domain=%DOMAIN% --set=canvasResourceInventory= --set=keycloak.url=https://canvas-keycloak.%KC_DOMAIN%/realms/odari 
helm upgrade --install -n compreg global-compreg-vs demos/multi-canvas-service-discovery/helm/component-registry-vs --set=domain=%DOMAIN%  --set=fullNameOverride=global-compreg



# Source: canvas-oda/charts/identityconfig-operator-keycloak/templates/secret.yaml
data:
  KEYCLOAK_USER: "YWRtaW4="
  KEYCLOAK_PASSWORD: "..."
  --> replace with secretRef

# Source: canvas-oda/charts/identityconfig-operator-keycloak/templates/configMap.yaml
data:
  KEYCLOAK_BASE: "http://canvas-keycloak-headless.canvas:8083/auth"
  --> old:
  KEYCLOAK_BASE: "http://{{ .Release.Name }}-keycloak-headless.{{ .Release.Namespace }}:{{ .Values.deployment.keycloak.http }}/auth"
  --> new:
  {{ if .Values.configmap.kcbase -}}
  KEYCLOAK_BASE: "{{ .Values.configmap.kcbase }}"
  {{- else -}}
  KEYCLOAK_BASE: "http://{{ .Release.Name }}-keycloak-headless.{{ .Release.Namespace }}:{{ .Values.deployment.keycloak.http }}/auth"
  {{- end }}


TODO:

```
[IHC-DT-A] > kubectl logs -n canvas deployment/canvas-compreg
KEYCLOAK_VALID_ISSUERS_array: {'http://canvas-keycloak.canvas.svc.cluster.local:8083/auth/realms/odari', 'https://canvas-keycloak.ihc-dt-a.cluster-2.de/realms/odari'}
```


```
CANVAS_RESOURCE_INVENTORY=https://canvas-resource-inventory.ihc-dt-a.cluster-2.de/tmf-api/resourceInventoryManagement/v5
OAUTH2_CLIENT_SECRET=WooMy0BuOlFjBEOTktWjFOlluLJOoBR9
OAUTH2_TOKEN_URL=https://canvas-keycloak.ihc-dt-a.cluster-2.de/realms/odari/protocol/openid-connect/token

# Keycloak Configuration
KEYCLOAK_URL=https://canvas-keycloak.ihc-dt-a.cluster-2.de/realms/odari
KEYCLOAK_CLIENT_SECRET=WooMy0BuOlFjBEOTktWjFOlluLJOoBR9
KEYCLOAK_VALID_ISSUERS=https://canvas-keycloak.ihc-dt-a.cluster-2.de/realms/odari
```
