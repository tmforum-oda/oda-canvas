'use strict'

const logger = require('../logger')

const axios = require('axios')

const { getResponseTypeByPath, getServerAndBasePath } = require('../utils/swaggerUtils')
const { processCommonAttributes } = require('../utils/operationsUtils')

const BUFFSIZE = 10000

const StreamArray = require('stream-json/streamers/StreamArray')
const zlib = require('zlib')
const unzipper = require('unzipper')

const Job = require('./Job')

class ImportJob extends Job {

  constructor (event, plugin) {
    super(event, 'ImportJob', plugin)
  }

  async run (done) {

    logger.info('importFile::event : ' + JSON.stringify(this.event, null, 2))

    logger.info("import::start url=" + this.event.url)
  
    try {

      this.updateJob({status: this.STATUS_RUNNING})

      const importType = getResponseTypeByPath(this.event.path)
  
      if (!importType) {
        const error = (this.event.path !== undefined) ?
          'Unable to identify resource type from path: ' + this.event.path :
          'Missing path property in job'
        throw new Error(error)
      }
  
      logger.info('importFile::importType=' + importType)
  
      const records = await this.importFile(importType)

      logger.info("import::records=" + records)

      if(records>0) {
        this.updateJob({
          status: this.STATUS_SUCCEEDED,
          completionDate: new Date(),
          message: 'processed ' + records + ' record(s)',
          errorLog: ''
        })

      } else {

        this.updateJob({
          completionDate: new Date(),
          message: 'processed ' + records + ' record(s)',
        })
      }
      
      if(done) done()

    } catch(error) {

      logger.error('importjob:: error=' + error)

      this.updateJob({
        status: this.STATUS_FAILED,
        errorLog: error?.message || '',
        completionDate: new Date()
      })

      if(done) done()
  
    }
  
  }

  async importFile (importType) {

    const url = this.event.url
    const path = this.event.path

    const getFile = async() => {
      try {
          const resp = await axios.get(url, {responseType: 'stream'})
          return this.performImport(url, path, importType, resp.data)
      } catch (error) {
          throw this.processError(error)
      }
    }

    return getFile()

  }

  async performImport(url, path, importType, source) {

    var pipeline = source

    const hostpath = getServerAndBasePath()
    const context = { url: `${hostpath}${path}` }

    try {

      let unzip = zlib.createUnzip()
      if (url.endsWith('gz')) {
        pipeline = pipeline.pipe(unzip)
      } else if (url.endsWith('zip')) {
        unzip = unzipper.ParseOne()
        pipeline = pipeline.pipe(unzip)
      }

      var streamArray = StreamArray.withParser()
      pipeline = pipeline.pipe(streamArray) // , {end:false})

      let processed = 0
      let inProcess = 0
      let buffer = []

      const process = async (payload, reject) => {
        try {

          if(!payload) return

          inProcess++

          payload = await processCommonAttributes(importType, payload, context)

          buffer.push(payload)
          if(buffer.length==BUFFSIZE) {
            const ready = buffer
            buffer = []
            await this.db.createMany(importType, ready)
          }

          processed++
          if(processed%BUFFSIZE==1) {
            logger.info('importJob:: importFile ' + new Date().toISOString() + " processed=" + processed)
          }

          inProcess--

        } catch(error) {
          logger.info('importJob:: process error=' + error)
          reject(error)
        }

      }

      const keepWaiting = () => { return inProcess>0 }

      const complete = async (round) => {

        round = round || 1
        let now = new Date().toISOString()
        logger.info(`waitComplete: ${now} inProcess: ${inProcess}`)
        while (keepWaiting()) {
          await new Promise(resolve => setTimeout(resolve, round * 5))
        }
        if(buffer.length>0) {
          await this.db.createMany(importType, buffer)
        }
        now = new Date().toISOString()
        logger.info(`waitComplete: ${now} done (${inProcess})`)

      }

      const self=this
      const processing = new Promise(function(resolve, reject) {

        pipeline.on('error', error    => reject(self.processError(error,source)))
        pipeline.on('end',   async () => { await complete() ; resolve(processed) } )
        pipeline.on('data',  data     =>  process(data.value,reject) )
       
        unzip.on('error',          error => reject(self.processError(error,source)) ) 

        source.on("error",         error => reject(self.processError(error)) ) 
        source.on("clientError",   error => reject(self.processError(error)) ) 
        source.on("end",           ()    => logger.debug("... source end")   ) 
  
      })

      return await processing

    } catch(error) {
      throw this.processError(error,source)
    }

  }

  processError(error, source) {
    logger.debug('importJob: processError error=' + error?.message)
    if(source) source.pause()
    return new Error(error?.message || ' ... no details available')
  }

}

module.exports = ImportJob
