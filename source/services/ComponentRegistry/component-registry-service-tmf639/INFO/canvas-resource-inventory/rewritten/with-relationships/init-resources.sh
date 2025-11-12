#!/bin/sh


echo "register localhost:8082/sync callback for localdev80 source"
curl -X 'POST' \
  'http://localhost:8080/hub' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "localdev80",
  "callback": "http://localhost:8082/sync",
  "query": "source=localdev80"
}'


echo "create ODAComponent: r-cat-productcatalogmanagement"
curl -X 'POST' \
  'http://localhost:8080/resource' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
	"id": "self:r-cat-productcatalogmanagement",
	"resourceVersion": "1761230462292351010",
	"href": "/resource/self:r-cat-productcatalogmanagement",
	"@type": "LogicalResource",
	"@baseType": "Resource",
	"name": "r-cat-productcatalogmanagement",
	"description": "ODA Component: r-cat-productcatalogmanagement",
	"category": "ODAComponent",
	"resourceSpecification": {
		"@type": "ResourceSpecificationRef",
		"id": "ODAComponent",
		"name": "ODA Component"
	},
	"resourceCharacteristic": [
		{
			"@type": "Characteristic",
			"name": "namespace",
			"value": "components"
		},
		{
			"@type": "Characteristic",
			"name": "deploymentStatus",
			"value": "Unknown"
		},
		{
			"@type": "Characteristic",
			"name": "description",
			"value": "Simple Product Catalog ODA-Component from Open-API reference implementation."
		},
		{
			"@type": "Characteristic",
			"name": "functionalBlock",
			"value": "CoreCommerce"
		},
		{
			"@type": "Characteristic",
			"name": "id",
			"value": "TMFC001"
		},
		{
			"@type": "Characteristic",
			"name": "maintainers",
			"value": [
				{
					"email": "lester.thomas@vodafone.com",
					"name": "Lester Thomas"
				}
			]
		},
		{
			"@type": "Characteristic",
			"name": "name",
			"value": "productcatalogmanagement"
		},
		{
			"@type": "Characteristic",
			"name": "owners",
			"value": [
				{
					"email": "lester.thomas@vodafone.com",
					"name": "Lester Thomas"
				}
			]
		},
		{
			"@type": "Characteristic",
			"name": "publicationDate",
			"value": "2024-09-17T00:00:00.000Z"
		},
		{
			"@type": "Characteristic",
			"name": "status",
			"value": "specified"
		},
		{
			"@type": "Characteristic",
			"name": "version",
			"value": "0.0.1"
		}
	],
	"resourceStatus": "standby",
	"operationalState": "disable",
	"administrativeState": "unlocked",
	"usageState": "active",
	"startDate": "2025-10-15T12:17:30Z",
	"place": [
		{
			"id": "components",
			"name": "components",
			"@type": "Namespace"
		}
	]
}
'


echo "create API: productcatalogmanagement"
curl -X 'POST' \
  'http://localhost:8080/resource' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
	"id": "self:r-cat-productcatalogmanagement:productcatalogmanagement",
	"resourceVersion": "1761230462292351011",
	"href": "/resource/self:r-cat-productcatalogmanagement:productcatalogmanagement",
	"@type": "LogicalResource",
	"@baseType": "Resource",
	"name": "productcatalogmanagement",
	"description": "Exposed API: productcatalogmanagement",
	"category": "API",
	"resourceSpecification": {
		"@type": "ResourceSpecificationRef",
		"id": "API",
		"name": "API"
	},
	"resourceCharacteristic": [
		{
			"@type": "Characteristic",
			"name": "namespace",
			"value": "components"
		},
		{
			"@type": "Characteristic",
			"name": "apiName",
			"value": "productcatalogmanagement"
		},
		{
			"@type": "Characteristic",
			"name": "apiType",
			"value": "openapi"
		},
		{
			"@type": "Characteristic",
			"name": "url",
			"value": "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4"
		},
		{
			"@type": "Characteristic",
			"name": "implementation",
			"value": "r-cat-prodcatapi"
		},
		{
			"@type": "Characteristic",
			"name": "specification",
			"value": [
				{
					"url": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json"
				},
				{
					"url": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v5.0.0.swagger.json"
				}
			]
		},
		{
			"@type": "Characteristic",
			"name": "apiDocs",
			"value": "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs"
		}
	],
	"resourceStatus": "available",
	"operationalState": "enable",
	"administrativeState": "unlocked",
	"usageState": "active",
	"startDate": "2025-10-15T12:17:31Z",
	"place": [
		{
			"id": "components",
			"name": "components",
			"@type": "Namespace"
		}
	],
	"resourceRelationship": [
		{
			"@type": "ResourceRelationship",
			"relationshipType": "exposedBy",
			"resource": {
				"@type": "ResourceRef",
				"id": "self:r-cat-productcatalogmanagement",
				"href": "/resource/self:r-cat-productcatalogmanagement"
			}
		}
	]
}
'


echo "create API: partyrole"
curl -X 'POST' \
  'http://localhost:8080/resource' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
	"id": "self:r-cat-productcatalogmanagement:partyrole",
	"resourceVersion": "1761230462292351012",
	"href": "/resource/self:r-cat-productcatalogmanagement:partyrole",
	"@type": "LogicalResource",
	"@baseType": "Resource",
	"name": "partyrole",
	"description": "Exposed API: partyrole",
	"category": "API",
	"resourceSpecification": {
		"@type": "ResourceSpecificationRef",
		"id": "API",
		"name": "API"
	},
	"resourceCharacteristic": [
		{
			"@type": "Characteristic",
			"name": "namespace",
			"value": "components"
		},
		{
			"@type": "Characteristic",
			"name": "apiName",
			"value": "partyrole"
		},
		{
			"@type": "Characteristic",
			"name": "apiType",
			"value": "openapi"
		},
		{
			"@type": "Characteristic",
			"name": "url",
			"value": "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/partyRoleManagement/v4"
		},
		{
			"@type": "Characteristic",
			"name": "implementation",
			"value": "r-cat-partyroleapi"
		},
		{
			"@type": "Characteristic",
			"name": "specification",
			"value": [
				{
					"url": "https://raw.githubusercontent.com/tmforum-apis/TMF669_PartyRole/master/TMF669-PartyRole-v4.0.0.swagger.json"
				}
			]
		},
		{
			"@type": "Characteristic",
			"name": "apiDocs",
			"value": "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/partyRoleManagement/v4/docs"
		}
	],
	"resourceStatus": "available",
	"operationalState": "enable",
	"administrativeState": "unlocked",
	"usageState": "active",
	"startDate": "2025-10-15T12:17:31Z",
	"place": [
		{
			"id": "components",
			"name": "components",
			"@type": "Namespace"
		}
	],
	"resourceRelationship": [
		{
			"@type": "ResourceRelationship",
			"relationshipType": "exposedBy",
			"resource": {
				"@type": "ResourceRef",
				"id": "self:r-cat-productcatalogmanagement",
				"href": "/resource/self:r-cat-productcatalogmanagement"
			}
		}
	]
}
'


echo "create API: metrics"
curl -X 'POST' \
  'http://localhost:8080/resource' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
	"id": "self:r-cat-productcatalogmanagement:metrics",
	"resourceVersion": "1761230462292351013",
	"href": "/resource/self:r-cat-productcatalogmanagement:metrics",
	"@type": "LogicalResource",
	"@baseType": "Resource",
	"name": "metrics",
	"description": "Exposed API: metrics",
	"category": "API",
	"resourceSpecification": {
		"@type": "ResourceSpecificationRef",
		"id": "API",
		"name": "API"
	},
	"resourceCharacteristic": [
		{
			"@type": "Characteristic",
			"name": "namespace",
			"value": "components"
		},
		{
			"@type": "Characteristic",
			"name": "apiName",
			"value": "metrics"
		},
		{
			"@type": "Characteristic",
			"name": "apiType",
			"value": "prometheus"
		},
		{
			"@type": "Characteristic",
			"name": "url",
			"value": "https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/metrics"
		},
		{
			"@type": "Characteristic",
			"name": "implementation",
			"value": "r-cat-productcatalogmanagement-sm"
		},
		{
			"@type": "Characteristic",
			"name": "apiDocs"
		}
	],
	"resourceStatus": "available",
	"operationalState": "enable",
	"administrativeState": "unlocked",
	"usageState": "active",
	"startDate": "2025-10-15T12:17:31Z",
	"place": [
		{
			"id": "components",
			"name": "components",
			"@type": "Namespace"
		}
	],
	"resourceRelationship": [
		{
			"@type": "ResourceRelationship",
			"relationshipType": "exposedBy",
			"resource": {
				"@type": "ResourceRef",
				"id": "self:r-cat-productcatalogmanagement",
				"href": "/resource/self:r-cat-productcatalogmanagement"
			}
		}
	]
}
'


