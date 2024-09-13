'use strict'

const logger = require('../logger')

const plugin = require('../plugins/plugins')
const config = require('../config')

const ImportJob = require('./ImportJob')
const ExportJob = require('./ExportJob')

const processEvent = (event,done) => {
  logger.info("jobServer:: eventType=" + event?.eventType)

  try {    
    
    if(event?.eventType?.startsWith('ExportJobCreation')) {
      const task = new ExportJob(event.event.exportJob, plugin)
      task.run(done)
    } else if(event?.eventType?.startsWith('ImportJobCreation')) {
      const task = new ImportJob(event.event.importJob, plugin)
      task.run(done)
    } else {
      logger.debug("jobServer:: event not processed: eventType=" + event?.eventType)
    }

  } catch(e) {
    logger.error("jobServer::error=" + e)
  }
}


plugin.waitForPlugins()
.then( () => {

  logger.info("jobServer::plugins ok")

  const clientId = config.tmfid ? `${config.tmfid}-jobserver` : 'tmf-ri-jobserver'

  plugin.queue.setConsumer(clientId)
  plugin.queue.consume(config.INTERNAL_EVENT || "event", processEvent)
  
  logger.info("jobServer::listen on topic " + config.INTERNAL_EVENT + " group=" + clientId)

})
.catch( error => {
  logger.error(`jobServer:: unable to connect to all plugins: error=${error}`)
})

