'use strict';

const { isObject, isArray } = require('lodash');
const logger = require('../logger');

function fixOpenApiYaml(schema) {
    if(typeof schema === 'object') {
       Object.keys(schema).forEach( key => {
           if(key.startsWith('application/json')) {
               schema['application/json'] = schema[key];
               delete schema[key];
           } else {
               fixOpenApiYaml(schema[key]);
           }
       }) 
    }
}

function clean(doc) {
    var res = undefined
    if (doc) {
        if (isArray(doc)) {
            res = []
            doc.forEach(x => res.push(clean(x)))
        } else if (isObject(doc)) {
            res = copy(doc)
            logger.debug("clean: keys=" + Object.keys(res))
            Object.keys(res).forEach(key => {
                if (key.startsWith("_")) {
                    delete res[key]
                } else {
                    res[key] = clean(res[key])
                }
            })
        } else {
            res = doc
        }
    }
    return res
}
  
function copy(doc) {
    return JSON.parse(JSON.stringify(doc))
}

module.exports = { fixOpenApiYaml, clean, copy }
