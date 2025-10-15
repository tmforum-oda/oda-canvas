# TMF639 Converter - Usage Guide

## Overview

The `tmf639_converter.py` module provides bidirectional conversion between:
- **ODA Component format** (simplified component representation)
- **TMF639 Resource Catalog format** (TM Forum standard)

## Quick Start

### 1. Basic Conversion - Component to TMF639

```python
from tmf639_converter import TMF639Converter
import json

# Your component data
component = {
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

# Convert to TMF639
converter = TMF639Converter()
tmf639_resources = converter.component_to_tmf639(component)

print(json.dumps(tmf639_resources, indent=2))
```

### 2. Basic Conversion - TMF639 to Component

```python
from tmf639_converter import TMF639Converter
import json

# Your TMF639 resources (list with component + API resources)
tmf639_resources = [...]  # Load from file or API

# Convert to component format
converter = TMF639Converter()
component = converter.tmf639_to_component(tmf639_resources)

print(json.dumps(component, indent=2))
```

### 3. Batch Conversion - Multiple Components

```python
from tmf639_converter import convert_component_list_to_tmf639, convert_tmf639_to_component_list
import json

# Convert multiple components to TMF639
components = [component1, component2, component3]
all_tmf639_resources = convert_component_list_to_tmf639(components)

# Convert TMF639 resources back to components
tmf639_resources = [...]  # All resources from catalog
components = convert_tmf639_to_component_list(tmf639_resources)
```

### 4. File-Based Conversion

```python
import json
from tmf639_converter import TMF639Converter

# Load component from file
with open('component.json', 'r') as f:
    component = json.load(f)[0]  # Assuming it's a list

# Convert to TMF639
converter = TMF639Converter()
tmf639_resources = converter.component_to_tmf639(component)

# Save to file
with open('tmf639-output.json', 'w') as f:
    json.dump(tmf639_resources, f, indent=2)
```

## Data Mapping

### Component → TMF639 Resource

**Component Fields:**
- `component_name` → Resource `id` (prefixed with "r-cat-")
- `component_version` → Characteristic named "version"
- `description` → Resource `description`
- `labels.*` → Characteristics named "label_*"
- `exposed_apis[].name` → API Resource with characteristics
- `exposed_apis[].oas_specification` → Characteristic "specification"
- `exposed_apis[].url` → Characteristic "url"
- `exposed_apis[].labels.status` → Resource `resourceStatus`
- `exposed_apis[].labels.*` → Characteristics named "label_*"

**Generated Structure:**
1. One LogicalResource with category="ODAComponent"
2. Multiple LogicalResources with category="API" (one per exposed API)
3. Bidirectional relationships via `relatedResource`

### TMF639 Resource → Component

The converter automatically:
- Groups resources by component ID
- Extracts characteristics back to labels
- Rebuilds the exposed_apis list from API resources
- Preserves all metadata

## Testing

Run the included test script:

```bash
python test_converter.py
```

This will:
- Convert the example component to TMF639 format
- Convert the TMF639 example back to component format
- Perform round-trip validation
- Generate test output files for inspection

## API Reference

### Class: TMF639Converter

#### Methods:

**`component_to_tmf639(component: Dict) -> List[Dict]`**
- Converts a single component to TMF639 resources
- Returns: List containing component resource + API resources

**`tmf639_to_component(resources: List[Dict]) -> Dict`**
- Converts TMF639 resources to component format
- Requires: List containing related component and API resources
- Returns: Single component dictionary

### Helper Functions:

**`convert_component_list_to_tmf639(components: List[Dict]) -> List[Dict]`**
- Converts multiple components at once
- Returns flattened list of all resources

**`convert_tmf639_to_component_list(resources: List[Dict]) -> List[Dict]`**
- Converts all TMF639 resources back to components
- Automatically groups by component
- Returns list of components

## Notes

- The converter maintains data integrity through round-trip conversions
- All labels are preserved with "label_" prefix in TMF639 characteristics
- API status is stored in `resourceStatus` field (TMF639) or `labels.status` (component)
- Resource IDs follow the pattern: `r-cat-{component_name}` and `r-cat-{component_name}-{api_name}`

## Example Output

See the test output files in `INFO/JSON_STRUCTURES/`:
- `test-output-tmf639.json` - Component converted to TMF639
- `test-output-component.json` - TMF639 converted back to component
