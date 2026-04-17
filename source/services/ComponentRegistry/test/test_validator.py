"""Test script for TMF639 OpenAPI validator."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.openapi_validator import OpenAPIValidator
from app.validators import TMF639ResourceValidator


def test_validator_initialization():
    """Test that the validator can load the OpenAPI spec."""
    print("Testing validator initialization...")
    try:
        validator = OpenAPIValidator()
        print(f"✓ OpenAPI spec loaded successfully from: {validator.spec_path}")
        print(f"  - Found {len(validator.schemas)} schemas")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize validator: {e}")
        return False


def test_schema_info():
    """Test getting schema information."""
    print("\nTesting schema info retrieval...")
    try:
        info = TMF639ResourceValidator.get_schema_info('Resource_FVO')
        print(f"✓ Resource_FVO schema info:")
        print(f"  - Description: {info['description'][:100]}...")
        print(f"  - Required fields: {info['required']}")
        print(f"  - Total properties: {len(info['properties'])}")
        return True
    except Exception as e:
        print(f"✗ Failed to get schema info: {e}")
        return False


def test_valid_resource():
    """Test validation with a valid resource."""
    print("\nTesting validation with valid resource...")
    
    valid_resource = {
        "@type": "Resource",
        "category": "Router",
        "name": "Test Router",
        "administrativeState": "unlocked",
        "operationalState": "enable",
        "usageState": "active",
        "resourceStatus": "available"
    }
    
    try:
        result = TMF639ResourceValidator.validate_resource_create(valid_resource)
        print(f"✓ Valid resource passed validation")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def test_invalid_resource_missing_type():
    """Test validation with missing @type."""
    print("\nTesting validation with missing @type...")
    
    invalid_resource = {
        "category": "Router",
        "name": "Test Router"
    }
    
    try:
        TMF639ResourceValidator.validate_resource_create(invalid_resource)
        print(f"✗ Validation should have failed but didn't")
        return False
    except Exception as e:
        print(f"✓ Validation correctly failed: Missing @type")
        return True


def test_invalid_enum_value():
    """Test validation with invalid enum value."""
    print("\nTesting validation with invalid enum value...")
    
    invalid_resource = {
        "@type": "Resource",
        "administrativeState": "invalid_state",
        "name": "Test Router"
    }
    
    try:
        TMF639ResourceValidator.validate_resource_create(invalid_resource)
        print(f"✗ Validation should have failed but didn't")
        return False
    except Exception as e:
        print(f"✓ Validation correctly failed: Invalid enum value")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("TMF639 OpenAPI Validator Test Suite")
    print("=" * 60)
    
    tests = [
        test_validator_initialization,
        test_schema_info,
        test_valid_resource,
        test_invalid_resource_missing_type,
        test_invalid_enum_value
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
