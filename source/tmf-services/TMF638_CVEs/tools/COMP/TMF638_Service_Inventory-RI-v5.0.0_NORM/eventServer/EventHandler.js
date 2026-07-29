'use strict';

const logger = require('../logger')

const { clean } = require('../utils/utils');

const config = require('../config');

const Service = require('../services/Service')

const EVENTS = "TMPEVENTS";
const HUB    = "EventsSubscription";

var db;
var queue;

class EventHandler {

  static setDB(plugin) {
    db = plugin
  }

  static setQueue(plugin) {
    queue = plugin
  }

  constructor(event, plugin) {
    this.event=event

    logger.debug("EventHandler::event=" + JSON.stringify(event))

    if(plugin) {
        db = plugin.db
        queue = plugin.queue
    }

    logger.debug("EventHandler:: #2")

  }

  run (done) {

    logger.debug("EventHandler:: run")

    const query = {}
    
    db.findMany(HUB,query)
    .then(([clients,totalSize]) => {
      logger.debug("EventHandler:: resourceType=" + HUB + " returning " + totalSize + " items" )
      this.notify(clients)
    })
    .catch((error) => {
      logger.info("EventHandler:: resourceType=" + HUB + ": error=" + error);
    })
  }

  notify(clients) {

    logger.info("notify:: clients=" + JSON.stringify(clients,null,2))

    logger.info("notify:: message=" + JSON.stringify(this.event,null,2))

    if(!this.event.id && this.event.eventId) this.event.id=this.event.eventId

    const id = this.event.id

    db.create(EVENTS,this.event)
    .then(() => {
      
      logger.debug("notify:: message=" + JSON.stringify(this.event,null,2))

      const promises = clients.map(client => this.processMessage(client,this.event))

      const cleanup = function() {
        const query = { id: id}
        db.remove(EVENTS,query)
        .then(() => {})
        .catch(err => logger.info("notify clean-up error=" + err))
      };

      Promise.all(promises)
      .then(() => {
        cleanup()
      })
      .catch(err => {
        logger.info("notify: finished processing - error=" + err)
        cleanup()
      })
    })
    .catch(err => logger.info("notify error=" + err))
  }


  processMessage(client, message) {
    return new Promise(function (resolve, reject) {
      var query

      try {
        // query = JSON.parse(client.query) // WAS ._query

        query = Service.getQuery(client.query)
        query.id = message.eventId

        logger.debug("processMessage: query = " + JSON.stringify(query, null, 2))
        if (!query || !query?.criteria) {
          logger.debug("processMessage: missing query")
          return reject()
        } else {
          query.criteria.eventId = message?.eventId;
        }
      } catch (error) {
        logger.debug("processMessage: missing query (unable to parse)")
        return resolve()
      }

      db.findOne(EVENTS, query)
        .then(doc => clean(doc))
        .then(doc => {
          
          const job = { uri: client.callback, method: "POST", body: doc, json: true }
          logger.info("processMessage: job=" + JSON.stringify(job, null, 2))

          queue.produce(config.SUBSCRIPTION, job)

          return resolve()
        })
        .catch(err => {
          logger.debug("processMessage: no match res=" + err)
          logger.debug("processMessage: no match query=" + JSON.stringify(query))
          return resolve()
        })
    })
  }

}

module.exports = EventHandler




