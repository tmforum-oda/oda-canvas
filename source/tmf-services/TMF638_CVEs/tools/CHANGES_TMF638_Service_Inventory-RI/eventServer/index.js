'use strict'

const logger = require('../logger')

const plugin = require('../plugins/plugins')
const config = require('../config')

const EventHandler = require('./EventHandler')

const processEvent = (event,done) => {
  logger.info("eventServer:: eventType=" + event?.eventType)

  try {    

    if(event?.eventType?.startsWith('ExportJobCreation') ||
      event?.eventType?.startsWith('ImportJobCreation') ) {
        return
    }
     
    const task = new EventHandler(event, plugin)
    task.run(done)

  } catch(e) {
    logger.info("eventServer::error=" + e)
  }
}


plugin.waitForPlugins()
.then( () => {

  logger.info("eventServer::plugins ok")

  const clientId = config.tmfid ? `${config.tmfid}-eventServer` : 'tmf-ri-eventServer'

  plugin.queue.setConsumer(clientId)
  plugin.queue.consume(config.INTERNAL_EVENT || "event", processEvent)

  logger.info("eventServer::listen on topic " + config.INTERNAL_EVENT + " group=" + clientId)


})
.catch( error => {
  logger.error(`eventServer:: unable to connect to all plugins: error=${error}`)
})



