import os
import yaml
import json

from openapi_schema_validator import validate
from app.validators import TMF639ResourceValidator


def main(json_file_path: str, schame_file_path: str = None):

    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    print(json.dumps(data, indent=2))

    # Validate resource against TMF639 v5.0.0 specification
    validated_resource = TMF639ResourceValidator.validate_resource_create(data)
    

    #===========================================================================
    # with open(schame_file_path, 'r') as schema_file:
    #     schema_content = yaml.safe_load(schema_file)
    #===========================================================================
    

    
    # from https://openapi-schema-validator.readthedocs.io/en/latest/references.html
    #===========================================================================
    # schema = {
    #     "type" : "object",
    #     "required": [
    #        "key",
    #        "data"
    #     ],
    #     "properties": {
    #         "key": {
    #             "type": "string"
    #         },
    #         "data": {
    #             "$ref": "#/components/schemas/Resource_RES"
    #         }
    #     },
    #     "additionalProperties": False,
    # }
    #===========================================================================
    
#===============================================================================
#     schema = {
#         "$ref": "#/components/schemas/Resource_RES"
#     }
#     
#     with open(json_file_path, 'r') as json_file:
#         data = json.load(json_file)
#     with open(schame_file_path, 'r') as schema_file:
#         schema_content = yaml.safe_load(schema_file)
# 
#     schema = schema | schema_content
#     
#     #===========================================================================
#     # reg.with_resource(
#     #         uri="file://" + os.path.abspath(schame_file_path),
#     #         resource=schema_content
#     #     )
#     #===========================================================================
#     
#     #===========================================================================
#     # schema = Resource(contents=schema_content, specification=DRAFT202012)
#     # registry = Registry().with_resource(uri="http://example.com/my/schema", resource=schema)
#     #===========================================================================
#     
#     
#     #===========================================================================
#     # addressable_schema = schema_content.get("components", {}).get("schemas", {}).get("Addressable", {})
#     # print(f"urn:addressable-schema:\n{json.dumps(addressable_schema, indent=2)}")
#     #===========================================================================
#     
#     #===========================================================================
#     # name_resource = Resource.from_contents(name_schema, default_specification=DRAFT202012)
#     # registry = Registry().with_resource(
#     #     uri="urn:name-schema",
#     #     resource=name_resource
#     # )
#     #===========================================================================
#     #print(registry.contents("urn:addressable-schema"))
#     
#     # print(json.dumps(schema, indent=2))
#     validate(data, schema)
#     # validate(data, schema, registry=registry)
#     print(f"Validation completed successfully.")
#     
#===============================================================================
    
    
if __name__ == "__main__":
    
    main(
        "C:\\Users\\A307131\\git\\oda-canvas\\source\\services\\ComponentRegistry\\component-registry-service-tmf639\\INFO\\test-request_FULL.json", 
        "C:\\Users\\A307131\\git\\oda-canvas\\source\\services\\ComponentRegistry\\component-registry-service-tmf639\\INFO\\test-schema-v500lt.yaml"
    )
