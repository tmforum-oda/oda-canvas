'use strict'

const logger = require('../logger')

const request = require('request')
const { getResponseTypeByPath, getTypeDefinition } = require('../utils/swaggerUtils')

const JSONStream = require('JSONStream')
const { Transform  } = require('stream')

const { clean } = require('../utils/utils')

const Service = require('../services/Service')

const BUFFSIZE = 10000

const zlib = require('zlib')
const archiver = require('archiver')

const Job = require('./Job')

class ExportJob extends Job {

    constructor (event, plugin) {
        super(event, 'ExportJob', plugin)
        this.uploadError = false
    }

    async run(done) {
        logger.info("export::start url=" + this.event.url)
 

        const cleanTransform = new Transform({
            objectMode: true,
            transform: (chunk, encoding, callback) => {
                const res = clean(chunk)
                callback(null, res)
            }
        })

        await this.updateJob({status: this.STATUS_RUNNING})
    
        const objectType = getResponseTypeByPath(this.event.path)
    
        logger.info("export:: objectType=" + objectType)

        if(!objectType) {
            this.updateJob({
                status: this.STATUS_FAILED,
                completionDate: new Date(),
                errorLog: (this.event.path!==undefined) ? 
                "Unable to identify resource type from path: " + this.event.path : 
                "Missing path property in job"
            })
            return
        }
    
        const url = this.event.url
        const query = Service.getQuery(this.event.query, objectType)

        logger.info("export:: query=" + JSON.stringify(query))
        logger.info("export:: url=" + url)

        const handleError = (error) => {            
            logger.debug("exportJob:: error " + new Date().toISOString() + ' ' + error)                                
    
            this.updateJob({
                status: this.STATUS_FAILED,
                completionDate: new Date(), 
                errorLog: error?.message || 'Error details not available'               
            })

            if(done) done()  
        }

        try {
              
            const updateSuccess = (records) => {
                logger.info("exportJob:: finished " + new Date().toISOString() + ' ' + records)                      
                this.updateJob({
                    status: this.STATUS_SUCCEEDED,
                    completionDate: new Date(), 
                    message: records + " records"
                })

                if(done) done()           
            }

            var count = 0

            let source = await this.db.findStream(objectType,query)
            
            const dest = request.post({url: url}) 
            let pipe
            let isZip = false
            const archive = archiver('zip')

            dest.on("response", (resp)  => {
                logger.info("exportJob:: " + new Date().toISOString() + ' resp.statusCode=' + resp.statusCode)
         
                if(resp.statusCode!=200) {
                    source.end()
                    const error = {message: `HTTP statuscode=${resp.statusCode} (expecting 200)` }
                    handleError(error)
                } 
            })
    
            const transformed = source.pipe(cleanTransform).pipe(JSONStream.stringify())
            pipe = transformed

            if(url.endsWith("gz") ) {
                const compress = zlib.createGzip()
                pipe = pipe.pipe(compress).pipe(dest)

            } else if(url.endsWith(".zip") ) {
                const filename = url.split('/').slice(-1)[0].replace('.zip','')
                archive.pipe(dest)
                archive.append(transformed, { name: filename })
            
                isZip = true

            } else {
                pipe = pipe.pipe(dest)
            }
           
            archive.on('error', function(err) {
                throw err
            })

            pipe.on("error",         error => handleError(error) ) 
            source.on("error",       error => handleError(error) ) 
            transformed.on("error",  error => handleError(error) ) 
            dest.on("error",         error => handleError(error) ) 
            dest.on("clientError",   error => handleError(error) ) 

            dest.on("end",     ()    => updateSuccess(count) )

            source.on("data", function () {
                count++;
                if(count%BUFFSIZE==1) {
                    logger.info("exportJob:: " + new Date().toISOString() + ' ' + count)
                }
            })
                 
            transformed.on("end", () =>  {
                logger.info("exportJob:: source end " + new Date().toISOString() + ' ' + count)
            
                if(isZip) {
                    archive.finalize(function(err, bytes) {
                        if (err) {
                           throw err
                        }
                        console.log(bytes + ' total bytes')
                        pipe.end() 
                    })
                } 
            })


        } catch(error) {
            logger.info("exportJob:: error " + error?.message)
            handleError(error)
        }

    }

    
}

module.exports = ExportJob
