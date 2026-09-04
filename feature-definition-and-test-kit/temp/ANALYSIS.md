# custom resources

```
[IHC-DT-A] > kubectl get depapis,exposedapis,components -A
NAMESPACE    NAME                                                                                         READY   AGE     SVCINVID                               URL
components   dependentapi.oda.tmforum.org/ctk-productcatalogmanagement-downstreamproductcatalog-v4        true    3m47s   fbdfa578-3b3d-49c0-8228-76d8055affbd   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
components   dependentapi.oda.tmforum.org/ctk-productcatalogmanagement-downstreamuserrolepermissions-v4           3m5s

NAMESPACE    NAME                                                                                  API_ENDPOINT                                                                             IMPLEMENTATION_READY
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-metrics                       https://34.51.232.176/ctk-productcatalogmanagement/metrics                               true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-productcatalogmanagement-v4   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4   true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-userrolesandpermissions-v5    https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5      true

NAMESPACE    NAME                                                     DEPLOYMENT_STATUS
components   component.oda.tmforum.org/ctk-productcatalogmanagement   In-Progress-DepApi
```


# helm list

```
[IHC-DT-A] > helm list -A
NAME                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                                           APP VERSION
canvas                  canvas          1               2026-06-02 13:46:37.7613719 +0200 CEST  deployed        canvas-oda-1.2.6-rc1                            v1
canvas-vs               istio-gateway   2               2026-06-01 20:44:10.0970694 +0200 CEST  deployed        virtual-services-for-canvas-0.1.0               0.1.0
code-server             code-server     2               2026-01-15 08:05:13.2103139 +0100 CET   deployed        code-server-3.32.0                              4.108.0
ctk                     components      87              2026-06-12 23:08:35.375601786 +0000 UTC deployed        productcatalog-sec-dependent-API-v1-0.0.1       1.0
global-compreg-vs       compreg         1               2026-05-27 18:02:37.2105184 +0200 CEST  deployed        component-registry-0.1.0                        v1
ihcdta-gateway          istio-gateway   1               2026-05-03 18:50:29.1548777 +0200 CEST  deployed        canvas-component-gateway-1.0.0                  v1
istio-base              istio-system    1               2026-01-12 22:41:18.064933 +0100 CET    deployed        base-1.28.2                                     1.28.2
istio-ingress           istio-ingress   1               2026-01-12 22:42:12.301281 +0100 CET    deployed        gateway-1.28.2                                  1.28.2
istiod                  istio-system    1               2026-01-12 22:41:36.9929332 +0100 CET   deployed        istiod-1.28.2                                   1.28.2
other-vs                default         2               2026-05-03 18:52:21.0698621 +0200 CEST  deployed        virtual-services-for-others-0.1.0               0.1.0
```

# dependent apis yaml

```
apiVersion: v1
items:
- apiVersion: oda.tmforum.org/v1
  kind: DependentAPI
  metadata:
    annotations:
      kopf.zalando.org/last-handled-configuration: |
        {"spec":{"apiType":"openapi","name":"downstreamproductcatalog","segment":"coreFunction","specification":{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json","version":"v4"}},"metadata":{"labels":{"app.kubernetes.io/managed-by":"Helm","oda.tmforum.org/componentName":"ctk-productcatalogmanagement"}},"status":{"implementation":{"ready":true}}}
    creationTimestamp: "2026-06-12T23:07:56Z"
    finalizers:
    - kopf.zalando.org/KopfFinalizerMarker
    generateName: ctk-productcatalogmanagement-
    generation: 4
    labels:
      app.kubernetes.io/managed-by: Helm
      oda.tmforum.org/componentName: ctk-productcatalogmanagement
    name: ctk-productcatalogmanagement-downstreamproductcatalog-v4
    namespace: components
    ownerReferences:
    - apiVersion: oda.tmforum.org/v1
      blockOwnerDeletion: true
      controller: true
      kind: Component
      name: ctk-productcatalogmanagement
      uid: 8f27cc57-881a-42ee-a197-a3922611b31e
    resourceVersion: "1781305677810447003"
    uid: 545fb2e3-b621-405d-ab09-9ef97f13d337
  spec:
    apiType: openapi
    name: downstreamproductcatalog
    segment: coreFunction
    specification:
      url: https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json
      version: v4
  status:
    depapiStatus:
      svcInvID: fbdfa578-3b3d-49c0-8228-76d8055affbd
      url: https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
    implementation:
      ready: true
    kopf:
      progress: {}
- apiVersion: oda.tmforum.org/v1
  kind: DependentAPI
  metadata:
    annotations:
      kopf.zalando.org/last-handled-configuration: |
        {"spec":{"apiType":"openapi","id":null,"name":"downstreamuserrolepermissions","segment":"securityFunction","specification":{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json","version":"v4"}},"metadata":{"labels":{"app.kubernetes.io/managed-by":"Helm","oda.tmforum.org/componentName":"ctk-productcatalogmanagement"}}}
    creationTimestamp: "2026-06-12T23:08:38Z"
    finalizers:
    - kopf.zalando.org/KopfFinalizerMarker
    generateName: ctk-productcatalogmanagement-
    generation: 1
    labels:
      app.kubernetes.io/managed-by: Helm
      oda.tmforum.org/componentName: ctk-productcatalogmanagement
    name: ctk-productcatalogmanagement-downstreamuserrolepermissions-v4
    namespace: components
    ownerReferences:
    - apiVersion: oda.tmforum.org/v1
      blockOwnerDeletion: true
      controller: true
      kind: Component
      name: ctk-productcatalogmanagement
      uid: 8f27cc57-881a-42ee-a197-a3922611b31e
    resourceVersion: "1781305718926047008"
    uid: a0a6f9b8-3fa3-4c23-a0a6-8932ffe1c862
  spec:
    apiType: openapi
    id: null
    name: downstreamuserrolepermissions
    segment: securityFunction
    specification:
      url: https://raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json
      version: v4
kind: List
metadata:
  resourceVersion: ""
```

# components yaml:

```
apiVersion: v1
items:
- apiVersion: oda.tmforum.org/v1
  kind: Component
  metadata:
    annotations:
      kopf.zalando.org/last-handled-configuration: |
        {"spec":{"componentMetadata":{"description":"Simple Product Catalog ODA-Component with TMF634 DependentAPI in managementFunction.","functionalBlock":"CoreCommerce","id":"TMFC001","maintainers":[{"email":"lester.thomas@vodafone.com","name":"Lester Thomas"}],"name":"productcatalogmanagement","owners":[{"email":"lester.thomas@vodafone.com","name":"Lester Thomas"}],"publicationDate":"2024-09-17T00:00:00.000Z","status":"specified","version":"0.0.1"},"coreFunction":{"dependentAPIs":[{"apiType":"openapi","name":"downstreamproductcatalog","specification":[{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"}]}],"exposedAPIs":[{"apiType":"openapi","developerUI":"/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs","implementation":"ctk-prodcatapi","name":"productcatalogmanagement","path":"/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4","port":8080,"specification":[{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"}]}]},"eventNotification":{"publishedEvents":[],"subscribedEvents":[]},"managementFunction":{"dependentAPIs":[{"apiType":"openapi","name":"downstreamresourcecatalog","specification":[{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF634_ResourceCatalog/master/TMF634-ResourceCatalog-v4.0.0.swagger.json"}]}],"exposedAPIs":[{"apiType":"prometheus","implementation":"ctk-productcatalogmanagement-sm","name":"metrics","path":"/ctk-productcatalogmanagement/metrics","port":4000}]},"securityFunction":{"canvasSystemRole":"Admin","exposedAPIs":[{"apiType":"openapi","developerUI":"/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs","gatewayConfiguration":{"CORS":{"allowCredentials":false,"allowOrigins":"https://allowed-origin.com, https://allowed-origin2.com","enabled":false,"handlePreflightRequests":{"allowHeaders":"Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers","allowMethods":"GET, POST","enabled":false,"maxAge":36000}},"OASValidation":{"allowUnspecifiedCookies":false,"allowUnspecifiedHeaders":false,"allowUnspecifiedQueryParams":false,"requestEnabled":false,"responseEnabled":false},"apiKeyVerification":{"enabled":false,"location":"header"},"quota":{"identifier":"","limit":""},"rateLimit":{"enabled":false,"identifier":"IP","interval":"pm","limit":"6"},"template":""},"implementation":"ctk-permissionspecapi","name":"userrolesandpermissions","path":"/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5","port":8080,"specification":[{"url":"https://raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermissions/master/TMF672-UserRolePermissions-v5.0.0.swagger.json"}]}]}},"metadata":{"labels":{"app.kubernetes.io/managed-by":"Helm","oda.tmforum.org/componentName":"ctk-productcatalogmanagement"},"annotations":{"meta.helm.sh/release-name":"ctk","meta.helm.sh/release-namespace":"components"}},"status":{"coreAPIs":[{"developerUI":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs","implementation":"ctk-prodcatapi","ip":"34.51.232.176","name":"ctk-productcatalogmanagement-productcatalogmanagement-v4","path":"/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4","port":8080,"ready":true,"uid":"d56a6df5-aa0f-43a5-b8c8-e8e76ef2941b","url":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4"}],"coreDependentAPIs":[{"name":"ctk-productcatalogmanagement-downstreamproductcatalog-v4","ready":true,"uid":"545fb2e3-b621-405d-ab09-9ef97f13d337","url":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4"}],"identityConfig":{"identityProvider":"Keycloak","listenerRegistered":true},"identityConfig/status.summary/status.deployment_status":"identityConfig resource unchanged","managementAPIs":[{"implementation":"ctk-productcatalogmanagement-sm","ip":"34.51.232.176","name":"ctk-productcatalogmanagement-metrics","path":"/ctk-productcatalogmanagement/metrics","port":4000,"ready":true,"uid":"f7eff3c2-e57e-4124-ab87-ac6bd9334acf","url":"https://34.51.232.176/ctk-productcatalogmanagement/metrics"}],"managementDependentAPIs":[],"publishedEvents":[],"securityAPIs":[{"developerUI":"https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs","implementation":"ctk-permissionspecapi","ip":"34.51.232.176","name":"ctk-productcatalogmanagement-userrolesandpermissions-v5","path":"/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5","port":8080,"ready":true,"uid":"0adc1041-7260-4372-becc-a91e16789397","url":"https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5"}],"securityDependentAPIs":[],"securitySecretsManagement":{},"subscribedEvents":[],"summary/status":{"coreAPIsummary":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4 ","coreDependentAPIsummary":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4 ","deployment_status":"Complete","developerUIsummary":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs ","managementAPIsummary":"https://34.51.232.176/ctk-productcatalogmanagement/metrics ","managementDependentAPIsummary":"","securityAPIsummary":"https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5 ","securityDependentAPIsummary":"","securitySecretsManagementSummary":""}}}
      meta.helm.sh/release-name: ctk
      meta.helm.sh/release-namespace: components
    creationTimestamp: "2026-06-12T11:09:31Z"
    generation: 1240
    labels:
      app.kubernetes.io/managed-by: Helm
      oda.tmforum.org/componentName: ctk-productcatalogmanagement
    name: ctk-productcatalogmanagement
    namespace: components
    resourceVersion: "1781305681033615021"
    uid: 8f27cc57-881a-42ee-a197-a3922611b31e
  spec:
    componentMetadata:
      description: Simple Product Catalog ODA-Component with TMF634 DependentAPI in
        managementFunction.
      functionalBlock: CoreCommerce
      id: TMFC001
      maintainers:
      - email: lester.thomas@vodafone.com
        name: Lester Thomas
      name: productcatalogmanagement
      owners:
      - email: lester.thomas@vodafone.com
        name: Lester Thomas
      publicationDate: "2024-09-17T00:00:00.000Z"
      status: specified
      version: 0.0.1
    coreFunction:
      dependentAPIs:
      - apiType: openapi
        name: downstreamproductcatalog
        specification:
        - url: https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json
      exposedAPIs:
      - apiType: openapi
        developerUI: /ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs
        implementation: ctk-prodcatapi
        name: productcatalogmanagement
        path: /ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
        port: 8080
        specification:
        - url: https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json
    eventNotification:
      publishedEvents: []
      subscribedEvents: []
    managementFunction:
      dependentAPIs:
      - apiType: openapi
        name: downstreamresourcecatalog
        specification:
        - url: https://raw.githubusercontent.com/tmforum-apis/TMF634_ResourceCatalog/master/TMF634-ResourceCatalog-v4.0.0.swagger.json
      exposedAPIs:
      - apiType: prometheus
        implementation: ctk-productcatalogmanagement-sm
        name: metrics
        path: /ctk-productcatalogmanagement/metrics
        port: 4000
    securityFunction:
      canvasSystemRole: Admin
      exposedAPIs:
      - apiType: openapi
        developerUI: /ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs
        gatewayConfiguration:
          CORS:
            allowCredentials: false
            allowOrigins: https://allowed-origin.com, https://allowed-origin2.com
            enabled: false
            handlePreflightRequests:
              allowHeaders: Accept, X-Requested-With, Content-Type, Access-Control-Request-Method,
                Access-Control-Request-Headers
              allowMethods: GET, POST
              enabled: false
              maxAge: 36000
          OASValidation:
            allowUnspecifiedCookies: false
            allowUnspecifiedHeaders: false
            allowUnspecifiedQueryParams: false
            requestEnabled: false
            responseEnabled: false
          apiKeyVerification:
            enabled: false
            location: header
          quota:
            identifier: ""
            limit: ""
          rateLimit:
            enabled: false
            identifier: IP
            interval: pm
            limit: "6"
          template: ""
        implementation: ctk-permissionspecapi
        name: userrolesandpermissions
        path: /ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5
        port: 8080
        specification:
        - url: https://raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermissions/master/TMF672-UserRolePermissions-v5.0.0.swagger.json
  status:
    coreAPIs:
    - developerUI: https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs
      implementation: ctk-prodcatapi
      ip: 34.51.232.176
      name: ctk-productcatalogmanagement-productcatalogmanagement-v4
      path: /ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
      port: 8080
      ready: true
      uid: d56a6df5-aa0f-43a5-b8c8-e8e76ef2941b
      url: https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
    coreDependentAPIs:
    - name: ctk-productcatalogmanagement-downstreamproductcatalog-v4
      ready: true
      uid: 545fb2e3-b621-405d-ab09-9ef97f13d337
      url: https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
    identityConfig:
      identityProvider: Keycloak
      listenerRegistered: true
    identityConfig/status.summary/status.deployment_status: identityConfig resource
      unchanged
    kopf:
      progress: {}
    managementAPIs:
    - implementation: ctk-productcatalogmanagement-sm
      ip: 34.51.232.176
      name: ctk-productcatalogmanagement-metrics
      path: /ctk-productcatalogmanagement/metrics
      port: 4000
      ready: true
      uid: f7eff3c2-e57e-4124-ab87-ac6bd9334acf
      url: https://34.51.232.176/ctk-productcatalogmanagement/metrics
    managementDependentAPIs: []
    publishedEvents: []
    securityAPIs:
    - developerUI: https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs
      implementation: ctk-permissionspecapi
      ip: 34.51.232.176
      name: ctk-productcatalogmanagement-userrolesandpermissions-v5
      path: /ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5
      port: 8080
      ready: true
      uid: 0adc1041-7260-4372-becc-a91e16789397
      url: https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5
    securityDependentAPIs: []
    securitySecretsManagement: {}
    subscribedEvents: []
    summary/status:
      coreAPIsummary: 'https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4 '
      coreDependentAPIsummary: 'https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4 '
      deployment_status: Complete
      developerUIsummary: 'https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs
        https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5/docs '
      managementAPIsummary: 'https://34.51.232.176/ctk-productcatalogmanagement/metrics '
      managementDependentAPIsummary: ""
      securityAPIsummary: 'https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5 '
      securityDependentAPIsummary: ""
      securitySecretsManagementSummary: ""
kind: List
metadata:
  resourceVersion: ""
```

# Component-Operator log

```
[2026-06-12 23:07:43,262] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:43,264] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:43,445] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:43,445] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:43,610] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:43,611] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:43,766] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:43,767] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:43,767] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Deleting DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4 (coreDependentAPIs): 
[2026-06-12 23:07:43,767] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|deleteDependentAPI] Deleting DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:43,794] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status []: 
[2026-06-12 23:07:43,934] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:43,934] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:43,935] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:44,072] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:44,072] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:44,072] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Deleting DependentAPI ctk-productcatalogmanagement-downstreamuserrolepermissions-v4 (securityDependentAPIs): 
[2026-06-12 23:07:44,072] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|deleteDependentAPI] Deleting DependentAPI ctk-productcatalogmanagement-downstreamuserrolepermissions-v4: 
[2026-06-12 23:07:44,097] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:44,238] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:44,239] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:44,375] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:44,512] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:44,652] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:44,652] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:44,652] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:44,788] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:44,789] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:45,147] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:45,147] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:45,308] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:45,308] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status []: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:45,746] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:45,747] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,747] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:45,892] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:45,892] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:46,032] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:46,181] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:46,321] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:46,322] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:46,323] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:55,634] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_service|adopt_service] adopt_service handler called: 
[2026-06-12 23:07:55,716] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_service|adopt_service] Adding component as parent of service: 
[2026-06-12 23:07:55,870] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_deployment|adopt_deployment] adopt_deployment handler called: 
[2026-06-12 23:07:55,912] kopf.objects         [ERROR   ] [components/ctk-promgmtapi] Handler 'adopt_deployment' failed temporarily: Conflict updating deployment.
[2026-06-12 23:07:55,951] kopf.objects         [WARNING ] [components/ctk-promgmtapi] Patching failed with inconsistencies: (('remove', ('status', 'kopf'), {'progress': {'adopt_deployment': {'started': '2026-06-12T23:07:55.869916+00:00', 'stopped': None, 'delayed': '2026-06-12T23:08:55.913450+00:00', 'purpose': 'create', 'retries': 1, 'success': False, 'failure': False, 'message': 'Conflict updating deployment.', 'subrefs': None}}}, None),)
[2026-06-12 23:07:55,961] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:55,961] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:56,327] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:56,327] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:56,689] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:56,690] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Calling createDependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4 (coreDependentAPIs): 
[2026-06-12 23:07:56,843] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] Creating DependentAPI Custom Object {'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'DependentAPI', 'metadata'; {'ownerReferences'; [{'controller'; True, 'blockOwnerDeletion'; True, 'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'Component', 'name'; 'ctk-productcatalogmanagement', 'uid'; '8f27cc57-881a-42ee-a197-a3922611b31e'}], 'generateName'; 'ctk-productcatalogmanagement-', 'namespace'; 'components', 'labels'; {'app.kubernetes.io/managed-by'; 'Helm', 'oda.tmforum.org/componentName'; 'ctk-productcatalogmanagement'}, 'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4'}, 'spec'; {'name'; 'downstreamproductcatalog', 'apiType'; 'openapi', 'id'; None, 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}, 'segment'; 'coreFunction'}}: 
[2026-06-12 23:07:56,865] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] DependentAPI Resource created ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:56,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'ready'; False}]: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,157] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:57,446] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:57,591] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:57,732] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:07:57,911] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:57,912] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:58,226] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:58,227] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:07:58,525] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:58,809] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:58,810] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:58,949] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:59,096] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:00,063] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,373] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:00,718] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:00,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:01,012] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:08:36,991] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:08:36,991] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:08:37,358] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:08:37,358] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:08:37,515] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:08:37,516] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:38,251] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:38,252] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:38,252] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamuserrolepermissions', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Calling createDependentAPI ctk-productcatalogmanagement-downstreamuserrolepermissions-v4 (securityDependentAPIs): 
[2026-06-12 23:08:38,393] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|createDependentAPIResource] Creating DependentAPI Custom Object {'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'DependentAPI', 'metadata'; {'ownerReferences'; [{'controller'; True, 'blockOwnerDeletion'; True, 'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'Component', 'name'; 'ctk-productcatalogmanagement', 'uid'; '8f27cc57-881a-42ee-a197-a3922611b31e'}], 'generateName'; 'ctk-productcatalogmanagement-', 'namespace'; 'components', 'labels'; {'app.kubernetes.io/managed-by'; 'Helm', 'oda.tmforum.org/componentName'; 'ctk-productcatalogmanagement'}, 'name'; 'ctk-productcatalogmanagement-downstreamuserrolepermissions-v4'}, 'spec'; {'name'; 'downstreamuserrolepermissions', 'apiType'; 'openapi', 'id'; None, 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'version'; 'v4'}, 'segment'; 'securityFunction'}}: 
[2026-06-12 23:08:38,413] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|createDependentAPIResource] DependentAPI Resource created ctk-productcatalogmanagement-downstreamuserrolepermissions-v4: 
[2026-06-12 23:08:38,414] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamuserrolepermissions-v4', 'uid'; 'a0a6f9b8-3fa3-4c23-a0a6-8932ffe1c862', 'ready'; False}]: 
[2026-06-12 23:08:38,558] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:38,558] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:38,697] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:38,838] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:08:39,126] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:08:39,126] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:08:39,493] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:08:39,493] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:08:39,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:08:39,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:39,803] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:39,803] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:39,803] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:39,804] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:39,945] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:39,945] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:39,945] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:40,083] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:40,084] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamuserrolepermissions', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:40,084] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamuserrolepermissions-v4: 
[2026-06-12 23:08:40,085] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamuserrolepermissions-v4', 'ready'; False, 'uid'; 'a0a6f9b8-3fa3-4c23-a0a6-8932ffe1c862'}]: 
[2026-06-12 23:08:40,227] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:40,227] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:40,371] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:40,512] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:40,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:40,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:40,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:08:55,962] kopf.objects         [WARNING ] [components/ctk-promgmtapi] Patching failed with inconsistencies: (('remove', ('status', 'kopf'), {'dummy': '2026-06-12T23:08:55.917116+00:00'}, None),)
[2026-06-12 23:08:56,123] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_deployment|adopt_deployment] adopt_deployment handler called: 
[2026-06-12 23:08:56,176] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_deployment|adopt_deployment] Adding component as parent of deployment: 
```

# npm run log

```
coder@code-server-76dd65f46f-nqhz2:~/git/oda-canvas/feature-definition-and-test-kit$ npm run start:tags -- "@UC002-F001" 

> oda-canvas-bdd-tests@0.0.1 start:tags
> cucumber-js --publish --format json:/tmp/cucumber.json --tags @UC002-F001

Resource Inventory TMF639 with RESOURCE_INVENTORY_BASE_URL: http://resource-inventory.canvas.svc.cluster.local/tmf-api/resourceInventoryManagement/v5


============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create ExposedAPI resources for each segment
.
=== Starting Package ExposedAPI Verification ===
Verifying package 'productcatalog-v1' has 1 ExposedAPI(s) in 'coreFunction' segment
✅ Successfully verified 1 ExposedAPI(s) in 'coreFunction' segment
=== Package ExposedAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:07:41 2026
NAMESPACE: components
STATUS: deployed
REVISION: 82
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete'...
.
=== Starting ExposedAPI Resource Verification ===
Verifying ExposedAPI 'productcatalogmanagement' on component 'ctk-productcatalogmanagement'
_findApiResource called with plural=exposedapis, apiName=productcatalogmanagement, componentName=ctk-productcatalogmanagement, namespace=components, options={"segmentName":"coreFunction"}, kindHint=ExposedAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-productcatalogmanagement
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-metrics","ctk-productcatalogmanagement-productcatalogmanagement-v4","ctk-productcatalogmanagement-userrolesandpermissions-v5"]
3) filter apiName=productcatalogmanagement in candidates by spec.name
POOL: ["ctk-productcatalogmanagement-productcatalogmanagement-v4"]
✅ Successfully found ExposedAPI 'productcatalogmanagement' on component 'ctk-productcatalogmanagement' after 237ms
=== ExposedAPI Resource Verification Complete ===
....

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create ExposedAPI resources for each segment
.
=== Starting Package ExposedAPI Verification ===
Verifying package 'productcatalog-v1' has 1 ExposedAPI(s) in 'managementFunction' segment
✅ Successfully verified 1 ExposedAPI(s) in 'managementFunction' segment
=== Package ExposedAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:07:45 2026
NAMESPACE: components
STATUS: deployed
REVISION: 83
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete'...
.
=== Starting ExposedAPI Resource Verification ===
Verifying ExposedAPI 'metrics' on component 'ctk-productcatalogmanagement'
_findApiResource called with plural=exposedapis, apiName=metrics, componentName=ctk-productcatalogmanagement, namespace=components, options={"segmentName":"managementFunction"}, kindHint=ExposedAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-metrics
✅ Successfully found ExposedAPI 'metrics' on component 'ctk-productcatalogmanagement' after 223ms
=== ExposedAPI Resource Verification Complete ===
....

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create ExposedAPI resources for each segment
.
=== Starting Package ExposedAPI Verification ===
Verifying package 'productcatalog-v1' has 1 ExposedAPI(s) in 'securityFunction' segment
✅ Successfully verified 1 ExposedAPI(s) in 'securityFunction' segment
=== Package ExposedAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:07:49 2026
NAMESPACE: components
STATUS: deployed
REVISION: 84
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete'...
.
=== Starting ExposedAPI Resource Verification ===
Verifying ExposedAPI 'userrolesandpermissions' on component 'ctk-productcatalogmanagement'
_findApiResource called with plural=exposedapis, apiName=userrolesandpermissions, componentName=ctk-productcatalogmanagement, namespace=components, options={"segmentName":"securityFunction"}, kindHint=ExposedAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-userrolesandpermissions
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-metrics","ctk-productcatalogmanagement-productcatalogmanagement-v4","ctk-productcatalogmanagement-userrolesandpermissions-v5"]
3) filter apiName=userrolesandpermissions in candidates by spec.name
POOL: ["ctk-productcatalogmanagement-userrolesandpermissions-v5"]
✅ Successfully found ExposedAPI 'userrolesandpermissions' on component 'ctk-productcatalogmanagement' after 448ms
=== ExposedAPI Resource Verification Complete ===
....

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create DependentAPI resources for each segment
.
=== Starting Package DependentAPI Verification ===
Verifying package 'productcatalog-dependendent-API-v1' has 1 DependentAPI(s) in 'coreFunction' segment
✅ Successfully verified 1 DependentAPI(s) in 'coreFunction' segment
=== Package DependentAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-dependendent-API-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:07:54 2026
NAMESPACE: components
STATUS: deployed
REVISION: 85
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete' or 'In-Progress-DepApi'...
._findApiResource called with plural=dependentapis, apiName=downstreamproductcatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamproductcatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamproductcatalog in candidates by spec.name
POOL: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
....

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create DependentAPI resources for each segment
.
=== Starting Package DependentAPI Verification ===
Verifying package 'productcatalog-mgmt-dependent-API-v1' has 1 DependentAPI(s) in 'managementFunction' segment
✅ Successfully verified 1 DependentAPI(s) in 'managementFunction' segment
=== Package DependentAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-mgmt-dependent-API-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:07:58 2026
NAMESPACE: components
STATUS: deployed
REVISION: 86
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete' or 'In-Progress-DepApi'...
._findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
_findApiResource called with plural=dependentapis, apiName=downstreamresourcecatalog, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamresourcecatalog
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4"]
3) filter apiName=downstreamresourcecatalog in candidates by spec.name
Waiting for DependentAPI 'downstreamresourcecatalog' on component 'ctk-productcatalogmanagement' in namespace components...
F
=== AUTO DEBUG after failed scenario ===

--- Component-Operator logs ---
[2026-06-12 23:07:44,652] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:44,652] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:44,788] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:44,789] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:45,147] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:45,147] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:45,308] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:45,308] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,463] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status []: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,604] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:45,746] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:45,747] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:45,747] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:45,892] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:45,892] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:46,032] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:46,181] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:46,321] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:46,322] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:46,323] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:55,634] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_service|adopt_service] adopt_service handler called: 
[2026-06-12 23:07:55,716] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_service|adopt_service] Adding component as parent of service: 
[2026-06-12 23:07:55,870] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|adopt_deployment|adopt_deployment] adopt_deployment handler called: 
[2026-06-12 23:07:55,912] kopf.objects         [ERROR   ] [components/ctk-promgmtapi] Handler 'adopt_deployment' failed temporarily: Conflict updating deployment.
[2026-06-12 23:07:55,951] kopf.objects         [WARNING ] [components/ctk-promgmtapi] Patching failed with inconsistencies: (('remove', ('status', 'kopf'), {'progress': {'adopt_deployment': {'started': '2026-06-12T23:07:55.869916+00:00', 'stopped': None, 'delayed': '2026-06-12T23:08:55.913450+00:00', 'purpose': 'create', 'retries': 1, 'success': False, 'failure': False, 'message': 'Conflict updating deployment.', 'subrefs': None}}}, None),)
[2026-06-12 23:07:55,961] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:55,961] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:56,327] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:56,327] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:56,689] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:56,690] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Calling createDependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4 (coreDependentAPIs): 
[2026-06-12 23:07:56,843] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] Creating DependentAPI Custom Object {'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'DependentAPI', 'metadata'; {'ownerReferences'; [{'controller'; True, 'blockOwnerDeletion'; True, 'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'Component', 'name'; 'ctk-productcatalogmanagement', 'uid'; '8f27cc57-881a-42ee-a197-a3922611b31e'}], 'generateName'; 'ctk-productcatalogmanagement-', 'namespace'; 'components', 'labels'; {'app.kubernetes.io/managed-by'; 'Helm', 'oda.tmforum.org/componentName'; 'ctk-productcatalogmanagement'}, 'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4'}, 'spec'; {'name'; 'downstreamproductcatalog', 'apiType'; 'openapi', 'id'; None, 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}, 'segment'; 'coreFunction'}}: 
[2026-06-12 23:07:56,865] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] DependentAPI Resource created ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:56,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'ready'; False}]: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,157] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:57,446] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:57,591] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:57,732] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:07:57,911] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:57,912] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:58,226] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:58,227] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:07:58,525] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:58,809] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:58,810] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:58,949] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:59,096] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:00,063] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,373] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:00,718] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:00,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:01,012] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 


--- Dependent APIs Debug Info ---
NAMESPACE    NAME                                                                                    READY   AGE   SVCINVID                               URL
components   dependentapi.oda.tmforum.org/ctk-productcatalogmanagement-downstreamproductcatalog-v4   true    38s   fbdfa578-3b3d-49c0-8228-76d8055affbd   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4

NAMESPACE    NAME                                                                                  API_ENDPOINT                                                                             IMPLEMENTATION_READY
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-metrics                       https://34.51.232.176/ctk-productcatalogmanagement/metrics                               true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-productcatalogmanagement-v4   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4   true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-userrolesandpermissions-v5    https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5      true

NAMESPACE    NAME                                                     DEPLOYMENT_STATUS
components   component.oda.tmforum.org/ctk-productcatalogmanagement   Complete


--- info service ---

[{"serviceType":"API","name":"unknown","description":"Implementation of unknown Open API","state":"active","serviceCharacteristic":[{"name":"componentName","valueType":"string","value":"ctk-productcatalogmanagement","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","value":"downstreamproductcatalog","@type":"StringCharacteristic"},{"name":"url","valueType":"string","value":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4","@type":"StringCharacteristic"},{"name":"OASSpecification","valueType":"string","value":"{'url': 'https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version': 'v4'}","@type":"StringCharacteristic"}],"serviceSpecification":{"id":"1","name":"API","version":"1.0.0","@type":"ServiceSpecification","specCharacteristic":[{"name":"componentName","valueType":"string","description":"The name of the component which wants to consume the API service. The component name is normally available in the environment vaiable COMPONENT_NAME","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","description":"The dependency name that this API service matches. The dependency name is set in the Component Specification","@type":"StringCharacteristic"},{"name":"url","valueType":"string","description":"The url the the API root endpoint","@type":"StringCharacteristic"},{"name":"OASSpecification","valueType":"string","description":"The url to the Open API Specification for this API","@type":"StringCharacteristic"}]},"@type":"Service","@schemaLocation":"http://info.cavas.svc.cluster.local/openapi#/components.schemas.Service","@baseType":"Service","id":"fbdfa578-3b3d-49c0-8228-76d8055affbd","href":"http://info.canvas.svc.cluster.local/service/fbdfa578-3b3d-49c0-8228-76d8055affbd"}]
NAME                           DEPLOYMENT_STATUS
ctk-productcatalogmanagement   Complete

=== End AUTO DEBUG ===
...

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Create DependentAPI resources for each segment
.
=== Starting Package DependentAPI Verification ===
Verifying package 'productcatalog-sec-dependent-API-v1' has 1 DependentAPI(s) in 'securityFunction' segment
✅ Successfully verified 1 DependentAPI(s) in 'securityFunction' segment
=== Package DependentAPI Verification Complete ===
.
helm upgrade ctk ./testData/productcatalog-sec-dependent-API-v1 -n components { encoding: 'utf-8' }
helm output: Release "ctk" has been upgraded. Happy Helming!
NAME: ctk
LAST DEPLOYED: Fri Jun 12 23:08:35 2026
NAMESPACE: components
STATUS: deployed
REVISION: 87
TEST SUITE: None

.Waiting for component 'ctk-productcatalogmanagement' in namespace 'components' to have deployment status 'Complete' or 'In-Progress-DepApi'...
._findApiResource called with plural=dependentapis, apiName=downstreamuserrolepermissions, componentName=ctk-productcatalogmanagement, namespace=components, options={}, kindHint=DependentAPI
1) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, name=ctk-productcatalogmanagement-downstreamuserrolepermissions
2) listNamespacedCustomObject(g=oda.tmforum.org, v=v1, ns=components, labelSelector=oda.tmforum.org/componentName=ctk-productcatalogmanagement
CANDIDATES: ["ctk-productcatalogmanagement-downstreamproductcatalog-v4","ctk-productcatalogmanagement-downstreamuserrolepermissions-v4"]
3) filter apiName=downstreamuserrolepermissions in candidates by spec.name
POOL: ["ctk-productcatalogmanagement-downstreamuserrolepermissions-v4"]
....

============================================================================
Feature:    UC002-F001 Install Component
Tags:       @UC002, @UC002-F001
Scenario:   Debug Logging 2
.
=== Start log of Deployment 'component-operator' in namespace {namespace} ===
[2026-06-12 23:07:56,327] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:56,689] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:56,690] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:56,842] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Calling createDependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4 (coreDependentAPIs): 
[2026-06-12 23:07:56,843] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] Creating DependentAPI Custom Object {'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'DependentAPI', 'metadata'; {'ownerReferences'; [{'controller'; True, 'blockOwnerDeletion'; True, 'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'Component', 'name'; 'ctk-productcatalogmanagement', 'uid'; '8f27cc57-881a-42ee-a197-a3922611b31e'}], 'generateName'; 'ctk-productcatalogmanagement-', 'namespace'; 'components', 'labels'; {'app.kubernetes.io/managed-by'; 'Helm', 'oda.tmforum.org/componentName'; 'ctk-productcatalogmanagement'}, 'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4'}, 'spec'; {'name'; 'downstreamproductcatalog', 'apiType'; 'openapi', 'id'; None, 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}, 'segment'; 'coreFunction'}}: 
[2026-06-12 23:07:56,865] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|createDependentAPIResource] DependentAPI Resource created ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:56,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'ready'; False}]: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,007] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:57,156] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:57,157] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:57,304] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:57,446] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:57,591] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:57,731] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:57,732] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:07:57,911] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:57,912] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:58,069] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:58,226] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:58,227] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:07:58,384] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:07:58,525] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,526] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:07:58,667] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:07:58,809] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:07:58,810] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:07:58,949] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:07:59,096] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:07:59,248] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:07:59,387] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:07:59,548] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:07:59,907] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:00,063] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:00,064] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,209] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:00,372] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:00,373] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status []: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:00,518] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:00,718] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:00,866] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:01,012] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:01,013] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status Complete: 
[2026-06-12 23:08:36,991] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:08:36,991] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:08:37,358] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:08:37,358] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:08:37,515] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:08:37,516] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] coreDependentAPIs handler called: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamproductcatalog', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] TODO; Update DependentAPI ctk-productcatalogmanagement-downstreamproductcatalog-v4: 
[2026-06-12 23:08:37,873] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreDependentAPIs|coreDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamproductcatalog-v4', 'ready'; True, 'uid'; '545fb2e3-b621-405d-ab09-9ef97f13d337', 'url'; 'https;//34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4'}]: 
[2026-06-12 23:08:38,251] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] managementDependentAPIs handler called: 
[2026-06-12 23:08:38,252] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] Normalized dependent APIs; []: 
[2026-06-12 23:08:38,252] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementDependentAPIs|managementDependentAPIs] result for status []: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] securityDependentAPIs handler called: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Normalized dependent APIs; [{'name'; 'downstreamuserrolepermissions', 'id'; None, 'version'; 'v4', 'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'apiType'; 'openapi', 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'version'; 'v4'}}]: 
[2026-06-12 23:08:38,392] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] Calling createDependentAPI ctk-productcatalogmanagement-downstreamuserrolepermissions-v4 (securityDependentAPIs): 
[2026-06-12 23:08:38,393] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|createDependentAPIResource] Creating DependentAPI Custom Object {'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'DependentAPI', 'metadata'; {'ownerReferences'; [{'controller'; True, 'blockOwnerDeletion'; True, 'apiVersion'; 'oda.tmforum.org/v1', 'kind'; 'Component', 'name'; 'ctk-productcatalogmanagement', 'uid'; '8f27cc57-881a-42ee-a197-a3922611b31e'}], 'generateName'; 'ctk-productcatalogmanagement-', 'namespace'; 'components', 'labels'; {'app.kubernetes.io/managed-by'; 'Helm', 'oda.tmforum.org/componentName'; 'ctk-productcatalogmanagement'}, 'name'; 'ctk-productcatalogmanagement-downstreamuserrolepermissions-v4'}, 'spec'; {'name'; 'downstreamuserrolepermissions', 'apiType'; 'openapi', 'id'; None, 'specification'; {'url'; 'https;//raw.githubusercontent.com/tmforum-apis/TMF672_UserRolePermission/master/TMF672-UserRolePermission-v4.0.0.swagger.json', 'version'; 'v4'}, 'segment'; 'securityFunction'}}: 
[2026-06-12 23:08:38,413] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|createDependentAPIResource] DependentAPI Resource created ctk-productcatalogmanagement-downstreamuserrolepermissions-v4: 
[2026-06-12 23:08:38,414] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityDependentAPIs|securityDependentAPIs] result for status [{'name'; 'ctk-productcatalogmanagement-downstreamuserrolepermissions-v4', 'uid'; 'a0a6f9b8-3fa3-4c23-a0a6-8932ffe1c862', 'ready'; False}]: 
[2026-06-12 23:08:38,558] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] securitySecretsManagement handler called: 
[2026-06-12 23:08:38,558] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securitySecretsManagement|securitySecretsManagement] result for status {}: 
[2026-06-12 23:08:38,697] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|publishedEvents|publishedEvents] publishedEvents handler called: 
[2026-06-12 23:08:38,838] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|subscribedEvents|subscribedEvents] subscribedEvents handler called: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] summary handler called: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - completed API count3/3: 
[2026-06-12 23:08:38,986] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|summary|summary] Creating summary - deployment status In-Progress-DepApi: 
[2026-06-12 23:08:39,126] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] coreAPIs handler called: 
[2026-06-12 23:08:39,126] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|coreAPIs|coreAPIs] Patching ExposedAPI ctk-productcatalogmanagement-productcatalogmanagement-v4: 
[2026-06-12 23:08:39,493] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] managementAPIs handler called: 
[2026-06-12 23:08:39,493] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|managementAPIs|managementAPIs] Patching ExposedAPI ctk-productcatalogmanagement-metrics: 
[2026-06-12 23:08:39,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] securityAPIs handler called: 
[2026-06-12 23:08:39,649] ComponentOperator    [INFO    ] [ctk-productcatalogmanagement|ctk-productcatalogmanagement|securityAPIs|securityAPIs] Patching ExposedAPI ctk-productcatalogmanagement-userrolesandpermissions-v5: 

=== End log of Deployment 'component-operator' in namespace canvas ===
.
=== Debug info for dependent APIs ===
NAMESPACE    NAME                                                                                         READY   AGE   SVCINVID                               URL
components   dependentapi.oda.tmforum.org/ctk-productcatalogmanagement-downstreamproductcatalog-v4        true    43s   fbdfa578-3b3d-49c0-8228-76d8055affbd   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
components   dependentapi.oda.tmforum.org/ctk-productcatalogmanagement-downstreamuserrolepermissions-v4           1s                                           

NAMESPACE    NAME                                                                                  API_ENDPOINT                                                                             IMPLEMENTATION_READY
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-metrics                       https://34.51.232.176/ctk-productcatalogmanagement/metrics                               true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-productcatalogmanagement-v4   https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4   true
components   exposedapi.oda.tmforum.org/ctk-productcatalogmanagement-userrolesandpermissions-v5    https://34.51.232.176/ctk-productcatalogmanagement/rolesAndPermissionsManagement/v5      true

NAMESPACE    NAME                                                     DEPLOYMENT_STATUS
components   component.oda.tmforum.org/ctk-productcatalogmanagement   In-Progress-DepApi


--- info service ---

[{"serviceType":"API","name":"unknown","description":"Implementation of unknown Open API","state":"active","serviceCharacteristic":[{"name":"componentName","valueType":"string","value":"ctk-productcatalogmanagement","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","value":"downstreamproductcatalog","@type":"StringCharacteristic"},{"name":"url","valueType":"string","value":"https://34.51.232.176/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4","@type":"StringCharacteristic"},{"name":"OASSpecification","valueType":"string","value":"{'url': 'https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json', 'version': 'v4'}","@type":"StringCharacteristic"}],"serviceSpecification":{"id":"1","name":"API","version":"1.0.0","@type":"ServiceSpecification","specCharacteristic":[{"name":"componentName","valueType":"string","description":"The name of the component which wants to consume the API service. The component name is normally available in the environment vaiable COMPONENT_NAME","@type":"StringCharacteristic"},{"name":"dependencyName","valueType":"string","description":"The dependency name that this API service matches. The dependency name is set in the Component Specification","@type":"StringCharacteristic"},{"name":"url","valueType":"string","description":"The url the the API root endpoint","@type":"StringCharacteristic"},{"name":"OASSpecification","valueType":"string","description":"The url to the Open API Specification for this API","@type":"StringCharacteristic"}]},"@type":"Service","@schemaLocation":"http://info.cavas.svc.cluster.local/openapi#/components.schemas.Service","@baseType":"Service","id":"fbdfa578-3b3d-49c0-8228-76d8055affbd","href":"http://info.canvas.svc.cluster.local/service/fbdfa578-3b3d-49c0-8228-76d8055affbd"}]
--- component yaml ---
NAME                           DEPLOYMENT_STATUS
ctk-productcatalogmanagement   In-Progress-DepApi

--- existing data ---
undefined
=== End debug info ===
....

Failures:

1) Scenario: Create DependentAPI resources for each segment # features/UC002-F001-Install-Component.feature:30
   ✔ Before # features/step-definition/ComponentManagementSteps.js:543
   ✔ Given an example package 'productcatalog-mgmt-dependent-API-v1' with '1' DependentAPI in its 'managementFunction' segment # features/step-definition/ComponentManagementSteps.js:88
   ✔ When I install the 'productcatalog-mgmt-dependent-API-v1' package as release 'ctk' # features/step-definition/ComponentManagementSteps.js:190
   ✔ And the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete' or 'In-Progress-DepApi' # features/step-definition/ComponentManagementSteps.js:354
   ✖ Then I should see the 'downstreamresourcecatalog' DependentAPI resource on the 'ctk-productcatalogmanagement' component # features/step-definition/APIManagementSteps.js:88
       AssertionError [ERR_ASSERTION]: The DependentAPI resource should be found within 30000 milliseconds
           + expected - actual

           -false
           +true

           at World.<anonymous> (/home/coder/git/oda-canvas/feature-definition-and-test-kit/features/step-definition/APIManagementSteps.js:104:12)
   ✔ After # features/step-definition/ProductCatalogSteps.js:370
   ✔ After # features/step-definition/ObservabilitySteps.js:346
   ✔ After # features/step-definition/ComponentManagementSteps.js:563

7 scenarios (1 failed, 6 passed)
26 steps (1 failed, 25 passed)
0m58.947s (executing steps: 0m58.819s)
┌──────────────────────────────────────────────────────────────────────────┐
│ View your Cucumber Report at:                                            │
│ https://reports.cucumber.io/reports/5c808b0a-d39f-4685-b742-098d39321dbe │
│                                                                          │
│ This report will self-destruct in 24h.                                   │
└──────────────────────────────────────────────────────────────────────────┘
```
