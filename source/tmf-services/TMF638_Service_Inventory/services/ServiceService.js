/* eslint-disable no-unused-vars */
const Service = require('./Service');

  /**
   * Creates a Service
   * This operation creates a Service entity.
   *
   * serviceFVO ServiceFVO The Service to be created
   * fields String Comma-separated properties to be provided in response (optional)
   * returns Service
   **/
  const createService =  ( args, context /* serviceFVOfields  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "Service";
        context.operationId  = "createService";
        context.method       = "post";
        try {
          /* matching isRestfulCreate */
          resolve(Service.create(args, context ));

        } catch (e) {
          console.log("createService: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Deletes a Service
   * This operation deletes a Service entity.
   *
   * id String Identifier of the Resource
   * no response value expected for this operation
   **/
  const deleteService =  ( args, context /* id  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "Service";
        context.operationId  = "deleteService";
        context.method       = "delete";
        try {
          /* matching isRestfulDestroy */
          resolve(Service.remove(args, context ));

        } catch (e) {
          console.log("deleteService: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * List or find Service objects
   * List or find Service objects
   *
   * fields String Comma-separated properties to be provided in response (optional)
   * offset Integer Requested index for start of resources to be provided in response (optional)
   * limit Integer Requested number of resources to be provided in response (optional)
   * returns List
   **/
  const listService =  ( args, context /* fieldsoffsetlimit  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "Service";
        context.operationId  = "listService";
        context.method       = "get";
        try {
          /* matching isRestfulIndex */
          resolve(Service.index(args, context ));

        } catch (e) {
          console.log("listService: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Updates partially a Service
   * This operation updates partially a Service entity.
   *
   * id String Identifier of the Resource
   * serviceMVO ServiceMVO The Service to be patched
   * fields String Comma-separated properties to be provided in response (optional)
   * returns Service
   **/
  const patchService =  ( args, context /* idserviceMVOfields  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "Service";
        context.operationId  = "patchService";
        context.method       = "patch";
        try {
          /* matching isRestfulUpdate */
          resolve(Service.update(args, context ));

        } catch (e) {
          console.log("patchService: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    
  /**
   * Retrieves a Service by ID
   * This operation retrieves a Service entity. Attribute selection enabled for all first level attributes.
   *
   * id String Identifier of the Resource
   * fields String Comma-separated properties to be provided in response (optional)
   * returns Service
   **/
  const retrieveService =  ( args, context /* idfields  */) =>
    new Promise(
      async (resolve) => {
        context.classname    = "Service";
        context.operationId  = "retrieveService";
        context.method       = "get";
        try {
          /* matching isRestfulShow */
          resolve(Service.show(args, context ));

        } catch (e) {
          console.log("retrieveService: error=" + e);
          resolve(Service.rejectResponse(
            e.message || 'Invalid input',
            e.status || 405,
          ));
        }
      },
    )
    

module.exports = {
  createService,
  deleteService,
  listService,
  patchService,
  retrieveService,
};
