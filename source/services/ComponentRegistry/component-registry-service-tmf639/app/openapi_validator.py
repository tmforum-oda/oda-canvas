"""Generic OpenAPI schema validator for TMF639 v5.0.0 using openapi-schema-validator."""

import yaml
from typing import Dict, Any
from pathlib import Path
from fastapi import HTTPException, status
from jsonschema import Draft7Validator, ValidationError
#from jsonschema.validators import RefResolver


class OpenAPIValidator:
    """Generic validator that uses the TMF639 OpenAPI specification with jsonschema."""
    
    def __init__(self, openapi_spec_path: str = None):
        """
        Initialize the validator with the OpenAPI specification.
        
        Args:
            openapi_spec_path: Path to the OpenAPI YAML file. If None, uses default path.
        """
        if openapi_spec_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent.parent
            # openapi_spec_path = base_dir / "openapi" / "TMF639-Resource_Inventory_Management-v5.0.0.oas.yaml"
            openapi_spec_path = base_dir / "openapi" / "OFF" / "TMF639-Resource_Inventory_Management-v5.0.0.oas_PATCHED.yaml"
        
        self.spec_path = Path(openapi_spec_path)
        self.spec = self._load_spec()
        self.schemas = self.spec.get('components', {}).get('schemas', {})
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load and parse the OpenAPI specification."""
        try:
            with open(self.spec_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise RuntimeError(f"OpenAPI specification not found at {self.spec_path}")
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse OpenAPI specification: {e}")
    
    def _resolve_schema_refs(self, schema: Dict[str, Any], visited: set = None) -> Dict[str, Any]:
        """
        Recursively resolve $ref references in a schema.
        
        Args:
            schema: The schema dictionary to resolve
            visited: Set of already visited references to prevent infinite loops
            
        Returns:
            Resolved schema with all $ref replaced
        """
        if visited is None:
            visited = set()
        
        if isinstance(schema, dict):
            # Handle $ref
            if '$ref' in schema:
                ref = schema['$ref']
                if ref in visited:
                    return {}  # Prevent infinite recursion
                
                visited.add(ref)
                
                # Extract schema name from $ref (e.g., '#/components/schemas/Resource_FVO')
                if ref.startswith('#/components/schemas/'):
                    schema_name = ref.split('/')[-1]
                    if schema_name in self.schemas:
                        return self._resolve_schema_refs(self.schemas[schema_name], visited.copy())
                return schema
            
            # Handle allOf - merge all schemas
            if 'allOf' in schema:
                merged = {}
                for sub_schema in schema['allOf']:
                    resolved = self._resolve_schema_refs(sub_schema, visited.copy())
                    merged = self._merge_schemas(merged, resolved)
                
                # Merge other properties from the current schema
                for key, value in schema.items():
                    if key != 'allOf':
                        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                            merged[key] = {**merged[key], **value}
                        elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                            merged[key] = merged[key] + value
                        else:
                            merged[key] = value
                
                return merged
            
            # Recursively resolve nested schemas
            resolved = {}
            for key, value in schema.items():
                resolved[key] = self._resolve_schema_refs(value, visited.copy())
            return resolved
        
        elif isinstance(schema, list):
            return [self._resolve_schema_refs(item, visited.copy()) for item in schema]
        
        else:
            return schema
    
    def _merge_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two schemas together."""
        merged = schema1.copy()
        
        for key, value in schema2.items():
            if key == 'properties':
                merged.setdefault('properties', {}).update(value)
            elif key == 'required':
                merged.setdefault('required', []).extend(value)
            elif key not in merged:
                merged[key] = value
        
        # Deduplicate required fields
        if 'required' in merged:
            merged['required'] = list(set(merged['required']))
        
        return merged
    
    def validate_resource_create(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate resource creation data against Resource_FVO schema from OpenAPI spec.
        
        Args:
            resource_data: The resource data to validate
            
        Returns:
            The validated resource data
            
        Raises:
            HTTPException: If validation fails
        """
        errors = []
        
        # Get the Resource_FVO schema from components/schemas
        if 'Resource_FVO' not in self.schemas:
            raise RuntimeError("Resource_FVO schema not found in OpenAPI specification")
        
        # Resolve all $ref references in the schema
        schema = self._resolve_schema_refs(self.schemas['Resource_FVO'])
        
        # Create a complete schema document for validation
        schema_doc = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **schema
        }
        
        try:
            # Create validator instance
            validator = Draft7Validator(schema_doc)
            
            # Validate and collect all errors
            validation_errors = list(validator.iter_errors(resource_data))
            
            for error in validation_errors:
                # Build a human-readable error message
                if error.absolute_path:
                    path = ".".join(str(p) for p in error.absolute_path)
                else:
                    path = "root"
                
                # Format the error message
                message = error.message
                if error.validator == 'required':
                    missing = error.message.split("'")[1]
                    message = f"Missing required field: {missing}"
                elif error.validator == 'enum':
                    message = f"Invalid value. {error.message}"
                
                errors.append(f"{path}: {message}" if path != "root" else message)
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        # If there are validation errors, raise HTTPException
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Schema validation failed",
                    "message": "Resource creation data does not comply with TMF639 v5.0.0 specification",
                    "violations": errors
                }
            )
        
        return resource_data
    
    def get_schema_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get information about a schema from the OpenAPI specification.
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            Schema information including description, required fields, and properties
        """
        if schema_name not in self.schemas:
            return {
                "name": schema_name,
                "error": f"Schema '{schema_name}' not found in OpenAPI specification"
            }
        
        # Resolve the schema
        schema = self._resolve_schema_refs(self.schemas[schema_name])
        
        return {
            "name": schema_name,
            "description": schema.get('description', ''),
            "required": schema.get('required', []),
            "properties": list(schema.get('properties', {}).keys()),
            "type": schema.get('type', 'object')
        }