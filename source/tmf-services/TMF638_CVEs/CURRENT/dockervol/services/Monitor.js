'use strict'

const logger = require('../logger')
const uuid = require('uuid')
const config = require('../config')

const { getHeaderValue } = require('../utils/requestHeaders')
const { hasResponseCode, getTypeDefinition } = require('../utils/swaggerUtils')

function isAsyncBehaviour(resourceType, context) {
  let res = resourceType !== config.MONITOR && getHeaderValue(context, config?.ASYNC_HEADER)  

  if(!res) return res

  const has202=hasResponseCode(context,202)
  if(!has202) {
    logger.info("... Missing 202 response for " + resourceType + " - necessary for async response")
  }

  return has202

}

async function createMonitor(context, payload, createFunction) {

    const url = config.EXTERNAL_URL + '/' + config.MONITOR_PATH
    const monitorId = uuid.v4()
    const monitor = {
      id: monitorId,
      href:  `${config.URL_PATH}:${config.URL_PORT}${context.request.url}/${config.MONITOR_PATH}/${monitorId}`,
      sourceHref: payload.href,
      state: 'InProgress',
      name: "Monitor for " + payload.name,
      type: config.MONITOR,
      request: { 
        method: context.method,
        body: payload,
        header: [ { name: "HEADER", value: "VALUE"} ], // for some reason one header value is required by the monitor
        to: payload.href
      },
      response: {
        statusCode: "202",
        body: payload,
        header: [ { name: "HEADER", value: "VALUE"} ]
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

    return monitor //createFunction(args,createContext)

}

module.exports = {
  createMonitor,
  isAsyncBehaviour,
  hasResponseCode
}
