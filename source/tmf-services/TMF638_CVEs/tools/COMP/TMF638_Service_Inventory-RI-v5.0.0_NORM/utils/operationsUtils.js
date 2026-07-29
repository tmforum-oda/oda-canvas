'use strict';

const uuid = require('uuid')
const fs = require('fs')

const swaggerUtils = require('../utils/swaggerUtils')

const plugins = require('../plugins/plugins')

const logger = require('../logger')

const config = require('../config')

const $RefParser = require('./json-schema-ref-parser/lib/index.js')

const schemaParser = new $RefParser()

const {TError, TErrorEnum} = require('../utils/errorUtils');

function traverse(req,schema,obj,operations,key,path) {
  operations = operations || [];
  path = path || "";

  return new Promise(function(resolve, reject) {
    lookupSchema(obj,schema)
    .then(objSchema => traverse_internal(req,objSchema,obj,operations,key,path))
    .then(res => resolve(res))
    .catch(err => reject(err))
  })
}

function getPolymorphic(obj) {
  var res;
  const SCHEMALOCATION = '@schemaLocation';
  if((obj instanceof Object) && obj[SCHEMALOCATION]!==undefined) {
    res = obj[SCHEMALOCATION];
    logger.debug('isPolymorphic: @schemaLocation = ' +  res);
    return res;
  } 
  return res;
}


function combinePropertiesAllOf(obj) {
  // move everything in allOf to properties
  if(obj.allOf!==undefined) {       
      if(obj.properties===undefined) obj.properties={}
      obj.allOf.forEach(item => {
          if(item.properties!==undefined) {
              // logger.debug('move properties ...');
              Object.keys(item.properties).forEach(key => {
                  obj.properties[key] = item.properties[key];
              })
          }
      })
      delete obj.allOf;
  }
  
  if(obj.examples!==undefined) {
      delete obj.examples
  }

  Object.keys(obj).forEach(p => {
      if(obj[p] instanceof Object) {
          combinePropertiesAllOf(obj[p]);
      }
  })
}

const schemaCache = {};

function lookupSchema(obj,schema) {
  return new Promise(function(resolve, reject) {
    const polySchema = getPolymorphic(obj);
    if(polySchema===undefined) {
      return resolve(schema);
    }

    logger.debug('found polySchema: ' + polySchema);
    const schemaValidationType = config.schemaValidationType;
    logger.debug('found schemaValidationType: ' + schemaValidationType);
    
    // if schemaValidationType is not configured, we proceed with the swagger schema
    if(schemaValidationType===undefined) {
      return resolve(schema)
    }

    if(schemaValidationType.includes('USE_LOCAL_CACHE')) {
      if(schemaCache[polySchema]!==undefined) {
        return resolve(schemaCache[polySchema])
      }
    }

    var newSchema;
    if(schemaValidationType.includes('USE_LOCAL_MAPPING')) {
      const localSchemaMapping = config.localSchemaMapping;
      const localSchemaLocation = localSchemaMapping.filter(x=> x.schema===polySchema).map(x => x.file);
      logger.debug('localSchemaLocation: ' + JSON.stringify(localSchemaLocation,null,2));
      if(localSchemaLocation && localSchemaLocation.length===1) {
        newSchema = localSchemaLocation[0];
        if(config.localSchemaLocation !== undefined) {
          newSchema = config.localSchemaLocation + '/' + newSchema;
        }
      }
    }

    if(newSchema===undefined && schemaValidationType.includes('USE_REMOTE_LOOKUP')) {
      newSchema = polySchema;
    }

    // prepare for checking if file exists in case of USE_OPTIMISTIC_LOCAL
    var checkSchema = polySchema;
    if(config.localSchemaLocation !== undefined) {
      checkSchema = config.localSchemaLocation + '/' + checkSchema;
    }
    fs.stat(checkSchema, function(err, stats) { 
      if(err) {
        // checkSchema does not exist and USE_OPTIMISTIC_LOCAL is not relevant
      } else if(schemaValidationType.includes('USE_OPTIMISTIC_LOCAL')) {
        newSchema = checkSchema;
      }

      if(newSchema===undefined) {
        return resolve(schema);
      }

      schemaParser.dereference(newSchema) 
      .then(s => {
          logger.debug('found schema: ' + JSON.stringify(s,null,2));
          
          try {
            var definition = s.definitions[s.title];        
            combinePropertiesAllOf(definition);
            logger.debug(JSON.stringify(definition,null,2));
            schemaCache[polySchema] = definition;
            return resolve(definition);

          } catch(error) {
            logger.debug('## new schema processing error: ' + error);
            return resolve(schema);
          }

      })
      .catch(error => {
          logger.debug('## new schema dereference: ' + error)
          return resolve(schema);
      })
    })
  })
}

function traverse_internal(req,schema,obj,operations,key,path) {

  return new Promise(function(resolve, reject) {

    // type is only undefined if not found in the parent schema
    // allow for properties not in schema by setting config strict_schema to false
    // defalt handling set to strict
    var strict_schema = true;
    if(config.strict_schema!=undefined) {
      strict_schema=config.strict_schema;
    }
    if(strict_schema && schema===undefined) {
        const error = new TError(TErrorEnum.INVALID_BODY_FIELD, 
                            "Property: " + key + " not allowed in resource " + path);
        return reject(error);
    }

    // nothing to do if not an object (or an array)
    if(typeof obj !== "object") {
      // logger.debug("traverse: no action for primitive element: type=" + JSON.stringify(type));
      var res = {key: key, val: obj};
      return resolve(res);
    }

    // need the definition of type to proceed 
    // const typedef = swaggerUtils.getTypeDefinition(type);
    // if(typedef==undefined) {
    //   return reject(new TError(TErrorEnum.UNPROCESSABLE_ENTITY, "Unknown type: " + type,req));
    // } 

    var promises;

    var nextPath = function(p,n) { return (p==="") ? n : p + "." + n; };

    if(Array.isArray(obj)) {
      
      var subschema = schema;
      promises = Object.keys(obj).map(idx => traverse(req,subschema,obj[idx],operations,idx,nextPath(path,idx)));

    } else {
        
      promises = Object.keys(obj).map(prop => {
        
        var subschema = schema;

        if(schema.properties!==undefined) {
          subschema = schema.properties[prop];
        }
 
        if(subschema===undefined) {
          // nothing to do right now
        } else if(subschema.type!==undefined && subschema.type==="array") {
          const type = subschema.items.$ref.split('/').slice(-1)[0];
          subschema = swaggerUtils.getTypeDefinition(type);

          // logger.debug("traverse: array: type=" + type + " subschema=" + JSON.stringify(subschema,null,2));

        } else if(subschema.$ref!==undefined) {
          const type = subschema.$ref.split('/').slice(-1)[0];
          subschema = swaggerUtils.getTypeDefinition(type);

          // logger.debug("traverse: object: type=" + type + " subschema=" + JSON.stringify(subschema,null,2));

        }         

        if(strict_schema && subschema===undefined) {
          return new Promise(function(resolve, reject) {
                const error = new TError(TErrorEnum.INVALID_BODY_FIELD, 
                            "Property: " + prop + " not allowed in resource " + path);
                reject(error);
            });

        } else {
          return traverse(req,subschema,obj[prop],operations,prop,nextPath(path,prop));
        }

      })
    }

    //
    // collect and return all schema errors before performing operations (if any) on the payload
    //
    executeAllPromises(promises)
    .then(results => {
      
      if(results.errors.length>0) {
        logger.debug("traverse: #! error:" + JSON.stringify(results.errors));

        const message = results.errors.reverse().map(error => error.message).join(', #_');

        return reject(new TError(TErrorEnum.INVALID_BODY_FIELD, message));

      } else {
        var res = Array.isArray(obj) ? [] : {};
        results.results.forEach(x => res[x.key]=x.val);
        
        var todos = operations.map(func => func(res,type,typedef));

        Promise.all(todos)
        .then((x) => { 

          const res = path==="" ? obj : {key: key, val: obj};
          return resolve(res);

        })
        .catch(err => {
          logger.debug("traverse: ## error:" + JSON.stringify(err));
          return reject(err);
        })

      }

    })
    .catch(err => {
      logger.debug("traverse: #$ error:" + JSON.stringify(err));
      // const error = new TError(TErrorEnum.UNPROCESSABLE_ENTITY, err);
      return reject(err);
    })
  })
}


function addHref(obj,type,typedef) {
  
  return new Promise(function(resolve, reject) {    
    // need obj to be a proper object
    // schema must specify href
    // obj must not have href already

    var result={};
    if(Array.isArray(obj) || !(typedef.href != undefined && obj.href == undefined)) {
      logger.debug("addHref: nothing to do for " + type);
      return resolve(obj);
    }

    // href found by looking up the relevant object instance, matching ALL properties 

    const baseType = type.replace("Ref","");

    plugins.db.connect()
    .then(db => {
      db.findMany(baseType)
      .then(doc => {
        var err;
        if(doc.length!=1) {
          err = new TError(TErrorEnum.RESOURCE_NOT_FOUND, 
            "Unable to locate sub-document " + type + " " + JSON.stringify(obj));
          return reject(err);
        }
        result.href = doc[0].href;
        return resolve(result);
      })
      .catch(err => {
        err = new TError(TErrorEnum.INTERNAL_ERROR, "Internal database error");
        return reject(err);
      })
    })
    .catch( err => {
      err = new TError(TErrorEnum.INTERNAL_ERROR, "Internal database error");
      return reject(err);
    })
  })
}

async function processCommonAttributes(type, obj, req) {
  
  return new Promise(function(resolve, reject) {    

    var typedef = swaggerUtils.getTypeDefinition(type);

    const required = typedef?.required

    typedef = typedef?.properties || typedef

    if(!typedef) {
      return resolve(obj)
    }

    if(Array.isArray(obj)) {
      return resolve(obj)
    }

    if(!type) {
      return resolve(obj)
    }

    if(typedef.id && !obj.id) {
      if(typedef.id?.type === 'string')
        obj.id = uuid.v4()
      else if(typedef.id?.type == 'integer') {
        obj.id = Math.floor( Math.random() * 1000000000000 )
      } else {
        obj.id = uuid.v4()
      }
    }

    if(req?.url && typedef.href && !obj.href) {

      const self = req.url.replace(/\/$/,"") + "/" + obj.id
      if(!self.startsWith('http') && req?.headers?.host) {
        obj.href = swaggerUtils.getURLScheme() + "://" + req.headers.host + self
      } else { 
        obj.href = self
      }

    }
    
    if(typedef.creationDate && !obj.creationDate) {
      obj.creationDate = new Date()
    }

    if(typedef.lastUpdate) {
       obj.lastUpdate = new Date()
    }

    if(typedef["@schemaLocation"] && !obj["@schemaLocation"]) {
      const ref = swaggerUtils.getTypePath(type);
      if(ref) {
        const url = config.SCHEMA_URL + "#/" + ref;
        obj["@schemaLocation"] = encodeURI(url)
      }
    }

    if(typedef["@type"] && !obj["@type"]) {
      obj["@type"] = type
    }

    if(typedef["@baseType"] && !obj["@baseType"]) {
      obj["@baseType"] = type
    }
    
    return resolve(obj)

  })
}


async function processMissingProperties(type, obj, req) {
  
  return new Promise(function(resolve, reject) {    

    logger.info(`... processMissingProperties: ${type}`)

    var typedef = swaggerUtils.getTypeDefinition(type);

    // logger.debug(`... processMissingProperties: ${JSON.stringify(typedef,null,2)}`)

    const required = typedef?.required

    typedef = typedef?.properties || typedef

    if(!typedef) {
      return resolve(obj)
    }

    if(Array.isArray(obj)) {
      return resolve(obj)
    }

    if(!type) {
      return resolve(obj)
    }

    required?.forEach(prop => {
      if(!obj[prop]) {
        logger.info(`... ${type}: missing required property ${prop}`)
        const sampleValue = generateSampleValue(type,prop)
        
        if(sampleValue) {
          obj[prop] = sampleValue
          logger.info(`... ${type}: setting property ${prop} to ${printValue(obj[prop])}`)
        } else {
          logger.info(`... ${type}: unable to create value for ${prop}`)
        }

      }
    })
    
    return resolve(obj)

  })
}


async function processExcludedInPost(type, obj, req) {
  
  return new Promise(function(resolve, reject) {    

    const createType = `${type}_Create`

    logger.info(`... processExcludedInPost: ${type} ${createType}`)

    var typedefCreate = swaggerUtils.getTypeDefinition(createType);

    if(!typedefCreate) {
      logger.info(`... processExcludedInPost: ${typedefCreate} not found`)
      return resolve(obj)
    }

    var typedef = swaggerUtils.getTypeDefinition(type);

    typedef = typedef?.properties || typedef
    typedefCreate = typedefCreate?.properties || typedefCreate

    if(!typedef || !typedefCreate) {
      return resolve(obj)
    }

    const typeKeys = Object.keys(typedef)
    const typeCreateKeys = Object.keys(typedefCreate)

    const deltaKeys = typeKeys.filter(prop => !typeCreateKeys.includes(prop))

    logger.debug(`... processMissingProperties: deltaKeys=${JSON.stringify(deltaKeys,null,2)}`)

    deltaKeys?.forEach(prop => {
      if(!obj[prop]) {
        logger.debug(`... ${type}: missing delta property ${prop}`)
        const sampleValue = generateSampleValue(type,prop)
        
        if(sampleValue) {
          obj[prop] = sampleValue
          logger.info(`... ${type}: setting property ${prop} to ${printValue(obj[prop])}`)
        } else {
          logger.info(`... ${type}: unable to create value for ${prop}`)
        }

      }
    })
    
    return resolve(obj)

  })
}

function printValue(value) {
  if(value instanceof Date) {
    return value.toISOString()
  } else {
    return value
  }
}

function generateSampleValue(type,property) {
    
    logger.debug(`... generateSampleValue:: ${type}: property: ${property}`)

    const typedef = swaggerUtils.getTypeDefinition(type);    
    const typeOfProp = typedef?.properties?.[property]

    logger.debug(`... generateSampleValue:: ${type}: typeOfProp: ${typeOfProp}`)

    if(!typeOfProp) return

    try {
      return generateSampleValueForType(type, typeOfProp, `sample of ${property}`)
    } catch(error) {
      console.log("generateSampleValue:: error=" + error)
      return
    }
    
}

function generateSampleValueForType(type, typedef, candidateDefault) {
   
  if(!typedef) return undefined

  logger.debug(`... generateSampleValueForType:: typedef: ${JSON.stringify(typedef)}`)

  if(typedef.format === 'date-time') {
    const OFFSET = 10000000
    return new Date( Date.now() + randomInt(OFFSET) )
  }

  if(typedef.enum) {
    return typedef.enum[0]
  }
  
  if(typedef['$ref']) {
    const ref = typedef['$ref'].split('/').splice(-1)[0]
    logger.debug(`... generateSampleValueForType:: ref: ${ref}`)
    const typeOfRef = swaggerUtils.getTypeDefinition(ref);    
    return generateSampleValueForType(ref, typeOfRef)
  }

  if(typedef.type === 'string') {
    return candidateDefault || "samplevalue"
  }

  if(typedef.type === 'boolean') {
    return false
  }

  if(typedef.properties) {
    const res={}
    Object.keys(typedef.properties).forEach(prop => {
      const sampleValue = generateSampleValue(type,prop)
      if(sampleValue) res[prop] = sampleValue 
    })
    return res
  }

}

function randomInt(max) {
  return Math.floor(Math.random() * max) 
}

async function checkMandatoryAttributes(type, obj, req) {
  
  return new Promise(function(resolve, reject) {    

    var typedef = swaggerUtils.getTypeDefinition(type);

    logger.debug("checkMandatoryAttributes: required=" + JSON.stringify(typedef,null,2) )

    return resolve(obj)

  })
}


function setBaseProperties(req,payload) {
  return new Promise(function(resolve, reject) {
    if (payload.id == undefined) {
      payload.id = uuid.v4()
    }
    var self = req.url.replace(/\/$/,"") + "/" + payload.id;
    payload.href = swaggerUtils.getURLScheme() + "://" + req.headers.host + self;
    resolve(payload)
  })
}

//
// Support for collecting all errors from list of promises
// (inspired by https://stackoverflow.com/questions/30362733/handling-errors-in-promise-all) 
//  

function executeAllPromises(promises) {
  // Wrap all Promises in a Promise that will always "resolve"
  var resolvingPromises = promises.map(function(promise) {
    return new Promise(function(resolve) {
      var payload = new Array(2);
      promise.then(function(result) {
          payload[0] = result
        })
        .catch(function(error) {
          payload[1] = error
        })
        .then(function() {
          /* 
           * The wrapped Promise returns an array:
           * The first position in the array holds the result (if any)
           * The second position in the array holds the error (if any)
           */
          resolve(payload)
        })
    })
  })

  var errors = [];
  var results = [];

  // Execute all wrapped Promises
  return Promise.all(resolvingPromises)
    .then(function(items) {
      items.forEach(function(payload) {
        if (payload[1]) {
          errors.push(payload[1])
        } else {
          results.push(payload[0])
        }
      });

      return {
        errors: errors,
        results: results
      }

    })
}


async function replaceWithJavascriptTypes(type, obj, req) {
  return new Promise(function(resolve, reject) {    
    try {
      let typeDefinition = swaggerUtils.getTypeDefinition(type)
      typeDefinition = typeDefinition?.properties || typeDefinition
      return resolve(replaceWithNativeTypes(typeDefinition,obj))
    } catch(error) {
      logger.info("... error " + error)
      return resolve(obj)
    }

  })

}

function replaceWithNativeTypes(typeDefinition, obj) {
  if(!typeDefinition) return obj

  if(typeDefinition?.['$ref']) {
    typeDefinition = swaggerUtils.getTypeDefinitionByRef(typeDefinition['$ref'])
    typeDefinition = typeDefinition?.properties || typeDefinition
  }

  if(Array.isArray(obj)) {
    const arrayDefinitions = typeDefinition?.items || typeDefinition
    obj = obj.map(o => replaceWithNativeTypes(arrayDefinitions,o))
  } else if(typeof obj === 'object') {
    Object.keys(obj).forEach(prop => {
      const definition = typeDefinition?.[prop]
      const format = definition?.format

      if(format==='date-time') {
        logger.info(`... replace ${prop} with native Date type`)
        obj[prop] = new Date(obj[prop])
      }

      if(typeof obj[prop] === 'object') {
        obj[prop] = replaceWithNativeTypes(typeDefinition[prop],obj[prop])
      }
      
    })
  } 
  return obj
}
 
module.exports = { 
  traverse, 
  processCommonAttributes, 
  processMissingProperties,
  processExcludedInPost,
  replaceWithJavascriptTypes,
  checkMandatoryAttributes,
  setBaseProperties, 
  addHref,
  
  generateSampleValue

}

