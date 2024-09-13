/**
 * The NotificationListenerController file is a very simple one, which does not need to be changed manually,
 * unless there's a case where business logic routes the request to an entity which is not
 * the service.
 * The heavy lifting of the Controller item is done in Request.js - that is where request
 * parameters are extracted and sent to the service, and where response is handled.
 */

const Controller = require('./Controller');
const service = require('../services/NotificationListenerService');
const serviceAttributeValueChangeEvent = async (request, response) => {
  await Controller.handleRequest(request, response, service.serviceAttributeValueChangeEvent);
};

const serviceCreateEvent = async (request, response) => {
  await Controller.handleRequest(request, response, service.serviceCreateEvent);
};

const serviceDeleteEvent = async (request, response) => {
  await Controller.handleRequest(request, response, service.serviceDeleteEvent);
};

const serviceOperatingStatusChangeEvent = async (request, response) => {
  await Controller.handleRequest(request, response, service.serviceOperatingStatusChangeEvent);
};

const serviceStateChangeEvent = async (request, response) => {
  await Controller.handleRequest(request, response, service.serviceStateChangeEvent);
};


module.exports = {
  serviceAttributeValueChangeEvent,
  serviceCreateEvent,
  serviceDeleteEvent,
  serviceOperatingStatusChangeEvent,
  serviceStateChangeEvent,
};
