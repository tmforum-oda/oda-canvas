# ComponentRegistry with TMF-369 


## create component using old interface

```
curl -X 'POST' \
  'http://localhost:8080/components' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "component_registry_ref": "self",
  "component_name": "comp01",
  "component_version": "1.0.0",
  "description": "The first Component",
  "exposed_apis": [
    {
      "name": "exp-api-01",
      "oas_specification": "http://expapis.01",
      "url": "http://expapi01.url"
    }
  ],
  "labels": {
    "id": "TMF01",
    "namespace": "components"
  }
}'
```

### query as resource


```
curl -sX GET http://localhost:8080/resource/self%3Acomp01 -H "accept: application/json" | jq

{
  "id": "self:comp01",
  "href": "/resource/self:comp01",
  "category": "Component",
  "description": "The first Component",
  "endOperatingDate": null,
  "name": "comp01",
  "resourceVersion": "1.0.0",
  "startOperatingDate": null,
  "activationFeature": null,
  "administrativeState": null,
  "attachment": null,
  "note": null,
  "operationalState": null,
  "place": null,
  "relatedParty": null,
  "resourceCharacteristic": [
    {
      "name": "component_registry_ref",
      "value": "self"
    },
    {
      "name": "component_version",
      "value": "1.0.0"
    },
    {
      "name": "api_exp-api-01_url",
      "value": "http://expapi01.url"
    },
    {
      "name": "api_exp-api-01_specification",
      "value": "http://expapis.01"
    }
  ],
  "resourceRelationship": null,
  "resourceSpecification": null,
  "resourceStatus": "available",
  "usageState": null,
  "@baseType": null,
  "@schemaLocation": null,
  "@type": null
}
```

## 



# Links

* https://engage.tmforum.org/communities/community-home/digestviewer/viewthread?MessageKey=6c46d80a-6dc3-4205-a8bd-72b829e8d02b&CommunityKey=d543b8ba-9d3a-4121-85ce-5b68e6c31ce5&tab=digestviewer

