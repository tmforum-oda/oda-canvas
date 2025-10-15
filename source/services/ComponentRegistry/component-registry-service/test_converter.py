"""
Test script for TMF639 Converter

This script tests the converter with the actual JSON files provided.
"""

import json
from pathlib import Path
from tmf639_converter import TMF639Converter, convert_component_list_to_tmf639, convert_tmf639_to_component_list


def load_json_file(filepath: str):
    """Load JSON data from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: str, data):
    """Save JSON data to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t')


def main():
    # Define file paths
    base_path = Path(__file__).parent / 'INFO' / 'JSON_STRUCTURES'
    component_file = base_path / 'component-r-cat-component.json'
    tmf639_file = base_path / 'converted-to-tmf639-resource-r-cat-component.json'
    
    print("TMF639 Converter Test")
    print("=" * 80)
    
    # Test 1: Component to TMF639
    print("\n[Test 1] Converting Component format to TMF639 format...")
    component_data = load_json_file(component_file)
    print(f"Loaded {len(component_data)} component(s) from {component_file.name}")
    
    tmf639_resources = convert_component_list_to_tmf639(component_data)
    print(f"Generated {len(tmf639_resources)} TMF639 resource(s)")
    
    output_file = base_path / 'test-output-tmf639.json'
    save_json_file(output_file, tmf639_resources)
    print(f"Saved to: {output_file.name}")
    
    # Test 2: TMF639 to Component
    print("\n[Test 2] Converting TMF639 format to Component format...")
    tmf639_data = load_json_file(tmf639_file)
    print(f"Loaded {len(tmf639_data)} TMF639 resource(s) from {tmf639_file.name}")
    
    components = convert_tmf639_to_component_list(tmf639_data)
    print(f"Generated {len(components)} component(s)")
    
    output_file = base_path / 'test-output-component.json'
    save_json_file(output_file, components)
    print(f"Saved to: {output_file.name}")
    
    # Test 3: Round-trip validation
    print("\n[Test 3] Round-trip conversion test...")
    original_component = load_json_file(component_file)[0]
    
    # Convert to TMF639 and back
    tmf639_converted = TMF639Converter.component_to_tmf639(original_component)
    round_trip_component = TMF639Converter.tmf639_to_component(tmf639_converted)
    
    # Compare key fields
    print("\nComparing original and round-trip component:")
    print(f"  Component name: {original_component['component_name']} -> {round_trip_component['component_name']}")
    print(f"  Version: {original_component['component_version']} -> {round_trip_component['component_version']}")
    print(f"  APIs count: {len(original_component['exposed_apis'])} -> {len(round_trip_component['exposed_apis'])}")
    
    if original_component['component_name'] == round_trip_component['component_name']:
        print("\n✓ Round-trip conversion successful!")
    else:
        print("\n✗ Round-trip conversion failed - data mismatch")
    
    print("\n" + "=" * 80)
    print("Test completed. Check the test-output-*.json files in INFO/JSON_STRUCTURES/")


if __name__ == "__main__":
    main()
