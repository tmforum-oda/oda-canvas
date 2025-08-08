'use strict';

const logger = require('../logger');

var db;
var queue;

class Job {

  static setDB(plugin) {
    db = plugin
  }

  static setQueue(plugin) {
    queue = plugin
  }

  constructor(event, resourceType, plugin) {
        this.event=event
        this.resourceType=resourceType

        this.STATUS_FAILED = "Failed"
        this.STATUS_NOT_STARTED = "Not Started"
        this.STATUS_RUNNING = "Running"
        this.STATUS_SUCCEEDED = "Succeeded"

        logger.info("Job::Job() event=" + JSON.stringify(event,null,2))

        if(plugin) {
            this.db = plugin.db
            this.queue = plugin.queue
        }

    }

    processError (error) {
        logger.info("Job: processError error=" + error?.message);
        try {
            updateJob({
                status: this.STATUS_FAILED,
                errorLog: error.message
            })
        } catch(error) {
            logger.info("processError:: failed with error=" + error);
        }
    }

    async updateJob(update) {
        try {
            const query = {
                id: this.event.id
            }

            logger.debug("updateJob:: update=" + JSON.stringify(update,null,2))

            if(this.db.patch) {
               await this.db.patch(this.resourceType,query,update)
            } else {
                logger.info("db.patch not defined")
            }

        } catch(error) {
            logger.info("updateJob:: failed error=" + error)
            this.processError(error)
        }
    }

}

module.exports = Job
