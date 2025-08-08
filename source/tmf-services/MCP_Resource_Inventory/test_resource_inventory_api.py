#!/usr/bin/env python3
# Test script for resource_inventory_api.py
# This script tests all functions in the resource_inventory_api.py module
# The test connects to a TMF639 API at http://localhost:8639/tmf-api/resourceInventoryManagement/v5
#
# Examples:
#   python test_resource_inventory_api.py                        # Run all tests and display results
#   python test_resource_inventory_api.py --verbose              # Run with verbose logging

import os
import sys
import json
import time
import logging
import asyncio
import argparse
import warnings
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import the module to test
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from resource_inventory_api import get_resource

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(
                logs_dir,
                f"resource_inventory_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            )
        ),
    ],
)
logger = logging.getLogger("resource-inventory-api-test")

# Print script header
script_description = """
#################################################################
#                                                               #
#             Resource Inventory API Test Script                #
#                                                               #
#  This script provides comprehensive testing capabilities      #
#  for the TMF639 Resource Inventory Management API            #
#                                                               #
#  Note: TMF639 is read-only, so only GET operations are       #
#  tested (no CREATE/UPDATE/DELETE operations)                 #
#                                                               #
#################################################################
"""

# Suppress SSL warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


async def test_get_all_resources():
    """Test getting all resources from the Resource Inventory."""
    try:
        logger.info("==================== TEST: GET ALL RESOURCES ====================")
        
        # Test getting all resources
        logger.info("Testing get_resource() for all resources...")
        all_resources = await get_resource()
        
        if all_resources is None:
            logger.warning("No resources returned from API")
            return False
            
        if isinstance(all_resources, list):
            logger.info(f"Successfully retrieved {len(all_resources)} resources")
            
            # Log some details about the resources if available
            for i, resource in enumerate(all_resources[:3]):  # Show first 3 resources
                logger.info(f"Resource {i+1}: ID={resource.get('id', 'N/A')}, "
                          f"Name={resource.get('name', 'N/A')}, "
                          f"Type={resource.get('@type', 'N/A')}")
                          
            if len(all_resources) > 3:
                logger.info(f"... and {len(all_resources) - 3} more resources")
                
        elif isinstance(all_resources, dict) and "error" in all_resources:
            logger.error(f"Error retrieving resources: {all_resources['error']}")
            return False
        else:
            logger.info(f"Retrieved resources data: {type(all_resources)}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error in test_get_all_resources: {str(e)}")
        logger.error(traceback.format_exc())
        return False


async def test_get_specific_resource():
    """Test getting a specific resource by ID."""
    try:
        logger.info("==================== TEST: GET SPECIFIC RESOURCE ====================")
        
        # First get all resources to find a valid ID
        logger.info("Getting all resources to find a valid resource ID...")
        all_resources = await get_resource()
        
        if not all_resources or not isinstance(all_resources, list) or len(all_resources) == 0:
            logger.warning("No resources available to test specific resource retrieval")
            return True  # Not a failure, just no data
            
        # Use the first resource's ID
        test_resource_id = all_resources[0].get("id")
        if not test_resource_id:
            logger.warning("First resource doesn't have an ID field")
            return True
            
        logger.info(f"Testing get_resource() for specific resource ID: {test_resource_id}")
        
        # Test getting specific resource
        specific_resource = await get_resource(resource_id=test_resource_id)
        
        if specific_resource is None:
            logger.warning(f"No resource returned for ID: {test_resource_id}")
            return False
            
        if isinstance(specific_resource, dict):
            if "error" in specific_resource:
                logger.error(f"Error retrieving resource {test_resource_id}: {specific_resource['error']}")
                return False
            else:
                logger.info(f"Successfully retrieved resource with ID: {test_resource_id}")
                logger.info(f"Resource details: Name={specific_resource.get('name', 'N/A')}, "
                          f"Type={specific_resource.get('@type', 'N/A')}, "
                          f"State={specific_resource.get('resourceStatus', 'N/A')}")
                return True
        else:
            logger.warning(f"Unexpected response type for specific resource: {type(specific_resource)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in test_get_specific_resource: {str(e)}")
        logger.error(traceback.format_exc())
        return False


async def test_get_resources_with_filters():
    """Test getting resources with various filters."""
    try:
        logger.info("==================== TEST: GET RESOURCES WITH FILTERS ====================")
        
        test_filters = [
            {"fields": "id,name,@type"},
            {"limit": 5},
            {"offset": 0, "limit": 3},
        ]
        
        for i, filter_params in enumerate(test_filters):
            logger.info(f"Testing filter {i+1}: {filter_params}")
            
            filtered_resources = await get_resource(**filter_params)
            
            if filtered_resources is None:
                logger.warning(f"No resources returned for filter: {filter_params}")
                continue
                
            if isinstance(filtered_resources, list):
                logger.info(f"Filter {i+1} returned {len(filtered_resources)} resources")
            elif isinstance(filtered_resources, dict) and "error" in filtered_resources:
                logger.error(f"Error with filter {i+1}: {filtered_resources['error']}")
                return False
            else:
                logger.info(f"Filter {i+1} returned data of type: {type(filtered_resources)}")
                
        return True
        
    except Exception as e:
        logger.error(f"Error in test_get_resources_with_filters: {str(e)}")
        logger.error(traceback.format_exc())
        return False


async def test_resource_inventory_connectivity():
    """Test basic connectivity to the Resource Inventory Management API."""
    try:
        logger.info("==================== TEST: API CONNECTIVITY ====================")
        
        logger.info("Testing basic connectivity to Resource Inventory Management API...")
        
        # Simple connectivity test
        result = await get_resource(limit=1)
        
        if result is None:
            logger.error("API connectivity test failed - no response")
            return False
            
        if isinstance(result, dict) and "error" in result:
            logger.error(f"API connectivity test failed - error: {result['error']}")
            return False
            
        logger.info("API connectivity test passed")
        return True
        
    except Exception as e:
        logger.error(f"Error in test_resource_inventory_connectivity: {str(e)}")
        logger.error(traceback.format_exc())
        return False


async def run_all_tests():
    """Run all Resource Inventory API tests."""
    logger.info(script_description)
    
    start_time = time.time()
    total_tests = 0
    passed_tests = 0
    
    # List of test functions to run
    test_functions = [
        test_resource_inventory_connectivity,
        test_get_all_resources,
        test_get_specific_resource,
        test_get_resources_with_filters,
    ]
    
    logger.info("Starting Resource Inventory Management API tests...")
    logger.info(f"Running {len(test_functions)} test suites...")
    
    for test_func in test_functions:
        total_tests += 1
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {test_func.__name__}...")
            
            result = await test_func()
            if result:
                passed_tests += 1
                logger.info(f"✓ {test_func.__name__} PASSED")
            else:
                logger.error(f"✗ {test_func.__name__} FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_func.__name__} FAILED with exception: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {total_tests - passed_tests}")
    logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    logger.info(f"Duration: {duration:.2f} seconds")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed")
        return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test script for Resource Inventory Management API (TMF639)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_resource_inventory_api.py                    # Run all tests
  python test_resource_inventory_api.py --verbose          # Run with verbose logging
        """
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main function to run all tests."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    try:
        success = await run_all_tests()
        
        if success:
            logger.info("\n🎉 All Resource Inventory API tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Some Resource Inventory API tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error during testing: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
