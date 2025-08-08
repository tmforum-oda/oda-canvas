const resourceInventoryUtilsTMF639 = require('resource-inventory-utils-TMF639');
const { Then } = require('@cucumber/cucumber');
const assert = require('assert');

const DEBUG_LOGS = false; // set to true for verbose debugging

/**
 * Step: Then the Resource Inventory should contain the following resources:
 * | resource name | category |
 * | ...           | ...      |
 */
Then('the Resource Inventory API should contain the following resources:', async function (dataTable) {
  console.log('\n=== Starting Resource Inventory Data Verification ===');
  console.log('Verifying expected resources exist in Resource Inventory');
  
  try {
    const expectedResources = dataTable.hashes();
    console.log(`Verifying ${expectedResources.length} expected resources`);
    const missingResources = [];

    console.log('Retrieving all resources from Resource Inventory API...');
    const resources = await resourceInventoryUtilsTMF639.getAllResources();
    console.log(`✅ Successfully retrieved ${resources.length} resources from Resource Inventory API`);
    
    if (DEBUG_LOGS) {
      console.log('Retrieved resources:', JSON.stringify(resources, null, 2));
    }

    let verifiedCount = 0;
    for (const resource of expectedResources) {
      const { 'resource id': resourceName, category } = resource;
      console.log(`Verifying resource ${verifiedCount + 1}/${expectedResources.length}: '${resourceName}' (${category})`);
      
      const foundResource = resources.find(r => r.name === resourceName && r.category === category);
      if (!foundResource) {
        console.log(`❌ Missing resource: '${resourceName}' (${category})`);
        missingResources.push(`${resourceName} (${category})`);
      } else {
        console.log(`✅ Verified resource '${resourceName}' (${category}) exists`);
        verifiedCount++;
      }
    }

    if (missingResources.length > 0) {
      console.error(`❌ ${missingResources.length} resources missing from Resource Inventory`);
      console.error('Missing resources:', missingResources.join(', '));
      assert.fail(`Missing resources in Resource Inventory: ${missingResources.join(', ')}`);
    }
    
    console.log(`✅ Successfully verified all ${verifiedCount} resources in Resource Inventory`);
    console.log('=== Resource Inventory Data Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during Resource Inventory data verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Resource Inventory API endpoint not accessible');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    console.error('- Expected resources not properly created or synchronized');
    
    console.log('=== Resource Inventory Data Verification Failed ===');
    throw error;
  }
});

/**
 * Step: Then I can query the Resource Inventory API for each of the following resources:
 * | resource id | category |
 * | ...         | ...      |
 */
Then('I can query the Resource Inventory API for each of the following resources:', async function (dataTable) {
  console.log('\n=== Starting Resource Inventory Individual Query Verification ===');
  console.log('Verifying individual resource queries in Resource Inventory');
  
  try {
    const expectedResources = dataTable.hashes();
    console.log(`Querying ${expectedResources.length} individual resources`);
    const missingResources = [];

    let queriedCount = 0;
    for (const resource of expectedResources) {
      const { 'resource id': resourceName, category } = resource;
      console.log(`Querying resource ${queriedCount + 1}/${expectedResources.length}: '${resourceName}' (${category})`);
      
      try {
        const foundResource = await resourceInventoryUtilsTMF639.findResource(resourceName);
        if (!foundResource) {
          console.log(`❌ Resource not found: '${resourceName}' (${category})`);
          missingResources.push(`${resourceName} (${category})`);
        } else {
          console.log(`✅ Successfully queried resource '${resourceName}' (${category})`);
          queriedCount++;
          
          if (DEBUG_LOGS) {
            console.log('Found resource:', JSON.stringify(foundResource, null, 2));
          }
        }
      } catch (queryError) {
        console.error(`❌ Error querying resource '${resourceName}': ${queryError.message}`);
        missingResources.push(`${resourceName} (${category})`);
      }
    }

    if (missingResources.length > 0) {
      console.error(`❌ ${missingResources.length} resources could not be queried from Resource Inventory`);
      console.error('Missing resources:', missingResources.join(', '));
      assert.fail(`Missing resources in Resource Inventory: ${missingResources.join(', ')}`);
    }
    
    console.log(`✅ Successfully queried all ${queriedCount} individual resources`);
    console.log('=== Resource Inventory Individual Query Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during Resource Inventory individual query verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Resource Inventory API endpoint not accessible');
    console.error('- Individual resource query endpoints not properly configured');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    console.error('- Resource IDs not matching expected format or values');
    
    console.log('=== Resource Inventory Individual Query Verification Failed ===');
    throw error;
  }
});

/**
 * Step: Then I can query the Resource Inventory API with a filter for each of the following:
 * | filter                | number of resources |
 * | ...                   | ...                |
 */
Then('I can query the Resource Inventory API with a filter for each of the following:', async function (dataTable) {
  console.log('\n=== Starting Resource Inventory Filter Query Verification ===');
  console.log('Verifying filtered queries in Resource Inventory');
  
  try {
    const filterRows = dataTable.hashes();
    console.log(`Testing ${filterRows.length} filter queries`);
    const failedFilters = [];

    let testedCount = 0;
    for (const row of filterRows) {
      const filter = row['filter'];
      const expectedCount = parseInt(row['number of resources'], 10);
      console.log(`Testing filter ${testedCount + 1}/${filterRows.length}: '${filter}' (expecting ${expectedCount} resources)`);
      
      try {
        const resources = await resourceInventoryUtilsTMF639.getResourcesByFilter(filter);
        
        if (DEBUG_LOGS) {
          console.log(`Filter '${filter}' returned:`, JSON.stringify(resources, null, 2));
        }
        
        if (!Array.isArray(resources)) {
          console.error(`❌ Filter '${filter}' returned non-array result: ${typeof resources}`);
          failedFilters.push(`${filter} (expected array, got ${typeof resources})`);
        } else if (resources.length !== expectedCount) {
          console.error(`❌ Filter '${filter}' returned ${resources.length} resources, expected ${expectedCount}`);
          failedFilters.push(`${filter} (expected ${expectedCount}, got ${resources.length})`);
        } else {
          console.log(`✅ Filter '${filter}' returned correct number of resources: ${resources.length}`);
          testedCount++;
        }
      } catch (filterError) {
        console.error(`❌ Error executing filter '${filter}': ${filterError.message}`);
        failedFilters.push(`${filter} (query error: ${filterError.message})`);
      }
    }

    if (failedFilters.length > 0) {
      console.error(`❌ ${failedFilters.length} filter queries failed`);
      console.error('Failed filters:', failedFilters.join(', '));
      assert.fail(`Resource Inventory filter queries failed: ${failedFilters.join(', ')}`);
    }
    
    console.log(`✅ Successfully tested all ${testedCount} filter queries`);
    console.log('=== Resource Inventory Filter Query Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during Resource Inventory filter query verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Resource Inventory API filter endpoints not accessible');
    console.error('- Filter query syntax not supported by the API');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    console.error('- Filter parameters not matching expected format or values');
    console.error('- Resource data not properly indexed for filtering');
    
    console.log('=== Resource Inventory Filter Query Verification Failed ===');
    throw error;
  }
});