# Analyze CVEs for TMF638 Service



## CVEs in existing docker image (Canvas-Info-Service)

```
trivy image --scanners vuln --severity CRITICAL tmforumodacanvas/tmf638-service-inventory-api:1.0.0
```

```
tmforumodacanvas/tmf638-service-inventory-api:1.0.0 (debian 12.8)

Total: 230 (CRITICAL: 230)

┌─────────────────────────────┬────────────────┬──────────┬──────────────┬──────────────────────────────┬───────────────────────────────┬──────────────────────────────────────────────────────────────┐
│           Library           │ Vulnerability  │ Severity │    Status    │      Installed Version       │         Fixed Version         │                            Title                             │
├─────────────────────────────┼────────────────┼──────────┼──────────────┼──────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ imagemagick                 │ CVE-2025-53014 │ CRITICAL │ fixed        │ 8:6.9.11.60+dfsg-1.6+deb12u2 │ 8:6.9.11.60+dfsg-1.6+deb12u4  │ ImageMagick: ImageMagick Heap Buffer Overflow                │
│                             │                │          │              │                              │                               │ https://avd.aquasec.com/nvd/cve-2025-53014                   │
│                             ├────────────────┤          │              │                              │                               ├──────────────────────────────────────────────────────────────┤
│                             │ CVE-2025-53101 │          │              │                              │                               │ ImageMagick: ImageMagick Stack Buffer Overflow               │
   ...
├─────────────────────────────┤                │          │              │                              ├───────────────────────────────┤                                                              │
│ zlib1g-dev                  │                │          │              │                              │                               │                                                              │
│                             │                │          │              │                              │                               │                                                              │
│                             │                │          │              │                              │                               │                                                              │
└─────────────────────────────┴────────────────┴──────────┴──────────────┴──────────────────────────────┴───────────────────────────────┴──────────────────────────────────────────────────────────────┘

Node.js (node-pkg)

Total: 10 (CRITICAL: 10)

┌────────────────────────────────┬────────────────┬──────────┬────────┬───────────────────┬─────────────────────┬──────────────────────────────────────────────────────────────┐
│            Library             │ Vulnerability  │ Severity │ Status │ Installed Version │    Fixed Version    │                            Title                             │
├────────────────────────────────┼────────────────┼──────────┼────────┼───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ fast-xml-parser (package.json) │ CVE-2026-25896 │ CRITICAL │ fixed  │ 4.5.1             │ 5.3.5, 4.5.4        │ fast-xml-parser: fast-xml-parser: Cross-Site Scripting (XSS) │
│                                │                │          │        │                   │                     │ due to improper DOCTYPE entity handling                      │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-25896                   │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ form-data (package.json)       │ CVE-2025-7783  │          │        │ 2.3.3             │ 2.5.4, 3.0.4, 4.0.4 │ form-data: Unsafe random function in form-data               │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2025-7783                    │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 2.5.2             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 4.0.1             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ mysql2 (package.json)          │ CVE-2024-21508 │          │        │ 2.3.3             │ 3.9.4               │ mysql2: Remote Code Execution                                │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21508                   │
│                                ├────────────────┤          │        │                   ├─────────────────────┼──────────────────────────────────────────────────────────────┤
│                                │ CVE-2024-21511 │          │        │                   │ 3.9.7               │ mysql2: Arbitrary Code Injection due to improper             │
│                                │                │          │        │                   │                     │ sanitization of the timezone parameter...                    │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21511                   │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ tar (package.json)             │ CVE-2026-59873 │          │        │ 6.2.1             │ 7.5.19              │ tar: node-tar: Denial of Service via crafted gzip bomb       │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-59873                   │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 7.4.3             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
└────────────────────────────────┴────────────────┴──────────┴────────┴───────────────────┴─────────────────────┴──────────────────────────────────────────────────────────────┘
```

So, we have 230 critical CVEs in the image + 10 critical in Node.JS

 

## CVEs in new docker image

Current sources downloaded from 

https://www.tmforum.org/open-digital-architecture/open-apis/service-inventory-management-api-TMF638/v5.0

The sources are no longer part of the download package. Instead of a docker compose file references Docker Images.
The change was described here:

https://projects.tmforum.org/wiki/display/API/TM+Forum+Open+API+Conformance+Testing+and+Validation+Instructions+Page?_gl=1*54nltg*_gcl_au*ODE2Mjk5OTQzLjE3NzkyNzU5MzQuLS4tLjE3ODUzMTM3OTUuNzMzOTA4MDgzLjE3ODUzMTM3OTYuMTc4NTMxMzc5NQ..

The Docker image used is tmforumorg/tmf638-v5.0.0-ri:1.0.1

```
trivy image --scanners vuln --severity CRITICAL tmforumorg/tmf638-v5.0.0-ri:1.0.1
```

```
...
tmforumorg/tmf638-v5.0.0-ri:1.0.1 (alpine 3.15.4)

Total: 1 (CRITICAL: 1)

┌─────────┬────────────────┬──────────┬────────┬───────────────────┬───────────────┬─────────────────────────────────────────────────────────────┐
│ Library │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version │                            Title                            │
├─────────┼────────────────┼──────────┼────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────────┤
│ zlib    │ CVE-2022-37434 │ CRITICAL │ fixed  │ 1.2.12-r0         │ 1.2.12-r2     │ zlib: heap-based buffer over-read and overflow in inflate() │
│         │                │          │        │                   │               │ in inflate.c via a...                                       │
│         │                │          │        │                   │               │ https://avd.aquasec.com/nvd/cve-2022-37434                  │
└─────────┴────────────────┴──────────┴────────┴───────────────────┴───────────────┴─────────────────────────────────────────────────────────────┘

Node.js (node-pkg)

Total: 4 (CRITICAL: 4)

┌──────────────────────────┬────────────────┬──────────┬────────┬───────────────────┬─────────────────────┬────────────────────────────────────────────────────────┐
│         Library          │ Vulnerability  │ Severity │ Status │ Installed Version │    Fixed Version    │                         Title                          │
├──────────────────────────┼────────────────┼──────────┼────────┼───────────────────┼─────────────────────┼────────────────────────────────────────────────────────┤
│ form-data (package.json) │ CVE-2025-7783  │ CRITICAL │ fixed  │ 2.3.3             │ 2.5.4, 3.0.4, 4.0.4 │ form-data: Unsafe random function in form-data         │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2025-7783              │
├──────────────────────────┼────────────────┤          │        │                   ├─────────────────────┼────────────────────────────────────────────────────────┤
│ mysql2 (package.json)    │ CVE-2024-21508 │          │        │                   │ 3.9.4               │ mysql2: Remote Code Execution                          │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21508             │
│                          ├────────────────┤          │        │                   ├─────────────────────┼────────────────────────────────────────────────────────┤
│                          │ CVE-2024-21511 │          │        │                   │ 3.9.7               │ mysql2: Arbitrary Code Injection due to improper       │
│                          │                │          │        │                   │                     │ sanitization of the timezone parameter...              │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21511             │
├──────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼────────────────────────────────────────────────────────┤
│ tar (package.json)       │ CVE-2026-59873 │          │        │ 6.1.11            │ 7.5.19              │ tar: node-tar: Denial of Service via crafted gzip bomb │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-59873             │
└──────────────────────────┴────────────────┴──────────┴────────┴───────────────────┴─────────────────────┴────────────────────────────────────────────────────────┘
```


So, the new image only contains 1 CVE in the image and 4 in Node.JS, which is much better then the currently used version.


## Changes to reference implementation

https://github.com/tmforum-oda/oda-canvas/commit/2b490d94134475a60aceb1438d710e0923e6e59e

```diff
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/README.md b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/README.md
index d3d47c09f..83f58d0d2 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/README.md
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/README.md
@@ -69,3 +69,9 @@ Currently a concept awaiting feedback. The idea is to have the objects defined i
 
 
 
+# Buildautomation and Versioning
+
+The build and release process for docker images is described here:
+[docs/developer/work-with-dockerimages.md](../../../docs/developer/work-with-dockerimages.md)
+
+
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/api/openapi.yaml b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/api/openapi.yaml
index 0c29f6f36..08c09e72a 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/api/openapi.yaml
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/api/openapi.yaml
@@ -39,7 +39,7 @@ info:
   title: Service Inventory Management
   version: 5.0.0
 servers:
-  - url: 'http://localhost:8638/tmf-api/serviceInventoryManagement/v5'
+  - url: 'http://info.canvas.svc.cluster.local'
 tags:
   - description: Operations for Service Resource
     name: service
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.js b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.js
index 923405271..3ce82322b 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.js
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.js
@@ -4,10 +4,16 @@ const fs   = require('fs')
 const contents = fs.readFileSync(__dirname + "/config.json")
 const jsonConfig = JSON.parse(contents)
 
+const SERVER_URL = process.env.SERVER_URL
+if (SERVER_URL) {
+  jsonConfig["servers"][0]["url"] = SERVER_URL
+}
+
 const config = {
   ROOT_DIR: __dirname,
   URL_PORT: 8638,
-  URL_PATH: 'http://localhost:8638/tmf-api/serviceInventoryManagement/v5',
+  URL_PATH: 'http://info.canvas.svc.cluster.local',
+  
   BASE_VERSION: 'v5',
   CONTROLLER_DIRECTORY: path.join(__dirname, 'controllers'),
   OPENAPI_YAML: '',
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.json b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.json
index 8f515c04e..b5aacbdf6 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.json
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/config.json
@@ -4,9 +4,9 @@
   "db_prot": "mongodb",
   "db_user": "mongodb",
   "db_password": "mongodb",
-  "db_host": "localhost",
+  "db_host": "canvas-svcinv-mongodb",
   "db_port": 27017,
-  "db_name": "tmf",
+  "db_name": "svcinv",
 
   "alarm_host": "http://localhost:10011",
   "alarm_url_hal": "/api/",
@@ -30,7 +30,7 @@
   "injectListenerPostings": true,
 
   "notExternal": true,
-  "servers" : [ { "url": "http://localhost:8638/tmf-api/serviceInventoryManagement/v5" } ], 
+  "servers" : [ { "url": "http://info.canvas.svc.cluster.local" } ], 
   "SCHEMA_URL" : "http://localhost:8080/openapi",
 
 
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/dockerfile b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/dockerfile
index 0f8fc1b4f..2d90a17ec 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/dockerfile
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/dockerfile
@@ -7,5 +7,12 @@ COPY package.json .
 RUN npm install
 COPY . .
 
+ARG SOURCE_DATE_EPOCH
+ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
+ARG GIT_COMMIT_SHA
+ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA
+ARG CICD_BUILD_TIME
+ENV CICD_BUILD_TIME=$CICD_BUILD_TIME
+
 EXPOSE 8080
 CMD [ "node", "index.js" ]
\ No newline at end of file
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/expressServer.js b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/expressServer.js
index 7a324c06d..cd1c441e7 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/expressServer.js
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/expressServer.js
@@ -24,6 +24,7 @@ class ExpressServer {
     this.port = port;
     this.app = express();
     this.openApiPath = openApiYaml;
+    
     try {
     
       this.schema = jsYaml.safeLoad(fs.readFileSync(openApiYaml))
@@ -105,6 +106,19 @@ class ExpressServer {
     
     try {
       
+      const SOURCE_DATE_EPOCH = process.env.SOURCE_DATE_EPOCH
+      const GIT_COMMIT_SHA = process.env.GIT_COMMIT_SHA
+      const CICD_BUILD_TIME = process.env.CICD_BUILD_TIME
+      if (SOURCE_DATE_EPOCH) {
+          logger.info(`SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}`)
+      }
+      if (GIT_COMMIT_SHA) {
+          logger.info(`GIT_COMMIT_SHA=${GIT_COMMIT_SHA}`)
+      }
+      if (CICD_BUILD_TIME) {
+          logger.info(`CICD_BUILD_TIME=${CICD_BUILD_TIME}`)
+      }
+      
       this.app.use( OpenApiValidator.middleware({
             apiSpec: this.openApiPath,
             operationHandlers: path.join(__dirname),
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package-lock.json b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package-lock.json
index c2b20def6..3effa465b 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package-lock.json
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package-lock.json
@@ -8146,4 +8146,4 @@
       }
     }
   }
-}
+}
\ No newline at end of file
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package.json b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package.json
index ccdd61525..819a52b15 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package.json
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/package.json
@@ -1,7 +1,7 @@
 {
-  "name": "openapi-petstore",
+  "name": "TMF638-Service-Inventory",
   "version": "1.0.0",
-  "description": "This is a sample server Petstore server. For this sample, you can use the api key `special-key` to test the authorization filters.",
+  "description": "",
   "main": "index.js",
   "scripts": {
     "prestart": "npm install",
diff --git a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/plugins/plugins.js b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/plugins/plugins.js
index 45c02bd31..619d3d6d1 100644
--- a/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/plugins/plugins.js
+++ b/source/tmf-services/TMF638_CVEs/tools/CHANGES_TMF638_Service_Inventory-RI/plugins/plugins.js
@@ -2,6 +2,7 @@
 
 const plugins = {}
 plugins.db = require('./mongo')
+// deactivating kafka here did not work
 plugins.queue = require('./kafka')
 
 const { waitForPlugins } = require('./wait')
 ```

