/* eslint-disable no-unused-vars */
const Service = require('./Service');
const KubernetesResourceService = require('./KubernetesResourceService');
const logger = require('../logger');

// Initialize Kubernetes service
const k8sService = new KubernetesResourceService();

/**
 * List or find Resource objects from ODA Canvas Kubernetes cluster
 * This operation lists Resources from Components and ExposedAPIs
 *
 * fields String Comma-separated properties to be provided in response (optional)
 * offset Integer Requested index for start of resources to be provided in response (optional)
 * limit Integer Requested number of resources to be provided in response (optional)
 * returns List
 **/
const listResource = (args, context /* fieldsoffsetlimit */) =>
  new Promise(
    async (resolve) => {
      context.classname = "Resource";
      context.operationId = "listResource";
      context.method = "get";      try {
        // Get all resources from Kubernetes using the new method
        const allResources = await k8sService.listResources();

        // Apply filtering, pagination etc.
        const filteredResources = Service.applyQuery(allResources, args, context);
        
        resolve(Service.createResponse(filteredResources, context));

      } catch (e) {
        logger.error("listResource: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Invalid input',
          e.status || 500,
        ));
      }
    },
  )

/**
 * Retrieves a Resource by ID from ODA Canvas Kubernetes cluster
 * This operation retrieves a Resource entity. Supports Components and ExposedAPIs.
 *
 * id String Identifier of the Resource
 * fields String Comma-separated properties to be provided in response (optional)
 * returns Resource
 **/
const retrieveResource = (args, context /* idfields */) =>
  new Promise(
    async (resolve) => {
      context.classname = "Resource";
      context.operationId = "retrieveResource";
      context.method = "get";      
      try {
        // Get the specific resource by ID
        const resource = await k8sService.getResourceById(args.id);

        if (!resource) {
          resolve(Service.rejectResponse(
            `Resource with id ${args.id} not found`,
            404,
          ));
          return;
        }

        // Apply field filtering if specified
        const filteredResource = Service.applyFields(resource, args.fields);
        
        resolve(Service.createResponse(filteredResource, context));

      } catch (e) {
        logger.error("retrieveResource: error=" + e);
        resolve(Service.rejectResponse(
          e.message || 'Invalid input',
          e.status || 500,
        ));
      }
    },
  )

module.exports = {
  listResource,
  retrieveResource,
};
