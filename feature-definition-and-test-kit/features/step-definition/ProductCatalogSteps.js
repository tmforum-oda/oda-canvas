// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const componentUtils = require('component-utils');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);

// Create an HTTPS agent that ignores self-signed certificates
const https = require('https');
const agent = new https.Agent({
  rejectUnauthorized: false
});

const NAMESPACE = 'components';
const API_DEPLOY_TIMEOUT = 10 * 1000; // 10 seconds
const API_URL_TIMEOUT = 60 * 1000; // 60 seconds
const API_READY_TIMEOUT = 120 * 1000; // 120 seconds
const TIMEOUT_BUFFER = 5 * 1000; // 5 seconds as additional buffer to the timeouts above for the wrapping function
const DEBUG_LOGS = false; // set to true for verbose debugging

setDefaultTimeout(20 * 1000);

/**
 * Validate that the product catalog has the required data (and add it if necessary).
 *
 * @param {string} componentName - The name of the component.
 * @param {string} releaseName - The name of the release.
 * @param {string} resourceType - The type of resource to validate.
 * @param {object} dataTable - Data table containing expected resource data.
 * @returns {Promise<void>} - A Promise that resolves when the resource data is validated and synchronized.
 */
Given('the {string} component has the following {string} data:', async function (componentName, resourceType, dataTable) {
  console.log('\n=== Starting Product Catalog Data Synchronization ===');
  console.log(`Synchronizing '${resourceType}' data for component '${componentName}'`);

  try {
    
    const productCatalogAPIURL = await componentUtils.getAPIURL(componentName, 'productcatalogmanagement', NAMESPACE);
    assert.notEqual(productCatalogAPIURL, null, `Can't find Product Catalog API for component '${componentName}'`);
    
    console.log(`✅ Successfully located Product Catalog API: ${productCatalogAPIURL}`);

    // Query the Product Catalog API to get the existing resourceType data
    console.log(`Querying existing '${resourceType}' data from Product Catalog API...`);
    const response = await chai.request(productCatalogAPIURL)
      .get('/' + resourceType)
      .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
      .trustLocalhost(true)
      .disableTLSCerts()
      .send();
    
    assert.equal(response.status, 200, `Failed to get '${resourceType}' data from Product Catalog API. Status: ${response.status}`);
    const existingData = response.body;
    
    if (DEBUG_LOGS) {
      console.log('Existing data:', JSON.stringify(existingData, null, 2));
    }

    // Compare the existing data with the expected data
    const expectedData = dataTable.hashes();
    console.log(`Expected data contains ${expectedData.length} ${resourceType} items`);
    
    if (DEBUG_LOGS) {
      console.log('Expected data:', JSON.stringify(expectedData, null, 2));
    }

    // Delete any existing data that is not in the expected data
    let deletedCount = 0;
    for (const index in existingData) {
      const existingItem = existingData[index];
      const found = expectedData.find(item => item.name === existingItem.name);
      if (!found) {
        console.log(`Deleting obsolete '${resourceType}' item: '${existingItem.name}'`);
        const delResponse = await chai.request(productCatalogAPIURL)
          .delete('/' + resourceType + '/' + existingItem.id)
          .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
          .trustLocalhost(true)
          .disableTLSCerts()
          .send();
        
        assert.equal(delResponse.status, 204, `Failed to delete '${resourceType}' item '${existingItem.name}' from Product Catalog API. Status: ${delResponse.status}`);
        deletedCount++;
      }
    }

    // Add any expected data that is not in the existing data
    let createdCount = 0;
    for (const index in expectedData) {
      const expectedItem = expectedData[index];
      const found = existingData.find(item => item.name === expectedItem.name);
      if (!found) {
        console.log(`Creating new '${resourceType}' item: '${expectedItem.name}'`);
        const postResponse = await chai.request(productCatalogAPIURL)
          .post('/' + resourceType)
          .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
          .trustLocalhost(true)
          .disableTLSCerts()
          .send(expectedItem);
        
        assert.equal(postResponse.status, 201, `Failed to create '${resourceType}' item '${expectedItem.name}' in Product Catalog API. Status: ${postResponse.status}`);
        createdCount++;
      }
    }

    console.log(`✅ Data synchronization complete: ${createdCount} items created, ${deletedCount} items deleted`);
    console.log('=== Product Catalog Data Synchronization Complete ===');

  } catch (error) {
    console.error(`❌ Error during Product Catalog data synchronization: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Release: '${releaseName}'`);
    console.error(`- Resource type: '${resourceType}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Product Catalog API endpoint not accessible');
    console.error('- Component not properly deployed');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    
    console.log('=== Product Catalog Data Synchronization Failed ===');
    throw error;
  }
});

/**
 * Query the product catalog component for specific resource data.
 *
 * @param {string} componentName - The name of the component.
 * @param {string} resourceType - The type of resource to query.
 * @returns {Promise<void>} - A Promise that resolves when the query is complete.
 */
When('I query the {string} component for {string} data:', async function (componentName, resourceType) {
  console.log('\n=== Starting Product Catalog Data Query ===');
  console.log(`Querying '${resourceType}' data from component '${componentName}'`);

  try {
  
    const productCatalogAPIURL = await componentUtils.getAPIURL(componentName, 'productcatalogmanagement', NAMESPACE);
    assert.notEqual(productCatalogAPIURL, null, `Can't find Product Catalog API for component '${componentName}'`);
    
    console.log(`✅ Successfully located Product Catalog API: ${productCatalogAPIURL}`);

    // Query the Product Catalog API to get the resourceType data
    console.log(`Making API request to retrieve '${resourceType}' data...`);
    const response = await chai.request(productCatalogAPIURL)
      .get('/' + resourceType)
      .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
      .trustLocalhost(true)
      .disableTLSCerts()
      .send();
    
    assert.equal(response.status, 200, `Failed to get '${resourceType}' data from Product Catalog API. Status: ${response.status}`);
    this.existingData = response.body;
    
    console.log(`✅ Successfully retrieved ${this.existingData.length} '${resourceType}' items from component '${componentName}'`);
    
    if (DEBUG_LOGS) {
      console.log(`Component '${componentName}' has the following '${resourceType}' data:`);
      console.log(JSON.stringify(this.existingData, null, 2));
    }
    
    console.log('=== Product Catalog Data Query Complete ===');

  } catch (error) {
    console.error(`❌ Error during Product Catalog data query: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Release: '${releaseName}'`);
    console.error(`- Resource type: '${resourceType}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Product Catalog API endpoint not accessible');
    console.error('- Component not properly deployed');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    
    console.log('=== Product Catalog Data Query Failed ===');
    throw error;
  }
});

/**
 * Verify that the federated product catalog contains the expected data.
 *
 * @param {string} resourceType - The type of resource to verify.
 * @param {object} dataTable - Data table containing expected resource data.
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete.
 */
Then('I should see the following {string} data in the federated product catalog:', async function (resourceType, dataTable) {
  console.log('\n=== Starting Federated Product Catalog Data Verification ===');
  console.log(`Verifying '${resourceType}' data in federated product catalog`);
  
  try {
    const expectedData = dataTable.hashes();
    console.log(`Verifying ${expectedData.length} expected '${resourceType}' items`);
    
    // Compare the existing data with the expected data
    let verifiedCount = 0;
    for (const index in expectedData) {
      const expectedItem = expectedData[index];
      console.log(`Verifying item ${parseInt(index) + 1}/${expectedData.length}: '${expectedItem.name}'`);
      
      let foundName = null;
      let found = null;
      try {
        found = this.existingData.find(item => item.name === expectedItem.name);
        foundName = found ? found.name : null;
      } catch (error) {
        foundName = null;
        console.error(`⚠️  Error searching for item '${expectedItem.name}': ${error.message}`);
      }
      
      if (DEBUG_LOGS && found) {
        console.log('Found item:', JSON.stringify(found, null, 2));
      }
      
      assert.equal(foundName, expectedItem.name, `Expected '${resourceType}' data with name "${expectedItem.name}" not found in federated product catalog API`);
      verifiedCount++;
      console.log(`✅ Verified item '${expectedItem.name}' exists in federated catalog`);
    }
    
    console.log(`✅ Successfully verified all ${verifiedCount} '${resourceType}' items in federated product catalog`);
    console.log('=== Federated Product Catalog Data Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during federated product catalog verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Resource type: '${resourceType}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (this.existingData) {
      console.error(`- Available items in catalog: ${this.existingData.length}`);
      console.error('- Available item names:', this.existingData.map(item => item.name).join(', '));
    } else {
      console.error('- No existing data available for comparison');
    }
    
    console.error('Possible causes:');
    console.error('- Expected data item not present in the federated catalog');
    console.error('- Data synchronization issue between catalog instances');
    console.error('- Previous query step failed to retrieve data');
    console.error('- Component federation not properly configured');
    
    console.log('=== Federated Product Catalog Data Verification Failed ===');
    throw error;
  }
});