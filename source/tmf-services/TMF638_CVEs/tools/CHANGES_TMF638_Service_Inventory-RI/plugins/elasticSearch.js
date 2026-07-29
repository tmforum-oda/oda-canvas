'use strict'

const { URL } = require('url')

const config = require('../config.json')
const logger = require('../logger');

const { Client } = require('@elastic/elasticsearch')

const { internalError, notFoundError, notImplemented, invalidQueryString, TError } = require('../utils/errorUtils');

const { getId, getFieldSelection, getOffset, getLimit } = require('../utils/query')
const { getTypeDefinition, getSwaggerDoc } = require('../utils/swaggerUtils')
const { expandAPIReferences } = require('../utils/schema')

const node = process.env.ELASTIC_URL || config.ELASTIC_URL || 'http://localhost:9200'

const db = new Client({
  node: node,
  maxRetries: 5,
  requestTimeout: 60000
})

async function create(resourceType, payload) {
  try {
    const id = payload.id
    const index = resourceType.toLowerCase()

    await createIndex(resourceType, index)

    const response = await db.index({
      id: id,
      index: index,
      body: payload
    })

    if (response?.statusCode !== 201) throw internalError
    return payload

  } catch (error) {
    logger.info('elastic::create: error=' + JSON.stringify(error, null, 2))
    if (error instanceof TError)
      throw error
    else
      throw internalError
  }

}

async function patch(resourceType, query, payload) {
  try {
    const id = getId(query)
    const index = resourceType.toLowerCase()

    const response = await db.update({
      index: index,
      id: id,
      body: {
        doc: payload
      },
      "_source": getFieldSelection(query)
    })

    if (response?.statusCode >= 400) throw internalError
    return response.body

  } catch (error) {
    logger.info('elastic::patch: error=' + error)
    if (error instanceof TError)
      throw error
    else
      throw internalError
  }
}


async function update(resourceType, query, payload) {
  try {
    const id = getId(query)
    const index = resourceType.toLowerCase()

    const response = await db.index({
      id: id,
      index: index,
      body: payload,
      "_source": getFieldSelection(query)
    })

    if (response?.statusCode >= 400) throw internalError
    return response.body

  } catch (error) {
    logger.info('elastic::update: #2 error=' + JSON.stringify(error, null, 2))
    if (error instanceof TError)
      throw error
    else
      throw internalError
  }
}

async function findOne(resourceType, query) {
  try {
    const id = getId(query)
    const index = resourceType.toLowerCase()

    if (!id) throw invalidQueryString

    const response = await db.get({
      index: index,
      id: id,
      "_source": getFieldSelection(query)
    })

    if (response?.statusCode >= 400) throw internalError

    const data = response.body
    logger.debug('elastic::findOne: data=' + JSON.stringify(data, null, 2))

    if (data.found && data._id === id && data._index === index)
      return data._source
    else
      throw notFoundError

  } catch (error) {
    logger.info('elastic::findOne: error=' + error?.meta?.statusCode || error)
    if (error instanceof TError)
      throw error
    else if (error?.meta?.statusCode === 404)
      throw notFoundError
    else
      throw internalError
  }

}

async function findMany(resourceType, query) {
  try {
    const index = resourceType.toLowerCase()
    const search = {
      index: index,
      "_source": getFieldSelection(query)
    }

    const offset = getOffset(query)
    if (offset) search.from = offset

    const limit = getLimit(query) || 1000
    if (limit) search.size = limit

    const conditions = getQueryConditions(query)

    logger.debug("conditions:" + JSON.stringify(conditions, null, 2))

    if (conditions?.must || conditions?.must_not) {
      search.body = {
        "query": {
          "bool": conditions
        }
      }
    }

    if (query?.sorting) {
      let sort = await getSortingKeys(index, query.sorting)
      sort = Object.keys(query.sorting).map(k => {
        const order = query.sorting[k] > 0 ? "asc" : "desc"
        return sort[k] + ":" + order
      })
      search.sort = sort
    }

    const response = await db.search(search)

    if (response?.statusCode >= 400) throw internalError

    const data = response.body.hits
    if (data && data?.hits) {
      logger.debug('elastic::findMany: data=' + JSON.stringify(Object.keys(data), null, 2))
      const rows = data.hits.map(x => x._source || x)
      const totalSize = data.total.value

      return [rows, totalSize]

    } else {
      throw notFoundError
    }
  } catch (error) {
    logger.info('elastic::findMany: error=' + JSON.stringify(error, null, 2))
    if (error instanceof TError)
      throw error
    else
      throw internalError
  }

}

let indexConfig
async function getSortingKeys(index, sorting) {
  try {
    if(!indexConfig) indexConfig = await db.cat.indices({ format: 'json' })

    const res={}
    Object.keys(sorting).forEach(k => { res[k] = k + ".keyword" })
    return res

  } catch (error) {
    logger.info("getSortingKeys: error=" + error)
    throw error
  }
}

function findStream(resourceType, query) {
  return new Promise((resolve, reject) => {
    reject(notImplemented)
  })
}

async function remove(resourceType, query) {
  try {
    logger.debug('elastic::remove: #0 query=' + JSON.stringify(query))
    const id = getId(query)
    const index = resourceType.toLowerCase()

    if (!id) throw invalidQueryString

    const response = await db.delete({
      index: index,
      id: id
    })

    logger.debug('elastic::remove: response=' + JSON.stringify(Object.keys(response), null, 2))

    if (response?.statusCode >= 400) throw internalError

    return {}

  } catch (error) {
    logger.info('elastic::remove: error=' + JSON.stringify(error, null, 2))
    if (error instanceof TError)
      throw error
    else
      throw internalError
  }
}

function getQueryConditions(query) {
  logger.debug('elastic::getQueryConditions: query=' + JSON.stringify(query))
  const must = []
  const must_not = []

  const criteria = query?.criteria

  if (criteria) {
    const keys = Object.keys(criteria)
    keys.forEach(key => {
      const condition = getQueryCondition(key, criteria[key])

      if (condition?.must) must.push(condition.must)
      if (condition?.must_not) must_not.push(condition.must_not)

    })
  }

  const res = {}
  if (must.length > 0) res.must = must
  if (must_not.length > 0) res.must_not = must_not

  logger.debug('elastic::getQueryConditions: res=' + JSON.stringify(res, null, 2))

  return res

}

function getQueryCondition(key, arg) {
  logger.info('elastic::getQueryCondition: key=' + key + ' arg=' + JSON.stringify(arg))
  var res;

  if (isRange(arg)) {
    res = { range: {} }
    res.range[key] = getRange(arg)
    return { must: res }

  } else if (arg['$in']) {
    res = { match: {} }
    res.match[key] = {
      "query": arg['$in'].join(' '),
    }

    return { must: res }

  } else if (arg['$ne']) {
    res = { match: {} }
    res.match[key] = getValue(arg)

    return { must_not: res }

  } else if (arg['$eq']) {
    res = { match: {} }
    res.match[key] = getValue(arg)

    return { must: res }

  } else {
    res = { match: {} }
    res.match[key] = arg
    return res
  }
}

function isRange(arg) {
  const rangeOperators = ["$gt", "$gte", "$lt", "$lte"]
  var res = false;
  const keys = Object.keys(arg);
  if (keys) {
    keys.forEach(key => {
      res = res || rangeOperators.includes(key)
    })
  }
  return res
}

function getRange(arg) {

  var res = {}

  const keys = Object.keys(arg)
  keys.forEach(key => {
    const new_key = key.replace('$', '');
    res[new_key] = arg[key]
  })

  return res

}

function getValue(arg) {
  var res = arg
  const operation = Object.keys(arg)[0]
  switch (operation) {
    case '$eq':
      res = arg[operation]
      break
    case '$ne':
      res = arg[operation]
      break

    default:

  }
  return res
}


// function patchObject (current, updates) {
//   var res = current
//   Object.keys(updates).forEach(key => {
//     res[key] = updates[key]
//   })
//   return res
// }

// function getQuery (arg) {
//   var res = {}
//   if (typeof arg === 'string') {
//     res = queryToMongo(arg)
//     const fields = res.options.fields || {}
//     delete res.options.fields
//     res.options.projection = fields
//   }
//   return res
// }

async function createIndex(resourceType, index) {

  try {
    let res = await db.indices.exists({ index: index })
   
    if (res?.statusCode != 200) {
      const body = createMapping(resourceType) || {}

      res = await db.indices.create({
        index: index,
        body: body
      })

      if (res?.statusCode >= 400) throw internalError

    }

  } catch (error) {
    logger.info("createIndex:: error=" + JSON.stringify(error))
    throw error
  }

}

function createMapping(resourceType) {
  let result

  try {
    let apidoc = expandAPIReferences()

    const typeDefinition = apidoc?.[resourceType]

    const properties = typeDefinition?.properties
    if (!properties) throw internalError

    const getMappingDetails = (def, p) => {
      let mapping
      let type = def[p]?.type || 'object'
      const format = def[p]?.format

      const formatMapping = { 'date-time': 'date' }
      type = formatMapping?.[format] || type

      if (type === 'string') {
        const format = def[p]?.format
        type = def[p]?.format === 'date-time' ? 'date' : 'text'
      }

      const typeMapping = { string: 'text', integer: 'long', number: 'float', array: 'object'}
      type = typeMapping?.[type] || type

      const properties = def[p]?.items?.properties || def[p]?.properties

      if (type === 'object' && properties) {
        const propertyMapping = Object.keys(properties)
          .map(k => {
            const r = {}
            r[k] = getMappingDetails(properties, k)
            return r
          })

        mapping = { properties: Object.assign({}, ...propertyMapping) }

      } else if (type !== 'object') {
        mapping = {
          type: type,
          fields: {
            keyword: {
              type: "keyword"
            }
          }
        }
      }
      return mapping
    }

    let res = {}
    Object.keys(properties).forEach(prop => {
      const mapping = getMappingDetails(properties, prop)
      if (mapping) res[prop] = mapping
    })

    result = { mappings: {} }
    result.mappings = { properties: res }

  } catch (error) {
    logger.info("createMapping:: error" + error)
  }

  return result

}

const getHost = () => {
  const url = new URL(node)
  return url.host
}

const getPort = () => {
  const url = new URL(node)
  return url.port
}

module.exports = {
  findMany,
  remove,
  create,
  patch,
  update,
  findOne,
  findStream,
  getHost,
  getPort
}
