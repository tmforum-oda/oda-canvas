/* eslint-disable no-unused-vars */
const Service = require('./Service');
const logger = require('../logger');

  /**
   * Client listener for entity ServiceAttributeValueChangeEvent
   * Example of a client listener for receiving the notification ServiceAttributeValueChangeEvent
   *
   * serviceAttributeValueChangeEvent ServiceAttributeValueChangeEvent Service attributeValueChange Event payload
   * no response value expected for this operation
   **/
  const serviceAttributeValueChangeEvent =  ( args, context /* serviceAttributeValueChangeEvent  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "NotificationListener";
        context.operationId  = "serviceAttributeValueChangeEvent";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          logger.error("serviceAttributeValueChangeEvent: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Client listener for entity ServiceCreateEvent
   * Example of a client listener for receiving the notification ServiceCreateEvent
   *
   * serviceCreateEvent ServiceCreateEvent Service create Event payload
   * no response value expected for this operation
   **/
  const serviceCreateEvent =  ( args, context /* serviceCreateEvent  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "NotificationListener";
        context.operationId  = "serviceCreateEvent";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          logger.error("serviceCreateEvent: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Client listener for entity ServiceDeleteEvent
   * Example of a client listener for receiving the notification ServiceDeleteEvent
   *
   * serviceDeleteEvent ServiceDeleteEvent Service delete Event payload
   * no response value expected for this operation
   **/
  const serviceDeleteEvent =  ( args, context /* serviceDeleteEvent  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "NotificationListener";
        context.operationId  = "serviceDeleteEvent";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          logger.error("serviceDeleteEvent: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Client listener for entity ServiceOperatingStatusChangeEvent
   * Example of a client listener for receiving the notification ServiceOperatingStatusChangeEvent
   *
   * serviceOperatingStatusChangeEvent ServiceOperatingStatusChangeEvent Service operatingStatusChange Event payload
   * no response value expected for this operation
   **/
  const serviceOperatingStatusChangeEvent =  ( args, context /* serviceOperatingStatusChangeEvent  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "NotificationListener";
        context.operationId  = "serviceOperatingStatusChangeEvent";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          logger.error("serviceOperatingStatusChangeEvent: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Client listener for entity ServiceStateChangeEvent
   * Example of a client listener for receiving the notification ServiceStateChangeEvent
   *
   * serviceStateChangeEvent ServiceStateChangeEvent Service stateChange Event payload
   * no response value expected for this operation
   **/
  const serviceStateChangeEvent =  ( args, context /* serviceStateChangeEvent  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "NotificationListener";
        context.operationId  = "serviceStateChangeEvent";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          logger.error("serviceStateChangeEvent: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    

module.exports = {
  serviceAttributeValueChangeEvent,
  serviceCreateEvent,
  serviceDeleteEvent,
  serviceOperatingStatusChangeEvent,
  serviceStateChangeEvent,
};
