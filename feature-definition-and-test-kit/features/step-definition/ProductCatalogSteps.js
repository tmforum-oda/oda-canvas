const componentUtils = require('component-utils')

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)

// Create an HTTPS agent that ignores self-signed certificates
const https = require('https');
const agent = new https.Agent({
  rejectUnauthorized: false
});

const NAMESPACE = 'components'
const API_DEPLOY_TIMEOUT = 10 * 1000 // 10 seconds
const API_URL_TIMEOUT = 60 * 1000 // 60 seconds
const API_READY_TIMEOUT = 120 * 1000 // 60 seconds
const TIMEOUT_BUFFER = 5 * 1000 // 5 seconds as additional buffer to the timeouts above for the wrapping function

setDefaultTimeout( 20 * 1000);

/**
 * Validate that the product catalog has the required data (and add it if necessary).
 *
 * @param {string} APIName - The name of the ExposedAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the ExposedAPI resource is available.
 */
Given('the {string} component in the {string} release has the following {string} data:', async function (componentName, releaseName, resourceType, dataTable) {
  // get access to the Product Catalog API
  const componentInstanceName = releaseName  + '-' + componentName
  console.log('Component Instance Name: ' + componentInstanceName)
  productCatalogAPIURL = await componentUtils.getAPIURL(componentInstanceName, 'productcatalogmanagement', NAMESPACE)
  assert.notEqual(productCatalogAPIURL, null, "Can't find Product Catalog API")

  // query the Product Catalog API to get the resourceType data
  const response = await chai.request(productCatalogAPIURL)
    .get('/' + resourceType)
    .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
    .send()
  assert.equal(response.status, 200, 'Failed to get ' + resourceType + ' data from Product Catalog API')
  const existingData = response.body
  // console.log('existingData')
  // console.log(existingData)

  // compare the existing data with the expected data
  const expectedData = dataTable.hashes()
  // console.log('expectedData')
  // console.log(expectedData)

  // delete any existing data that is not in the expected data
  for (const index in existingData) {
    const existingItem = existingData[index]
    const found = expectedData.find(item => item.name === existingItem.name)
    if (!found) {
      console.log('Deleting ' + resourceType + ' data: ' + existingItem.name)
      const delResponse = await chai.request(productCatalogAPIURL)
        .delete('/' + resourceType + '/' + existingItem.id)
        .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
        .send()
      assert.equal(delResponse.status, 204, 'Failed to delete ' + resourceType + ' data from Product Catalog API')
    }
  }

  // add any expected data that is not in the existing data
  for (const index in expectedData) {
    const expectedItem = expectedData[index]
    const found = existingData.find(item => item.name === expectedItem.name)
    if (!found) {
      console.log('Adding ' + resourceType + ' data: ' + expectedItem.name)
      const postResponse = await chai.request(productCatalogAPIURL)
        .post('/' + resourceType)
        .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
        .send(expectedItem)
      assert.equal(postResponse.status, 201, 'Failed to post ' + resourceType + ' data to Product Catalog API')
    }
  }

});

When('I query the {string} component in the {string} release for {string} data:', async function (componentName, releaseName, resourceType) {
  // Write code here that turns the phrase above into concrete actions
  const componentInstanceName = releaseName  + '-' + componentName
  console.log('Component Instance Name: ' + componentInstanceName)
  productCatalogAPIURL = await componentUtils.getAPIURL(componentInstanceName, 'productcatalogmanagement', NAMESPACE)
  assert.notEqual(productCatalogAPIURL, null, "Can't find Product Catalog API")

  // query the Product Catalog API to get the resourceType data
  const response = await chai.request(productCatalogAPIURL)
    .get('/' + resourceType)
    .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
    .send()
  assert.equal(response.status, 200, 'Failed to get ' + resourceType + ' data from Product Catalog API')
  this.existingData = response.body
});

Then('I should see the following {string} data in the federated product catalog:', async function (resourceType, dataTable) {
  const expectedData = dataTable.hashes()
  // compare the existing data with the expected data
  for (const index in expectedData) {
    const expectedItem = expectedData[index]
    // console.log('expectedItem')
    // console.log(expectedItem)
    let foundName = null;
    try {
        found = this.existingData.find(item => item.name === expectedItem.name);
        foundName = found.name;
    } catch (error) {
        foundName = ''; 
    }
    // console.log('found')
    // console.log(found)
    assert.equal(foundName, expectedItem.name, 'Expected ' + resourceType + ' data with name "' + expectedItem.name + '" not found in federated product catalog API')
  }
});