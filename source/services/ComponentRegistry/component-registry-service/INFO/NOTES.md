# create componentregistry

```json
{
  "name": "self",
  "url": "http://localhost:8000",
  "type": "self",
  "labels": {
    "regname": "reg-A"
  }
}
```

curl

```
curl -X 'POST' \
  'http://localhost:8000/registries' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "self",
  "url": "http://localhost:8000",
  "type": "self",
  "labels": {
    "regname": "reg-A"
  }
}'
```

# create component

```json
{
  "component_registry_ref": "self",
  "component_name": "comp_name",
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
  'http://localhost:8000/components' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "component_registry_ref": "self",
  "component_name": "comp_name",
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
}'
```