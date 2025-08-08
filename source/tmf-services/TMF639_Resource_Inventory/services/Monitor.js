'use strict'

const logger = require('../logger')

const config = require('../config')

const { getHeaderValue } = require('../utils/requestHeaders')
const { hasResponseCode, getTypeDefinition } = require('../utils/swaggerUtils')

function isAsyncBehaviour(resourceType, context) {
  let res = resourceType !== config.MONITOR && getHeaderValue(context, config?.ASYNC_HEADER)  

  if(!res) return res

  const hasMonitor=getTypeDefinition(config.MONITOR)
  if(!hasMonitor) {
    logger.info("... Monitor not included in the API - necessary for async (202) response")
  } 

  const has202=hasResponseCode(context,202)
  if(!has202) {
    logger.info("... Missing 202 response for " + resourceType + " - necessary for async response")
  }

  return hasMonitor && has202

}

async function createMonitor(context, payload, createFunction) {

    const url = config.EXTERNAL_URL + '/' + config.MONITOR_PATH

    const monitor = {
      sourceHref: payload.href,
      state: 'InProgress',
      request: { 
        method: context.method,
        body: JSON.stringify(payload),
        header: [ { name: "HEADER", value: "VALUE"} ], // for some reason one header value is required by the monitor
        to: payload.href
      }
    }

    const args = {
      body: monitor
    } 

    const createContext = {
      classname:    config.MONITOR,
      operationId: 'internalCreate',
      request:     { url: url }
    }

    return createFunction(args,createContext)

}

module.exports = {
  createMonitor,
  isAsyncBehaviour,
  hasResponseCode
}
