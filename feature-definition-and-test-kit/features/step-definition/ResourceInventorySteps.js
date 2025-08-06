
const resourceInventoryUtilsTMF639 = require('resource-inventory-utils-TMF639');
const { Then } = require('@cucumber/cucumber');
const assert = require('assert');





/**
 * Step: Then the Resource Inventory should contain the following resources:
 * | resource name | category |
 * | ...           | ...      |
 */
Then('the Resource Inventory API should contain the following resources:', async function (dataTable) {
  const expectedResources = dataTable.hashes();
  const missingResources = [];

  const resources = await resourceInventoryUtilsTMF639.getAllResources();
  for (const resource of expectedResources) {
      const { 'resource id': resourceName, category } = resource;
      const foundResource = resources.find(r => r.name === resourceName && r.category === category);
      if (!foundResource) {
      missingResources.push(`${resourceName} (${category})`);
      }
  }

  if (missingResources.length > 0) {
    assert.fail(`Missing resources in Resource Inventory: ${missingResources.join(', ')}`);
  }
});

/**
 * Step: Then the Resource Inventory API should contain a resource with:
 * | resource name | category |
 * | ...           | ...      |
 */
Then('I can query the Resource Inventory API for each of the following resources:', async function (dataTable) {
  const expectedResources = dataTable.hashes();
  const missingResources = [];

  for (const resource of expectedResources) {
    const { 'resource id': resourceName, category } = resource;
    const foundResource = await resourceInventoryUtilsTMF639.findResource(resourceName);
    if (!foundResource) {
      missingResources.push(`${resourceName} (${category})`);
    }
  }

  if (missingResources.length > 0) {
    assert.fail(`Missing resources in Resource Inventory: ${missingResources.join(', ')}`);
  }
});

/**
 * Step: Then I can query the Resource Inventory API with a filter for each of the following:
 * | filter                | number of resources |
 * | ...                   | ...                |
 */
Then('I can query the Resource Inventory API with a filter for each of the following:', async function (dataTable) {
  const filterRows = dataTable.hashes();
  const failedFilters = [];

  for (const row of filterRows) {
    const filter = row['filter'];
    const expectedCount = parseInt(row['number of resources'], 10);
    const resources = await resourceInventoryUtilsTMF639.getResourcesByFilter(filter);
    if (!Array.isArray(resources) || resources.length !== expectedCount) {
      failedFilters.push(`${filter} (expected ${expectedCount}, got ${resources.length})`);
    }
  }

  if (failedFilters.length > 0) {
    assert.fail(`Resource Inventory filter queries failed: ${failedFilters.join(', ')}`);
  }
});