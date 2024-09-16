'use strict';

const fs = require('fs');
const yaml = require('js-yaml');

const logger = require('../logger');
const config = require('../config');
const {URL} = require('url')
const {reloadAPI} = require('./swaggerUtils')

function updateAPISpecification(schema, file) {

  try {

    const schemaOld = yaml.dump(schema)

    if(config.EXTERNAL_URL) {
      schema.servers = []
      schema.servers.push({ "url": config.EXTERNAL_URL })
    }

    const componentName=process.env.COMPONENT_NAME
    if(componentName) {
      schema.servers = addComponentName(componentName,schema.servers)
    }

    console.log("schema.servers=" + JSON.stringify(schema.servers,null,2))

    fixMediaType(schema.paths)

    addDynamicQueryParameters(schema.paths)

    addJSONPathFilterParameter(schema.paths)

    addFieldsParameter(schema.paths)

    addSortingParameter(schema.paths)

    allowAdditionalPropertiesForField(schema.paths)
    
    const data = yaml.dump(schema)

    if(data != schemaOld) {
      fs.writeFileSync(file,data)
      logger.info('... saved the updated/modified API specification ' + file)

      reloadAPI()
 
    }

  } catch(e) {
    logger.error('failed to save the updated/modified API specification', e)
  }

}

function addComponentName(componentName,servers) {

  let component = componentName
  if(!component.endsWith('/')) component = component + '/'

 console.log("servers="+JSON.stringify(servers))
 console.log("component="+component)

  const addComponentNameToURL = (name,url) => {

 console.log("url="+JSON.stringify(url))

    const urlobj = new URL(url)
    if(!urlobj.pathname.startsWith(name)) urlobj.pathname = name + urlobj.pathname;
    urlobj.pathname = urlobj.pathname.replace(/\/\//,'/')

console.log("urlobj=" + urlobj.toString()) 
    return urlobj.toString()
  }

  // return servers.map(item => addComponentNameToURL(component,item.url)) 
  //return servers.map(item => {url: addComponentNameToURL(component,item.url)}) 
  return servers.map(item => { return {url: addComponentNameToURL(component,item.url)} }) 


}


function fixMediaType(schema) {
  if(schema instanceof Object) { 
    for(let key of Object.keys(schema)) {
      // logger.info("... processing: key=" + key)
      if(key === 'content') {
        fixMediaTypeHelper(schema[key])
      } else {
        fixMediaType(schema[key])
      }
    }
  } else if(schema instanceof Array) {
    for(let item of schema) {
      fixMediaType(item)
    }
  } else {
    // logger.info("... not processed: " + Object.keys(schema))
  }
}

function fixMediaTypeHelper(schema) {
  if(schema instanceof Object) {
    for(let key of Object.keys(schema)) {
      let keyparts = key.split(";")
      if(keyparts.length>1) {
        schema[keyparts[0]] = schema[key]
        delete schema[key]
      }
    }
  }
}

// - in: query
// name: _dynamic_params
// schema:
//   type: object
//   additionalProperties:
//     type: string
// style: form
// explode: true

const dynamic_params = {
        in: 'query',
        name: '_dynamic_params',
        schema: {
          type: 'object',
          additionalProperties: {
            type: 'string'
          }
        },
        style: 'form',
        explode: true
}

function addDynamicQueryParameters(paths) {  
  let modified=false
  for(let path of Object.keys(paths)) {
    const pathDef = paths[path]
    for(let operation of Object.keys(pathDef)) {
      const operationDef = pathDef[operation]
      if(operation=='get' && operationDef.parameters) {
        let hasDynamic = operationDef.parameters.filter(p => p.name && p.name === dynamic_params.name)
        if(hasDynamic.length==0) {
          logger.info("... add dynamic query parameters to " + operation + " " + path)
          operationDef.parameters.push(copy(dynamic_params))
          modified=true
        }
      }
    }
  }
  return modified
}

const jsonpath_filter_param = {
  in: 'query',
  name: 'filter',
  schema: {
    type: 'string'
  }
}

function addJSONPathFilterParameter(paths) {
  let modified=false
  for (let path of Object.keys(paths)) {
    const pathDef = paths[path]
    for (let operation of Object.keys(pathDef)) {
      const operationDef = pathDef[operation]
      if (operation == 'get' && operationDef.parameters) {
        let hasDynamic = operationDef.parameters.filter(p => p.name && p.name === jsonpath_filter_param.name)
        if (hasDynamic.length == 0) {
          logger.info("... add JSONPath filter query parameters to " + operation + " " + path)
          operationDef.parameters.push(copy(jsonpath_filter_param))
          modified=true
        }
      }
    }
  }
  return modified
}

const fields_param = {
    description: 'Comma-separated properties to be provided in response',
    in: 'query',
    name: 'fields',
    schema: {
      type: 'string'
    }
}

function addFieldsParameter(paths) {
  let modified=false
  for (let path of Object.keys(paths)) {
    const pathDef = paths[path]
    for (let operation of Object.keys(pathDef)) {
      const operationDef = pathDef[operation]
      if (operation == 'post' && !operationDef?.parameters) {
        logger.info("... add fields query parameters to " + operation + " " + path)
        operationDef.parameters = []
        operationDef.parameters.push(copy(fields_param))
        modified=true
      }
    }
  }
  return modified
}

function allowAdditionalPropertiesForField(paths) {
  for (let path of Object.keys(paths)) {
    const pathDef = paths[path]
    for (let operation of Object.keys(pathDef)) {
      const operationDef = pathDef[operation]
      const fieldsParameter = operationDef?.parameters?.filter(p => p.name==='fields') || []
      fieldsParameter.forEach(p => { p.allowReserved=true} ) 
    }
  }
}

const sorting_param = {
  description: "Comma-separated properties for sorting (prefix with '-' for descending",
  in: "query",
  name: "sort",
  schema: {
    type: "string"
  },
  allowReserved: true
}

function addSortingParameter(paths) {
  let modified=false
  for (let path of Object.keys(paths)) {
    const pathDef = paths[path]
    for (let operation of Object.keys(pathDef)) {
      const operationDef = pathDef[operation]
      if (operation==='get' && !path.endsWith('}')) {
        const hasSorting = operationDef?.parameters?.filter(p => p.name==='sort')?.length>0 || false
        if(!hasSorting) {
          logger.info("... add sort query parameters to " + operation + " " + path)
          operationDef.parameters = operationDef?.parameters || []
          operationDef.parameters.push(copy(sorting_param))
          modified=true
        }
      }
    }
  }
  return modified
} 

function copy(o) {
  return JSON.parse(JSON.stringify(o))
}

module.exports = { 
  updateAPISpecification
}
