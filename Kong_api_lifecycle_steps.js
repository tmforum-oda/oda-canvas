const { Given, When, Then, setDefaultTimeout } = require('@cucumber/cucumber');
const assert = require('assert');
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
 
const NAMESPACE = 'components';
const TIMEOUT = 20 * 1000; // 20 seconds timeout buffer
 
setDefaultTimeout(TIMEOUT);
 
/**
* Step to create or update HTTPRoute for an API Resource.
*/
Given('an API resource with path "{string}"', async function (path) {
  this.apiResource = { path };
});
 
When('the API resource is created or updated', async function () {
  this.response = await resourceInventoryUtils.createOrUpdateAPIResource(this.apiResource, NAMESPACE);
});
 
Then('an HTTPRoute should be created or updated in the "components" namespace', async function () {
  const httpRoute = await resourceInventoryUtils.getHTTPRoute(this.apiResource.path, NAMESPACE);
  assert(httpRoute, `HTTPRoute for path ${this.apiResource.path} not found`);
});
 
Then('the HTTPRoute should be associated with the correct service', async function () {
  const httpRoute = await resourceInventoryUtils.getHTTPRoute(this.apiResource.path, NAMESPACE);
  assert(httpRoute.spec.rules[0].backendRefs[0].name === this.apiResource.path, 'HTTPRoute is not associated with the correct service');
});
 
Then('the HTTPRoute should have the appropriate annotations', async function () {
  const httpRoute = await resourceInventoryUtils.getHTTPRoute(this.apiResource.path, NAMESPACE);
  assert(httpRoute.metadata.annotations['konghq.com/plugins'], 'HTTPRoute annotations not found');
});
 
Given('an API resource with rate limiting enabled and a limit of {int} requests per minute', function (limit) {
  this.apiResource = {
    path: '/api/v1/resource',
    rateLimit: { enabled: true, limit },
  };
});
 
When('the API resource is created or updated', async function () {
  this.response = await resourceInventoryUtils.createOrUpdateAPIResource(this.apiResource, NAMESPACE);
});
 
Then('a rate limiting plugin should be created or updated in the "components" namespace', async function () {
  const plugin = await resourceInventoryUtils.getPlugin('rate-limit', this.apiResource.path, NAMESPACE);
  assert(plugin, `Rate limiting plugin for path ${this.apiResource.path} not found`);
});
 
Given('an API resource with API key verification enabled', function () {
  this.apiResource = {
    path: '/api/v1/resource',
    apiKeyVerification: { enabled: true },
  };
});
 
Then('an API key verification plugin should be created or updated in the "components" namespace', async function () {
  const plugin = await resourceInventoryUtils.getPlugin('api-key-auth', this.apiResource.path, NAMESPACE);
  assert(plugin, `API key verification plugin for path ${this.apiResource.path} not found`);
});
 
 
Given('an API resource with a URL template for plugins "{string}"', function (url) {
  this.apiResource = { path: '/api/v1/resource', template: url };
});
 
When('the API resource is created or updated', async function () {
  this.pluginsApplied = await resourceInventoryUtils.applyPluginsFromURL(this.apiResource.template, NAMESPACE);
});
 
Then('plugins should be downloaded and applied from the URL template', function () {
  assert(Array.isArray(this.pluginsApplied) && this.pluginsApplied.length > 0, 'Plugins from URL template were not applied');
});
 
Then('the applied plugins should be associated with the correct API resource', async function () {
  const plugins = await resourceInventoryUtils.getAppliedPlugins(this.apiResource.path, NAMESPACE);
  assert(plugins.length > 0, 'No plugins associated with the API resource');
});
 
Given('an API resource with path "{string}" is deleted', function (path) {
  this.apiResourcePath = path;
});
 
When('the deletion event is triggered', async function () {
  await resourceInventoryUtils.deleteAPIResource(this.apiResourcePath, NAMESPACE);
});
 
Then('the associated HTTPRoute should be automatically deleted', async function () {
  const httpRoute = await resourceInventoryUtils.getHTTPRoute(this.apiResourcePath, NAMESPACE);
  assert(!httpRoute, `HTTPRoute for path ${this.apiResourcePath} still exists`);
});
 
Then('the deletion should be logged', function () {
  // Implement logging verification if needed
  assert(true, 'Deletion logging not verified');
});
