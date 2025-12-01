'use strict';

const fs = require('fs')
const jsyaml = require('js-yaml')

const logger = require('../logger')

const swaggerUtils = require('../utils/swaggerUtils');

const config = require('../config.json')


const {internalError} = require('../utils/errorUtils')
const {generateSampleValue} = require('../utils/operationsUtils')

var conformanceDoc = null

function getConformanceDoc() {
  logger.debug("getConformanceDoc: config.conformance="  + config.conformance )

  if(conformanceDoc==null && config.conformance) {
    const spec = fs.readFileSync(config.conformance, 'utf8')
    conformanceDoc = jsyaml.safeLoad(spec)
  }
  return conformanceDoc
}

async function populateMandatoryAttributes(type, obj, req) {
  
  return new Promise(function(resolve, reject) {    

    try {
      const typedef = swaggerUtils.getTypeDefinition(type);

      logger.info("populateMandatoryAttributes: type=" + type )

      if(!typedef) {
        return resolve(obj)
      }

      var conformance = getConformanceDoc()

      logger.debug("populateMandatoryAttributes: type=" + type + " conformance=" + conformance )

      if(conformance?.conformance[type]) {
        conformance = conformance.conformance[type]
        const attributes = Object.keys(conformance.attributes)

        logger.debug("populateMandatoryAttributes: attributes=" + attributes )

        var mandatory = attributes
                .map(a => { return { "attribute": a, "conformance": conformance.attributes[a]} })
                .filter(a => a.conformance.condition)
                .filter(a => a.conformance.condition.startsWith('M'))

        mandatory = mandatory.filter(m => !m.attribute.includes('.'))

        // logger.debug("populateMandatoryAttributes: #1 mandatory=" + JSON.stringify(mandatory,null,2) )

        mandatory = mandatory.filter(m => !obj[m.attribute])

        logger.info("populateMandatoryAttributes: conformance=" + JSON.stringify(mandatory,null,2) )

        mandatory.forEach(m => obj[m.attribute]= generateSampleValue(type,m.attribute) )

      }

      return resolve(obj)

    } catch(e) {
      logger.error("populateMandatoryAttributes: error=" + e )

      return resolve(obj)

    }

  })

}

module.exports = { 
  populateMandatoryAttributes 
}

