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

            // Check if this is a complex nested array filter that's not supported by the jsonpath library
            if (isComplexNestedFilter(query)) {
                logger.info("applyJSONPath:: detected complex nested filter, using hybrid approach")
                const results = applyComplexFilter(data, query)
                return resolve(results)
            }

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
                const results = jp.query(data, query)
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

// Helper function to detect complex nested array filters
function isComplexNestedFilter(query) {
    // Look for patterns like: [?(...[?(...)])]
    // This indicates nested array filtering which is not supported by jsonpath library
    const nestedFilterPattern = /\[\?\([^)]*\[\?\([^)]*\)\][^)]*\)\]/
    return nestedFilterPattern.test(query)
}

// Helper function to apply complex filters using programmatic approach
function applyComplexFilter(data, query) {
    logger.info("applyComplexFilter:: processing query=" + query)
    
    // For now, handle the specific case of resourceCharacteristic filtering
    // Pattern: $[?(@.resourceCharacteristic[?(@.name=='functionalBlock' && @.value=='CoreCommerce')])]
    
    const resourceCharMatch = query.match(/\$\[\?\(\@\.resourceCharacteristic\[\?\(\@\.name=='([^']+)'\s*&&\s*\@\.value=='([^']+)'\)\]\)\]/)
    
    if (resourceCharMatch) {
        const [, targetName, targetValue] = resourceCharMatch
        logger.info(`applyComplexFilter:: filtering by resourceCharacteristic name='${targetName}' value='${targetValue}'`)
        
        return data.filter(resource => {
            const characteristics = resource.resourceCharacteristic || []
            return characteristics.some(char => 
                char.name === targetName && char.value === targetValue
            )
        })
    }
    
    // Handle simpler nested case: $[?(@.resourceCharacteristic[?(@.name=='functionalBlock')])]
    const simpleNestedMatch = query.match(/\$\[\?\(\@\.resourceCharacteristic\[\?\(\@\.name=='([^']+)'\)\]\)\]/)
    
    if (simpleNestedMatch) {
        const [, targetName] = simpleNestedMatch
        logger.info(`applyComplexFilter:: filtering by resourceCharacteristic name='${targetName}'`)
        
        return data.filter(resource => {
            const characteristics = resource.resourceCharacteristic || []
            return characteristics.some(char => char.name === targetName)
        })
    }
    
    // For other complex patterns, try to fall back to simple $[*] and warn
    logger.warn("applyComplexFilter:: unsupported complex filter pattern, returning all data")
    return data
}
 
module.exports = {
    applyJSONPath,
    getFieldSelection
}
