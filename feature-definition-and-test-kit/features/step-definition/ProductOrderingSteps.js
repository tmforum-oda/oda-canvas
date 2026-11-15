// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const componentUtils = require('component-utils');

const { When, Then } = require('@cucumber/cucumber');
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
const ORDER_TIMEOUT = 60 * 1000; // 60 seconds
const ORDER_RETRIES = 5; // the product order API looks up its downstream APIs on each request, with a 1 second timeout
const ORDER_RETRY_DELAY = 5 * 1000; // 5 seconds
const DEBUG_LOGS = false; // set to true for verbose debugging

/**
 * Get the URL of an ExposedAPI of a component, failing the step if it has none.
 *
 * @param {string} componentName - The name of the component.
 * @param {string} apiName - The name of the ExposedAPI.
 * @returns {Promise<string>} - The URL of the ExposedAPI.
 */
async function getRequiredAPIURL(componentName, apiName) {
  const apiURL = await componentUtils.getAPIURL(componentName, apiName, NAMESPACE);
  assert.notEqual(apiURL, null, `Can't find the '${apiName}' API for component '${componentName}'`);
  console.log(`✅ Located the '${apiName}' API of component '${componentName}': ${apiURL}`);
  return apiURL;
}

function httpRequest(apiURL, method, path, body) {
  const request = chai.request(apiURL)[method](path)
    .agent(agent)  // Use the custom HTTPS agent that allows self-signed certificates
    .trustLocalhost(true)
    .disableTLSCerts();
  return body ? request.send(body) : request.send();
}

/**
 * Create a TMF622 product order with one 'add' order item for the given product offering.
 * The product order API validates the offering against its downstreamproductcatalog DependentAPI
 * and returns 422 if it can't find it. With retryOnUnprocessable, a 422 is retried a few times,
 * because the first requests to the downstream API can time out while its route warms up.
 *
 * @param {object} world - The Cucumber World, where the response is stored.
 * @param {string} componentName - The name of the product order component.
 * @param {object} productOffering - The productOffering reference (id and name).
 * @param {boolean} retryOnUnprocessable - Whether to retry a 422 response.
 */
async function createProductOrder(world, componentName, productOffering, retryOnUnprocessable) {
  const productOrderingAPIURL = await getRequiredAPIURL(componentName, 'productorderingmanagement');
  const productOrder = {
    '@type': 'ProductOrder',
    description: 'BDD test order for ' + (productOffering.name || productOffering.id),
    productOrderItem: [{
      '@type': 'ProductOrderItem',
      id: '1',
      quantity: 1,
      action: 'add',
      productOffering: Object.assign({ '@type': 'ProductOfferingRef' }, productOffering)
    }]
  };

  let response = null;
  for (let attempt = 1; attempt <= ORDER_RETRIES; attempt++) {
    console.log(`Creating product order for product offering '${productOffering.id}' (attempt ${attempt}/${ORDER_RETRIES})`);
    response = await httpRequest(productOrderingAPIURL, 'post', '/productOrder', productOrder);
    console.log(`Product order API returned status ${response.status}`);
    if (DEBUG_LOGS) {
      console.log(JSON.stringify(response.body, null, 2));
    }
    if (!(retryOnUnprocessable && response.status === 422) || attempt === ORDER_RETRIES) {
      break;
    }
    console.log(`Got 422 (${JSON.stringify(response.body)}), retrying in ${ORDER_RETRY_DELAY / 1000} seconds`);
    await new Promise(resolve => setTimeout(resolve, ORDER_RETRY_DELAY));
  }
  world.productOrderResponse = response;
  world.productOffering = productOffering;
}

/**
 * Create a product order for a product offering that is in the downstream product catalog.
 *
 * @param {string} componentName - The name of the product order component.
 * @param {string} offeringName - The name of the product offering.
 * @param {string} catalogComponentName - The name of the product catalog component that holds the offering.
 */
When('I create a product order in the {string} component for the {string} product offering from the {string} component', { timeout: ORDER_TIMEOUT }, async function (componentName, offeringName, catalogComponentName) {
  console.log('\n=== Starting Product Order Creation ===');
  const productCatalogAPIURL = await getRequiredAPIURL(catalogComponentName, 'productcatalogmanagement');
  const offeringResponse = await httpRequest(productCatalogAPIURL, 'get', '/productOffering');
  assert.equal(offeringResponse.status, 200, `Failed to get 'productOffering' data from component '${catalogComponentName}'. Status: ${offeringResponse.status}`);
  const offering = offeringResponse.body.find(item => item.name === offeringName);
  assert.ok(offering, `Product offering '${offeringName}' not found in component '${catalogComponentName}'`);
  console.log(`✅ Found product offering '${offeringName}' with id '${offering.id}'`);

  await createProductOrder(this, componentName, { id: offering.id, name: offering.name }, true);
  console.log('=== Product Order Creation Complete ===');
});

/**
 * Create a product order for a product offering id, which may not be in the downstream product catalog.
 *
 * @param {string} componentName - The name of the product order component.
 * @param {string} offeringId - The id of the product offering.
 */
When('I create a product order in the {string} component for a product offering with id {string}', { timeout: ORDER_TIMEOUT }, async function (componentName, offeringId) {
  console.log('\n=== Starting Product Order Creation ===');
  await createProductOrder(this, componentName, { id: offeringId }, false);
  console.log('=== Product Order Creation Complete ===');
});

/**
 * Verify that the last product order was created, in the given state.
 *
 * @param {string} state - The expected state of the product order.
 */
Then('the product order should be created with a state of {string}', function (state) {
  const response = this.productOrderResponse;
  assert.ok(response, 'No product order was created');
  assert.equal(response.status, 201, `Expected the product order to be created (201), but got ${response.status}: ${JSON.stringify(response.body)}`);
  assert.equal(response.body.state, state, `Expected the product order to be in state '${state}', but it is in state '${response.body.state}'`);
  console.log(`✅ Product order '${response.body.id}' created in state '${state}'`);
});

/**
 * Verify that the last product order was rejected with the given HTTP status.
 *
 * @param {string} status - The expected HTTP status.
 */
Then('the product order should be rejected with a status of {string}', function (status) {
  const response = this.productOrderResponse;
  assert.ok(response, 'No product order was attempted');
  assert.equal(response.status, parseInt(status), `Expected the product order to be rejected with ${status}, but got ${response.status}: ${JSON.stringify(response.body)}`);
  console.log(`✅ Product order rejected with status ${status}: ${JSON.stringify(response.body)}`);
});

/**
 * Verify that the product order component created the ordered product in the downstream product inventory,
 * and recorded its id on the order item.
 *
 * @param {string} inventoryComponentName - The name of the product inventory component.
 */
Then('the {string} component should have the product from the product order', async function (inventoryComponentName) {
  console.log('\n=== Starting Product Inventory Verification ===');
  const orderItem = this.productOrderResponse.body.productOrderItem[0];
  assert.ok(orderItem.product && orderItem.product.id, `The product order item has no product id, so no product was created in the product inventory: ${JSON.stringify(orderItem)}`);

  const productInventoryAPIURL = await getRequiredAPIURL(inventoryComponentName, 'productinventorymanagement');
  const response = await httpRequest(productInventoryAPIURL, 'get', '/product/' + orderItem.product.id);
  assert.equal(response.status, 200, `Product '${orderItem.product.id}' not found in component '${inventoryComponentName}'. Status: ${response.status}`);
  assert.equal(response.body.productOffering && response.body.productOffering.id, this.productOffering.id,
    `Product '${orderItem.product.id}' is for product offering '${JSON.stringify(response.body.productOffering)}', expected '${this.productOffering.id}'`);
  console.log(`✅ Product '${orderItem.product.id}' for product offering '${this.productOffering.id}' is in component '${inventoryComponentName}'`);
  console.log('=== Product Inventory Verification Complete ===');
});
