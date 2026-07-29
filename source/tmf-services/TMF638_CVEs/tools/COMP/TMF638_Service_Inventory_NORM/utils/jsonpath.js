'use strict';

const jp = require('jsonpath');

const logger = require('../logger');
const { TError, TErrorEnum } = require('../utils/errorUtils');

const STRING = 'string_literal'
const UNION = 'union'
const SUBSCRIPT = 'subscript'
const DESCENDENT = "descendant"
const MEMBER = 'member'
const IDENTIFIER = 'identifier'

const DEFAULT_MANDATORY_FIELDS = ['id', 'href', '@type']

function getProjection(candidate) {
    let res = []

    if (candidate?.operation === SUBSCRIPT && candidate?.expression?.type === STRING) {
        res.push(candidate?.expression?.value)
    } else if (candidate?.operation === MEMBER && candidate?.expression?.type === IDENTIFIER) {
        res.push(candidate?.expression?.value)
    } else if (candidate?.operation === SUBSCRIPT && candidate?.expression?.type === UNION) {
        const onlyStrings = candidate?.expression?.value.every(e => e?.expression.type === STRING)
        if (onlyStrings) {
            res = candidate?.expression?.value?.map(e => e.expression?.value)
        }
    }
    return res
}

function applyJSONPath(data, query) {

    return new Promise((resolve, reject) => {   
        if(!query) {
            return resolve(data)
        }

        try {

            logger.info("applyJSONPath:: query=" + query )

            let path = jp.parse(query)
            let candidateProjection = path[path.length - 1]

            let projection = getProjection(candidateProjection)

            if (projection.length > 0) {
                projection = [...projection, ...DEFAULT_MANDATORY_FIELDS]

                path.pop()

                const revised_query = jp.stringify(path)
                const results = jp.query(data, revised_query)

                results.forEach(o => {
                    const keysToRemove = Object.keys(o).filter(k => !projection.includes(k))
                    keysToRemove.forEach(k => delete o[k])
                })

                return resolve(results)

            } else {
                const results = jp.query(cities, query)
                return resolve(results)
            }

        } catch(error) {
            logger.info("applyJSONPath:: error=" + error)
            const lexical = error.toString().toUpperCase().includes("LEXICAL")
            const parse = error.toString().toUpperCase().includes("PARSE")
            let message = "Unable to process JSONPath query"
            if(lexical || parse) {
                message = message + " - " + "jsonpath syntax error"
            }
            return reject(new TError(TErrorEnum.INVALID_QUERY_STRING_PARAMETER_VALUE, message))
        }
    })

}

function getFieldSelection(filter) {
    let res=[]
    try {
        if(filter) {
            const path = jp.parse(filter)
            const candidateProjection = path[path.length - 1]
            res=getProjection(candidateProjection)
        }
    } catch(error) {
        // ignoring any errors, just returning the empty array
    }
    return res
}
 
module.exports = {
    applyJSONPath,
    getFieldSelection
}
