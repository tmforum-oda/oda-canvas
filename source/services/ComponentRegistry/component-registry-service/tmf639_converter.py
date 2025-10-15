"""
TMF639 Resource Catalog Converter

This module provides bidirectional conversion between ODA Component representation
and TMF639 Resource Catalog format.

Author: ODA Canvas Team
"""

from typing import Dict, List, Any, Optional


class TMF639Converter:
    """
    Converter for transforming between ODA Component format and TMF639 Resource format.
    
    Supports bidirectional conversion:
    - component_to_tmf639: Converts ODA Component dict to TMF639 Resource list
    - tmf639_to_component: Converts TMF639 Resource list to ODA Component dict
    """
    
    @staticmethod
    def component_to_tmf639(component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert ODA Component format to TMF639 Resource format.
        
        Args:
            component: Dictionary containing component data in ODA format
            
        Returns:
            List of TMF639 Resource dictionaries (component + APIs)
        """
        resources = []
        
        # Extract component metadata
        component_name = component.get("component_name", "")
        component_version = component.get("component_version", "")
        description = component.get("description", "")
        labels = component.get("labels", {})
        exposed_apis = component.get("exposed_apis", [])
        
        # Build related resources list (API references)
        related_resources = []
        for api in exposed_apis:
            api_name = api.get("name", "")
            api_resource_id = f"{component_name}-{api_name}"
            related_resources.append({
                "@type": "ResourceRef",
                "@referredType": "LogicalResource",
                "id": api_resource_id,
                "href": f"/resource/{api_resource_id}",
                "name": api_resource_id,
                "category": "API",
                "relationshipType": "exposes"
            })
        
        # Build component resource characteristics
        component_characteristics = [
            {
                "@type": "Characteristic",
                "name": "name",
                "value": component_name.replace("r-cat-", "") if component_name.startswith("r-cat-") else component_name
            },
            {
                "@type": "Characteristic",
                "name": "version",
                "value": component_version
            }
        ]
        
        # Add labels as characteristics
        for label_key, label_value in labels.items():
            component_characteristics.append({
                "@type": "Characteristic",
                "name": f"label_{label_key}",
                "value": label_value
            })
        
        # Create main component resource
        component_resource = {
            "@type": "LogicalResource",
            "@baseType": "Resource",
            "id": component_name,
            "href": f"/resource/{component_name}",
            "name": component_name,
            "description": description,
            "category": "ODAComponent",
            "resourceSpecification": {
                "@type": "ResourceSpecificationRef",
                "id": "ODAComponent",
                "name": "ODA Component"
            },
            "resourceCharacteristic": component_characteristics,
            "relatedResource": related_resources
        }
        
        resources.append(component_resource)
        
        # Create API resources
        for api in exposed_apis:
            api_name = api.get("name", "")
            oas_specification = api.get("oas_specification", "")
            url = api.get("url", "")
            api_labels = api.get("labels", {})
            
            api_resource_id = f"{component_name}-{api_name}"
            
            # Build API resource characteristics
            api_characteristics = [
                {
                    "@type": "Characteristic",
                    "name": "apiName",
                    "value": api_name
                },
                {
                    "@type": "Characteristic",
                    "name": "specification",
                    "value": oas_specification
                },
                {
                    "@type": "Characteristic",
                    "name": "url",
                    "value": url
                }
            ]
            
            # Add API labels as characteristics
            api_status = None
            for label_key, label_value in api_labels.items():
                if label_key == "status":
                    api_status = label_value
                else:
                    api_characteristics.append({
                        "@type": "Characteristic",
                        "name": f"label_{label_key}",
                        "value": label_value
                    })
            
            # Create API resource
            api_resource = {
                "@type": "LogicalResource",
                "@baseType": "Resource",
                "id": api_resource_id,
                "href": f"/resource/{api_resource_id}",
                "name": api_resource_id,
                "category": "API",
                "resourceSpecification": {
                    "@type": "ResourceSpecificationRef",
                    "id": "API",
                    "name": "API"
                },
                "resourceCharacteristic": api_characteristics,
                "relatedResource": [
                    {
                        "@type": "ResourceRef",
                        "@referredType": "LogicalResource",
                        "id": component_name,
                        "href": f"/resource/{component_name}",
                        "name": component_name,
                        "category": "ODAComponent",
                        "relationshipType": "exposedBy"
                    }
                ]
            }
            
            # Add status if present
            if api_status:
                api_resource["resourceStatus"] = api_status
            
            resources.append(api_resource)
        
        return resources
    
    @staticmethod
    def tmf639_to_component(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert TMF639 Resource format to ODA Component format.
        
        Args:
            resources: List of TMF639 Resource dictionaries
            
        Returns:
            Dictionary containing component data in ODA format
        """
        # Find the main component resource
        component_resource = None
        api_resources = []
        
        for resource in resources:
            if resource.get("category") == "ODAComponent":
                component_resource = resource
            elif resource.get("category") == "API":
                api_resources.append(resource)
        
        if not component_resource:
            raise ValueError("No ODAComponent resource found in input")
        
        # Extract component name from resource ID
        component_name = component_resource.get("id", "")
        
        # Extract component metadata from characteristics
        component_version = None
        labels = {}
        
        for characteristic in component_resource.get("resourceCharacteristic", []):
            char_name = characteristic.get("name", "")
            char_value = characteristic.get("value", "")
            
            if char_name == "version":
                component_version = char_value
            elif char_name.startswith("label_"):
                label_key = char_name[6:]  # Remove "label_" prefix
                labels[label_key] = char_value
        
        # Build exposed APIs list
        exposed_apis = []
        
        for api_resource in api_resources:
            api_name = None
            oas_specification = None
            url = None
            api_labels = {}
            
            # Extract API characteristics
            for characteristic in api_resource.get("resourceCharacteristic", []):
                char_name = characteristic.get("name", "")
                char_value = characteristic.get("value", "")
                
                if char_name == "apiName":
                    api_name = char_value
                elif char_name == "specification":
                    oas_specification = char_value
                elif char_name == "url":
                    url = char_value
                elif char_name.startswith("label_"):
                    label_key = char_name[6:]  # Remove "label_" prefix
                    api_labels[label_key] = char_value
            
            # Add status from resourceStatus field
            api_status = api_resource.get("resourceStatus")
            if api_status:
                api_labels["status"] = api_status
            
            exposed_apis.append({
                "name": api_name,
                "oas_specification": oas_specification,
                "url": url,
                "labels": api_labels
            })
        
        # Build component dictionary
        component = {
            "component_name": component_name,
            "component_version": component_version,
            "description": component_resource.get("description", ""),
            "labels": labels,
            "exposed_apis": exposed_apis
        }
        
        return component


def convert_component_list_to_tmf639(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of ODA Components to TMF639 Resource format.
    
    Args:
        components: List of component dictionaries in ODA format
        
    Returns:
        List of all TMF639 Resource dictionaries (flattened)
    """
    converter = TMF639Converter()
    all_resources = []
    
    for component in components:
        resources = converter.component_to_tmf639(component)
        all_resources.extend(resources)
    
    return all_resources


def convert_tmf639_to_component_list(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert TMF639 Resources to a list of ODA Components.
    Groups resources by component.
    
    Args:
        resources: List of TMF639 Resource dictionaries
        
    Returns:
        List of component dictionaries in ODA format
    """
    converter = TMF639Converter()
    
    # Group resources by component
    components_map = {}
    
    for resource in resources:
        if resource.get("category") == "ODAComponent":
            component_id = resource.get("id")
            if component_id:
                components_map[component_id] = [resource]
        elif resource.get("category") == "API":
            # Find the parent component from relatedResource
            for related in resource.get("relatedResource", []):
                if related.get("category") == "ODAComponent":
                    component_id = related.get("id")
                    if component_id:
                        if component_id not in components_map:
                            components_map[component_id] = []
                        components_map[component_id].append(resource)
                    break
    
    # Convert each component group
    components = []
    for component_resources in components_map.values():
        if component_resources:
            component = converter.tmf639_to_component(component_resources)
            components.append(component)
    
    return components


if __name__ == "__main__":
    import json
    import sys
    
    # Example usage
    print("TMF639 Converter - Bidirectional conversion utility")
    print("=" * 60)
    
    # Example: Convert component to TMF639
    example_component = {
        "component_name": "productcatalogmanagement",
        "component_version": "0.0.1",
        "description": "Simple Product Catalog ODA-Component",
        "labels": {
            "id": "TMFC001",
            "functionalBlock": "CoreCommerce"
        },
        "exposed_apis": [
            {
                "name": "productcatalogmanagement",
                "oas_specification": "https://example.com/spec.json",
                "url": "https://example.com/api/v4",
                "labels": {
                    "apiType": "openapi",
                    "status": "ready"
                }
            }
        ]
    }
    
    converter = TMF639Converter()
    
    print("\n1. Converting Component to TMF639:")
    tmf639_resources = converter.component_to_tmf639(example_component)
    print(json.dumps(tmf639_resources, indent=2))
    
    print("\n2. Converting TMF639 back to Component:")
    converted_back = converter.tmf639_to_component(tmf639_resources)
    print(json.dumps(converted_back, indent=2))