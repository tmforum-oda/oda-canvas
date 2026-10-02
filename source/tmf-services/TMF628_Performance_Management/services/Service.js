'use strict';

const logger = require('../logger');
const { generateResponseHeaders } = require('../utils/responseHeaders');

class Service {

  static rejectResponse(error, code = 500) {
    code = error.statusCode || code;
    logger.debug("Service.rejectResponse: error= " + error + " code=" + code);
    return { payload: error, code: code };
  }

  static successResponse(payload, code = 200, headerParams = undefined) {
    logger.debug("Service.successResponse: code=" + code + " headers=" + headerParams);
    if (code == 204) payload = null;
    return { payload, code, headerParams };
  }

  /**
   * Apply query filters (field selection and pagination) to resources
   */
  static applyQuery(resources, args) {
    // Handle non-array inputs
    if (!Array.isArray(resources)) {
      return resources;
    }
    
    let result = [...resources];
    const totalSize = result.length;

    // Apply field selection if requested
    if (args.fields) {
      result = result.map(resource => this.applyFields(resource, args.fields));
    }

    // Apply pagination
    let offset = parseInt(args.offset) || 0;
    let limit = parseInt(args.limit) || result.length;
    
    // Slice array for pagination
    result = result.slice(offset, offset + limit);

    // Generate response headers for pagination
    const headerParams = generateResponseHeaders(totalSize, result.length, offset, limit);

    return { data: result, headerParams, totalSize };
  }

  /**
   * Apply field selection to a resource
   */
  static applyFields(resource, fields) {
    if (!fields) return resource;

    const fieldList = fields.split(',').map(f => f.trim());
    const filteredResource = {};

    fieldList.forEach(field => {
      if (resource.hasOwnProperty(field)) {
        filteredResource[field] = resource[field];
      }
    });

    // Always include @type, id, and href if not explicitly requested
    if (!fieldList.includes('@type') && resource['@type']) {
      filteredResource['@type'] = resource['@type'];
    }
    if (!fieldList.includes('id') && resource.id) {
      filteredResource.id = resource.id;
    }
    if (!fieldList.includes('href') && resource.href) {
      filteredResource.href = resource.href;
    }

    return filteredResource;
  }

  /**
   * Create a standardized response
   */
  static createResponse(data, headerParams = undefined, code = 200) {
    return this.successResponse(data, code, headerParams);
  }

}

module.exports = Service;
