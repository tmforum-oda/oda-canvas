"""Schema validators for TMF639 Resource Inventory Management v5.0.0."""

from typing import Dict, Any
from fastapi import HTTPException
from app.openapi_validator import OpenAPIValidator


class TMF639ResourceValidator:
    """Validator for TMF639 Resource schema compliance using OpenAPI specification."""
    
    _validator = None
    
    @classmethod
    def _get_validator(cls) -> OpenAPIValidator:
        """Get or create the OpenAPI validator instance."""
        if cls._validator is None:
            cls._validator = OpenAPIValidator()
        return cls._validator
    
    @staticmethod
    def validate_resource_create(resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate resource creation data against TMF639 v5.0.0 Resource_FVO schema.
        
        This method uses the official TMF639 OpenAPI specification to validate
        the resource data, ensuring full compliance with the standard.
        
        Args:
            resource_data: The resource data to validate
            
        Returns:
            The validated resource data
            
        Raises:
            HTTPException: If validation fails
        """
        validator = TMF639ResourceValidator._get_validator()
        return validator.validate_resource_create(resource_data)
    
    @staticmethod
    def get_schema_info(schema_name: str = 'Resource_FVO') -> Dict[str, Any]:
        """
        Get schema information from the OpenAPI specification.
        
        Args:
            schema_name: Name of the schema to retrieve info for
            
        Returns:
            Dictionary with schema information
        """
        validator = TMF639ResourceValidator._get_validator()
        return validator.get_schema_info(schema_name)