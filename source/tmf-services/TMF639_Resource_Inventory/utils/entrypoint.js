'use strict'
const logger = require('../logger');
const {getSwaggerDoc} = require('../utils/swaggerUtils')

//
// The EntryPoint is the equivalent of the home-page for the API.
//

function entrypoint(req, res) {
    const swaggerDoc = getSwaggerDoc();
  
    try {

        const basePath = swaggerDoc?.servers?.[0]?.url || swaggerDoc.basePath

        if(!basePath) throw new Error('server implementation error')

        const cleanPath = (path) => path.replace(/\/\//,'/')
        
        var linksObject = {}
        linksObject.self = {
            "href": basePath,

            "swagger-ui": cleanPath(`${basePath}/api-docs`),

            "openapi": cleanPath(`${basePath}/openapi`)

        }

        // add swagger info details to self link
        for (var infoKey in swaggerDoc.info) {
            linksObject.self[infoKey] = swaggerDoc.info[infoKey]
        }
        // go through every operation in every path to create additional links
        for (var pathKey in swaggerDoc.paths) {
            for (var methodKey in swaggerDoc.paths[pathKey]) {
                linksObject[swaggerDoc.paths[pathKey][methodKey].operationId] = {
                    "href": stripTrailingSlash(basePath) + pathKey,
                    "method" : methodKey.toUpperCase(),
                    "description" : swaggerDoc.paths[pathKey][methodKey].description
                }
            }
        }

        var responseJSON = {
            "_links": linksObject
        }
        
        res.end(JSON.stringify(responseJSON,null,2))  

    } catch(error) {
        logger.error('Return 404 error for url ' + req?.url)
        logger.error('Error=' + error?.message)

        res.statusCode=404
        res.end('Endpoint details not available')
    }
    
}

function stripTrailingSlash(str) {
    return str?.replace(/\/$/,'') || str
}

module.exports = { entrypoint }
