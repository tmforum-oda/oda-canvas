# dependentapi-simple-operator

![Version: 0.2.4](https://img.shields.io/badge/Version-0.2.4-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.2.3"](https://img.shields.io/badge/AppVersion-0.2.3"-informational?style=flat-square)

The DependentAPI Simple Operator

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| image | string | `"tmforumodacanvas/dependentapi-simple-operator"` |  |
| imagePullPolicy | string | `"IfNotPresent"` |  |
| loglevel | string | `"20"` |  |
| prereleaseSuffix | string | `nil` |  |
| serviceInventoryAPI.enabled | bool | `true` |  |
| serviceInventoryAPI.image | string | `"tmforumodacanvas/tmf638-service-inventory-api"` |  |
| serviceInventoryAPI.imagePullPolicy | string | `"IfNotPresent"` |  |
| serviceInventoryAPI.mongodb.database | string | `"svcinv"` |  |
| serviceInventoryAPI.mongodb.port | int | `27017` |  |
| serviceInventoryAPI.prereleaseSuffix | string | `nil` |  |
| serviceInventoryAPI.serverUrl | string | `"http://info.canvas.svc.cluster.local"` |  |
| serviceInventoryAPI.version | string | `"0.1.1"` |  |
| version | string | `"0.2.4"` |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
