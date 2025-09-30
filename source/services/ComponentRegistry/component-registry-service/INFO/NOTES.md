# Deploy ComponentRegistry Helm Charts

```
helm upgrade --install compreg -n compreg --create-namespace helm/component-registry
```




# create componentregistry

```json
{
  "name": "self",
  "url": "http://localhost:8080",
  "type": "self",
  "labels": {
    "regname": "reg-A",
    "cluster": "two"
  }
}
```

curl

```
curl -X 'POST' \
  'http://localhost:8080/registries' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "self",
  "url": "http://localhost:8080",
  "type": "self",
  "labels": {
    "regname": "reg-A",
    "cluster": "two"
  }
}'
```

# create component

```json
{
  "component_registry_ref": "self",
  "component_name": "comp_name",
  "component_version": "0.1.0",
  "description": "dummy component entry",
  "exposed_apis": [
    {
      "name": "expapi1",
      "oas_specification": "https://open.api/spec",
      "url": "http://expapi1.cluster-2.de",
      "labels": {
        "expapikey1": "expapivalue1",
        "expapikey2": "expapivalue2"
      }
    }
  ],
  "labels": {
    "team": "oda-fans",
    "unit": "b2b"
  }
}

```

curl

```
curl -X 'POST' \
  'http://localhost:8080/components' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "component_registry_ref": "self",
  "component_name": "comp_name",
  "component_version": "0.1.0",
  "description": "dummy component entry",
  "exposed_apis": [
    {
      "name": "expapi1",
      "oas_specification": "https://open.api/spec",
      "url": "http://expapi1.cluster-2.de",
      "labels": {
        "expapikey1": "expapivalue1",
        "expapikey2": "expapivalue2"
      }
    }
  ],
  "labels": {
    "team": "oda-fans",
    "unit": "b2b"
  }
}
'
```
