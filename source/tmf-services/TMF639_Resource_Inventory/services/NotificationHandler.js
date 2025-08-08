'use strict';

const logger = require('../logger')

const uuid = require('uuid')

const { transform, isEqual, isObject, isArray } = require('lodash')

const { getMethod, getResourceType } = require('../utils/swaggerUtils')

var config = require('../config')

const HUB = config.hub || "eventsSubscription"
const EVENTS = "TMPEVENTS"

var db;
var queue;

class NotificationHandler {

  static setDB(plugin) {
    db = plugin
  }

  static setQueue(plugin) {
    queue = plugin
  }
  
  static publish(context,doc,old) {

    const method = getMethod(context)
    const resourceType = getResourceType(context)

    const message = this.createEventMessage(resourceType, method, doc, old)

      
    logger.info("NotificationHandler:: publish "+ config.INTERNAL_EVENT + " " + message.eventType)

    queue.produce(config.INTERNAL_EVENT, message)

  }

  static createEventMessage(resourceType, operation, doc, old) {

    logger.debug("createEventMessage: resourceType=" + resourceType + " operation=" + operation)

    var eventType = resourceType 

    if(operation === "POST") {
      eventType = eventType + "Creation"
    } else if(operation === "DELETE") {
      eventType = eventType + "Remove"
    } else if(operation === "PUT" || operation === "PATCH") {
      var change = "AttributeValueChange"
      if(old) {
        const diff = this._difference(doc,old)
        logger.debug("createEventMessage: diff=" + JSON.stringify(diff))
        if(diff.state || diff.status) {
          change = "StateChange" 
        }
      }
      eventType = eventType + change
    }
    eventType = eventType + "Notification"

    var message = {
      eventId: uuid.v4(),
      eventTime: new Date(),
      eventType: eventType,
      event: {}
    }

    const entity = resourceType.replace(/^\w/, c => c.toLowerCase())
    message.event[entity] = doc

    logger.debug("createEventMessage:: message=" + JSON.stringify(message,null,2))

    return message

  }

  /**
   * Deep diff between two object, using lodash
   * @param  {Object} object Object compared
   * @param  {Object} base   Object to compare with
   * @return {Object}        Return a new object who represent the diff
   */
static _difference(object, base) {
    return transform(object, (result, value, key) => {
      if (!isEqual(value, base[key])) {
        result[key] = isObject(value) && isObject(base[key]) ? this._difference(value, base[key]) : value;
      }
    })
  }
}

module.exports = NotificationHandler




