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
    
    
    
if __name__ == "__main__":
    
    main(
        "C:\\Users\\A307131\\git\\oda-canvas\\source\\services\\ComponentRegistry\\component-registry-service-tmf639\\INFO\\test-request_PART.json", 
        "C:\\Users\\A307131\\git\\oda-canvas\\source\\services\\ComponentRegistry\\component-registry-service-tmf639\\INFO\\test-schema-v500lt.yaml"
    )
