'use strict';

var config = require('../config')

const default_redis_host = "localhost"

const args = process.env
const redis_host = args.redis_host || config.redis_host || default_redis_host

const kue = require('kue');
const logger = require('../logger');

const queue = kue.createQueue({
  redis: {
    host: redis_host
  }
})

const setConsumer = async (reader) => {
  // nothing to do with kue on top of redis
}

const produce = async (topic, msg) => {
  queue.create(topic, msg).priority('high').save()          
}

const consume = async (topic,process) => {

  logger.debug("kafka:: consume topic: " + topic)

  queue.on('job complete', function(id, result){
    kue.Job.get(id, (e1, job) => {
      if (!e1) {
        job.remove( (e2) => {
          if (e2) throw e2;
          logger.info('removed completed job ' + job.id)
        })
      }
    })
  })
  
  queue.process(topic, (event, done) => {
    process(event?.data, done)
  })

}

const getHost = () => {
  return redis_host
}

const getPort = () => {
  return 6379
}

module.exports = { produce, consume, setConsumer, getHost, getPort }




