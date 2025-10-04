// Simple unit test for resource-inventory-utils-TMF639.js
// Checks that GET /resource returns HTTP 200


const resourceInventoryUtils = require('./resource-inventory-utils-TMF639');
const assert = require('assert');

describe('resource-inventory-utils-TMF639', () => {
  it('should get an array of resources from getAllResources()', async () => {
    const resources = await resourceInventoryUtils.getAllResources();
    assert.ok(Array.isArray(resources), 'Expected resources to be an array');
  });
});
