const logger = require('../logger');

class Controller {
  static sendResponse(response, payload) {
    /**
     * The default response-code is 200. We want to allow to change that. in That case,
     * payload will be an object consisting of a code and a payload. If not customized
     * send 200 and the payload as received in this method.
     */

    // logger.info("Controller::sendResponse:: " + JSON.stringify(payload,null,2))

    response.status(payload.code || 200);

    const headers = payload.headerParams
    if (headers) {
      headers.forEach((item) => {
        const key = Object.keys(item)[0];
        const val = item[key];
        response.setHeader(key,val);
      });
    }

    const responsePayload = payload?.payload ? payload.payload : payload;
    if(responsePayload==null || payload?.code==204) {
      response.end()
    } else if (responsePayload instanceof Object) {
      response.json(responsePayload)
    } else {
      response.end(responsePayload);
    }

  }

  static sendError(response, error) {
    try {

      logger.debug("sendError: error=" + JSON.stringify(error,null,2))

      if(error?.error) error=error.error

      if(error?.statusCode) {
        response.status(error.statusCode)
      } else {
        response.status(500)
      }

      if (error instanceof Object) {
        response.json(error)
      } else {
        response.end(error?.message || '')
      } 
    } catch(e) {
      logger.info("sendError: catch error=" + e)
    }
  }

  static collectFiles(request) {

    // logger.debug('Checking if files are expected in schema')
  
    try {
      if (request.openapi.schema.requestBody) { 
        const [contentType] = request.headers['content-type'].split(';')
        if (contentType === 'multipart/form-data') {
          const contentSchema = request.openapi.schema.requestBody.content[contentType].schema
          Object.entries(contentSchema.properties).forEach(([name, property]) => {
            if (property.type === 'string' && ['binary', 'base64'].indexOf(property.format) > -1) {
              request.body[name] = request.files.find(file => file.fieldname === name)
            }
          })
        } else if (request.openapi.schema.requestBody.content[contentType] && request.files) {
          [request.body] = request.files
        }
      }
    } catch(e) {
      logger.debug('collectFiles: exception=' + e)
    }

  }

  static collectRequestParams(request) {

    this.collectFiles(request)
    const requestParams = {}

    try {
      if (request.openapi.schema.requestBody) {
        requestParams.body = request.body
      }
      if(request.openapi.schema.parameters) {
        request.openapi.schema.parameters.forEach((param) => {
          if (param.in === 'path') {
            requestParams[param.name] = request.openapi.pathParams[param.name]
          } else if (param.in === 'query') {
            requestParams[param.name] = request.query[param.name]
          }
        })
      }

      // add other query params to dynamic element
      if(request.query) {
        Object.keys(request.query).forEach((param) => {
          if(!requestParams[param]) {
            if(!requestParams.dynamic) requestParams.dynamic = {}
            requestParams.dynamic[param] = request.query[param]
          }
        })
      }
    } catch(e) {
      logger.debug('collectRequestParams: exception=' + e)
    }

    return requestParams

  }

  static async handleRequest(request, response, serviceOperation) {

    logger.debug('Controller::handleRequest: serviceOperation=' + serviceOperation)

    try {
      const context = { request }
      const serviceResponse = await serviceOperation(this.collectRequestParams(request),context)
      Controller.sendResponse(response, serviceResponse)
    } catch (error) {
      logger.info("handleRequest:: error=" + JSON.stringify(error,null,2))

      Controller.sendError(response, error)
    }
  }
}

module.exports = Controller;