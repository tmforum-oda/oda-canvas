/**
 * The PerformanceMeasurementController provides access to carbon intensity measurements.
 * Supports GET operations (TMF628 standard) plus PATCH for dynamic updates and admin endpoints.
 */

const Controller = require('./Controller');
const service = require('../services/PerformanceMeasurementService');

const listPerformanceMeasurement = async (request, response) => {
  await Controller.handleRequest(request, response, service.listPerformanceMeasurement);
};

const retrievePerformanceMeasurement = async (request, response) => {
  // Extract the ID parameter directly from Express params
  const measurementId = request.params.id;
  
  // Manually inject the ID into the request for the Controller.handleRequest
  if (!request.openapi) request.openapi = {};
  if (!request.openapi.pathParams) request.openapi.pathParams = {};
  request.openapi.pathParams.id = measurementId;
  
  // Set up a minimal schema to help parameter extraction
  request.openapi.schema = {
    parameters: [
      { name: 'id', in: 'path' }
    ]
  };
  
  await Controller.handleRequest(request, response, service.retrievePerformanceMeasurement);
};

/**
 * Update (PATCH) a PerformanceMeasurement by ID
 * Updates specific fields of an existing measurement
 */
const updatePerformanceMeasurement = async (request, response) => {
  const measurementId = request.params.id;
  
  if (!request.openapi) request.openapi = {};
  if (!request.openapi.pathParams) request.openapi.pathParams = {};
  request.openapi.pathParams.id = measurementId;
  
  // Inject body data directly
  if (!request.openapi.body) request.openapi.body = request.body;
  
  // Set up schema with requestBody so Controller.collectRequestParams can extract it
  request.openapi.schema = {
    requestBody: true,  // This tells Controller to extract body
    parameters: [
      { name: 'id', in: 'path' }
    ]
  };
  
  await Controller.handleRequest(request, response, service.updatePerformanceMeasurement);
};

/**
 * Admin endpoint: Reload data from file
 */
const reloadDataFromFile = async (request, response) => {
  await Controller.handleRequest(request, response, service.reloadDataFromFile);
};

/**
 * Admin endpoint: Get data statistics
 */
const getDataStatistics = async (request, response) => {
  await Controller.handleRequest(request, response, service.getDataStatistics);
};


module.exports = {
  listPerformanceMeasurement,
  retrievePerformanceMeasurement,
  updatePerformanceMeasurement,
  reloadDataFromFile,
  getDataStatistics,
};
