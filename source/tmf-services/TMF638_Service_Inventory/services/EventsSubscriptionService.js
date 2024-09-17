/* eslint-disable no-unused-vars */
const Service = require('./Service');

  /**
   * Create a subscription (hub) to receive Events
   * Sets the communication endpoint to receive Events.
   *
   * hubFVO HubFVO Data containing the callback endpoint to deliver the information
   * returns Hub
   **/
  const createHub =  ( args, context /* hubFVO  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "EventsSubscription";
        context.operationId  = "createHub";
        context.method       = "post";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          console.log("createHub: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Remove a subscription (hub) to receive Events
   *
   * id String Identifier of the Resource
   * no response value expected for this operation
   **/
  const hubDelete =  ( args, context /* id  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "EventsSubscription";
        context.operationId  = "hubDelete";
        context.method       = "delete";
        try {
          /* NOT matching isRestful */
          resolve(Service.serve(args, context ));

        } catch (e) {
          console.log("hubDelete: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    

module.exports = {
  createHub,
  hubDelete,
};
