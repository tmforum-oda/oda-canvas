'use strict';

const logger   = require('../logger')
const jsonpath = require('../utils/jsonpath')

const config = require('../config')

const queryToMongo = require('query-to-mongo')

const {internalError, invalidQueryString, notFoundError, TError } = require('../utils/errorUtils')

const { Pool } = require('pg')
const QueryStream = require('pg-query-stream')
const JSONStream = require('JSONStream')

var _db

const host = process.env.DB_HOST || config.DB_HOST || config.db_host || 'localhost'
const port = process.env.DB_PORT || config.DB_PORT || config.db_port || '5432'
const user     = process.env.DB_USER || config.DB_USER || config.db_user || 'postgres'
const password = process.env.DB_PASSWORD || config.DB_PASSWORD || config.db_password
const database = process.env.DB_DATABASE || config.DB_DATABASE || config.db_name || 'tmf'

async function connect() {
  try {
    if(_db) {
      return _db
    } else {
      await connect_helper()
      return _db
    }
  } catch(error) {
    const message=error?.toString() || 'no error message'
    logger.error("postgresql::connect error=" + message)
    _db=undefined
 
    if(message.includes('Access denied for user')) {
      throw accessDenied
    } else if(message.includes('does not exist')) {
      await connect_and_create_db()
      return _db
    } else {
      throw internalError
    }
  }
}

async function connect_helper() {
  try {
    const connectionString = `postgresql://${user}:${password}@${host}:${port}/${database}`
      
    _db = new Pool({
        connectionString: process.env.DATABASE_URL || connectionString,
        ssl: config?.isProduction || false,
        max: 5
    })

    logger.debug("postgresql:: connect " + connectionString)

    await _db.connect()
        
  } catch(error) {
    logger.error("postgresql:: connect_helper error= " + error)
    throw error
  }

}

async function connect_and_create_db() {

  try { 
    const connectionString = `postgresql://${user}:${password}@${host}:${port}`
      
    const client = new Pool({
        connectionString: process.env.DATABASE_URL || connectionString,
        ssl: config?.isProduction || false,
        max: 2
    })

    logger.debug("postgresql:: connect_and_create_db " + connectionString)

    await client.connect()
    
    const sql = `CREATE DATABASE ${database}`

    logger.debug("postgresql::connect_and_create_db: sql=" + sql)

    await client.query(sql)

    await connect_helper()

  } catch(error) {
    logger.error("postgresql:: connect_and_create_db error= " + error)
    throw error
  }

}

async function findMany(resourceType,query) {
  logger.debug("postgresql::findMany: query=" + JSON.stringify(query))

  let sql
  try {
    const db = await connect()
   
    logger.debug("postgresql::findMany: resourceType=" + resourceType + " query=" + JSON.stringify(query))

    let conditions = getQueryConditions(query)
    let offset     = getOffset(query)
    let limit      = getLimit(query)
    let ordering   = getOrdering(query)

    sql = `SELECT count(*) FROM ${resourceType} ${conditions}`

    logger.debug("postgresql::findMany: sql=" + sql)

    const stats = await db.query(sql)
    const totalSize=getCount(stats)

    logger.debug("postgresql::findMany: totalSize=" + totalSize)

    const fieldSelection = getFieldSelection(query)
      
    sql = `SELECT ${fieldSelection} FROM ${resourceType} ${conditions} ${ordering} ${offset} ${limit}`

    logger.debug("postgresql::findMany sql: " + sql)

    const data = await db.query(sql)
    logger.debug("findMany: data=" + JSON.stringify(data,null,2))

    const rows = data.rows.map(x => x.data ? x.data : x)

    logger.debug("findMany: rows=" + JSON.stringify(rows,null,2))

    return [rows,totalSize]
   
  } catch(error) {
    logger.error("postgresql::findMany: error=" + error.toString())
    logger.error("postgresql::findMany: sql=" + sql)

    const msg=error.toString()
    if(msg.includes("does not exist")) {
      return [[],0]
    } else if(error instanceof TError) {
      throw error
    } else if(msg.includes("syntax error") && msg.includes("jsonpath input")) {
      throw invalidQueryString.setMessage("PostgreSQL jsonpath syntax expected")
    } else {
      throw internalError
    }
  }

}

async function findStream(resourceType,query) {

  let sql
  try {
    const db = await connect()
    const client = await db.connect()

    logger.debug("postgresql::findStream: resourceType=" + resourceType + " query=" + JSON.stringify(query))

    const conditions = getQueryConditions(query)
    const offset     = getOffset(query)
    const limit      = getLimit(query)
    const ordering   = getOrdering(query)
    const fieldSelection = getFieldSelection(query)
      
    sql = `SELECT ${fieldSelection} FROM ${resourceType} ${conditions} ${ordering} ${offset} ${limit}`

    logger.debug("postgresql::findStream sql: " + sql)

    const stream = await client.query(new QueryStream(sql))

    logger.debug("postgresql::findStream stream ok")
 
    return stream

    } catch(error) {
      logger.debug("findStream: error=" + error)
      throw internalError
  }

}

async function remove(resourceType,query) {
  try {
    logger.debug("remove: query=" + JSON.stringify(query))
    const db = await connect()

    const sql = "DELETE FROM " + resourceType + " WHERE data->>'id'=" + "'" + query.id + "'"
    logger.debug("remove sql: " + sql)

    await db.query(sql)

    return {}
  
  } catch(error) {
    logger.error("remove error: " + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    }  
  }

}

function getId(query) {
  var res;
  logger.debug("getId: query=" + JSON.stringify(query))
  if(query?.id) 
    res=query.id
  else if(query?.criteria && query?.criteria?.id)
    res=query.criteria.id

  logger.debug("getId: id=" + JSON.stringify(res))

  return res
}

function getProjection(query) {
  return Object.keys(query?.options?.projection || {})
}

function getFieldSelection(query) {
  let projection = getProjection(query)        

  const jsonpathFields = jsonpath.getFieldSelection(query.jsonpath)

  if(jsonpathFields) {
    projection = [...projection, ...jsonpathFields]
  }

  let selection;
  if(projection.length>0) {
    projection = [...projection, ...config.DEFAULT_FILTERING_FIELDS_KEYS]
    selection = projection.filter(p => p!='').map(p => getQueryPath(p) + ` as "${p}"`).join(", ")
  } else {
    selection = "*"
  }
  return selection;
}

function getOffset(query) {
  var res = "";
  if(query?.options?.skip) {
    res = " OFFSET " + query.options.skip
  }
  return res
}

function getLimit(query) {
  var res = "";
  if(query?.options?.limit) {
    res = " LIMIT " + query.options.limit
  }
  return res
}

function getCount(stats) {
  logger.debug("getCount: stats=" + JSON.stringify(stats))
 
  return stats?.rows?.[0]?.count || 0

}


function getQueryConditions(query) {
  logger.debug("getQueryConditions: query=" + JSON.stringify(query))
  let res=[]
  const criteria = query?.criteria || {}

  if(query.id && !criteria.id) {
    criteria.id = query.id
  }

  if(criteria) {
    let args = Object.keys(criteria)
    res.push(...args.map(arg => getQueryPath(arg) + getQueryCondition(criteria[arg])))
  }

  if(query?.jsonpath) {
    res.push( `jsonb_path_exists(data, '${query.jsonpath}')` )
  }

  let result = res.join(' AND ')

  if(result.length>0) result = ' WHERE ' + result

  logger.debug("getQueryConditions: res=" + JSON.stringify(result))

  return result
}

function getQueryPath(arg) {
  logger.debug("getQueryPath: arg=" + JSON.stringify(arg))
  // const path = 'data->' + arg.split('.').map(p => `'${p}'`).join('->')
  let path = ['data', ...arg.split('.').map(p => `'${p}'`)]
  let last = path.pop()
  path = path.join('->') + '->>' + last
  return path
}

function getQueryCondition(arg) {
  logger.debug("getQueryCondition: arg=" + JSON.stringify(arg))
  var res=''
  if(typeof arg !== 'object') {
    return "=" + quoted(arg)
  }
  const operation = Object.keys(arg)[0]
  const value = quoted(arg[operation])
  switch(operation) {
    case '$eq': 
      res = '=' + value
      break

    case '$ne': 
      res = '!=' + value
      break

    case '$gt':
      res = '>' + value
      break

    case '$gte':
      res = '>=' + value
      break

    case '$lt':
      res = '<' + value
      break

    case '$lte':
      res = '<=' + value
      break
      
    default:
      res = '=' + quoted(arg)
  }
  
  return res

}

function quoted(arg) {
  logger.debug("quoted: arg=" + arg + " typeof=" + typeof arg)
  if(typeof arg === 'string') 
    return "'" + arg + "'"
  else if(arg instanceof Date)
    return "'" + arg.toISOString() + "'"
  else 
    return "'" + arg + "'"
}

function getOrdering(query) {
  let res = ''

  const sort = query?.sorting
  if (sort) {
    res = Object.keys(sort).map(k => {
      const path = getQueryPath(k)
      const order = sort[k] > 0 ? "ASC" : "DESC"
      return `${path} ${order}`
    })
    res = res.join(', ')
    if(res!='') res = 'ORDER BY ' + res
  }

  return res
}


async function create(resourceType,payload) {
  logger.debug("postgresql::create: resourceType=" + resourceType + "len=" + (payload?.length || 1))

  logger.debug("postgresql::create: payload=" + JSON.stringify(payload,null,2))
  try {
    const db = await connect()

    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS ` + resourceType + ` (
          id SERIAL PRIMARY KEY,
          data JSONB
      )`

    await db.query(createTableSQL)
  
    if(!Array.isArray(payload)) {
      payload = [payload]
      const insertSQL = `INSERT INTO ${resourceType} (data) VALUES($1)`
      await db.query(insertSQL, payload)

    } else {
      
      const args = [...payload.keys()].map(idx => `($${idx+1})`).join(', ')
      const insertSQL = `INSERT INTO ${resourceType} (data) VALUES ${args}`

      logger.debug("postgresql::create: insertSQL=" + insertSQL)

      await db.query({text: insertSQL, values: payload})

    }

    return payload
   
  } catch(error) {
    logger.error("create: error=" + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    }    
  }
}


async function createMany(resourceType,payload) {
  try {
    return create(resourceType,payload)
  } catch(error) {
    logger.error("postgresql::createMany error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }
}


async function patch(resourceType,query,payload) {
  try {
    logger.debug("patch: query=" + JSON.stringify(query))
    logger.debug("patch: payload=" + JSON.stringify(payload))

    const current = await findOne(resourceType,query)
   
    logger.debug("patch: current=" + JSON.stringify(current))

    const patched = patchObject(current,payload)

    logger.debug("patch: patched=" + JSON.stringify(patched))

    await update(resourceType, query, patched)

    return patched
  
  } catch(error) {
    logger.debug("patch: error=" + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    }  
  }

}


async function update(resourceType,query,payload) {
  try {
    const db = await connect()
    const id = getId(query)

    logger.debug("update: query=" + JSON.stringify(query) + " id=" + id)

    var patchSQL = 'UPDATE ' + resourceType + ' SET data = ($1)'

    if(id) {
      patchSQL = patchSQL  + " WHERE data->>'id'=" + "'" + id + "'"
    }

    if(!payload.id) {
      payload.id = id
    }

    await db.query(patchSQL, [payload])
   

  } catch(error) {
    logger.debug("update: error=" + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    } 
  }

}

function patchObject(current,updates) {
  var res=current
  Object.keys(updates).forEach(key => {
    res[key] = updates[key]
  })
  return res
}

async function findOne(resourceType,query) {
  try {
    const id = getId(query)

    if(!id) throw invalidQueryString

    const fieldSelection = getFieldSelection(query)
    let sql = "SELECT " + fieldSelection + " FROM " + resourceType;

    const conditions = getQueryConditions(query)
    const offset = getOffset(query)
    const limit = getLimit(query)

    sql = sql + ' ' + conditions + ' ' + offset + ' ' + limit;

    logger.debug("findOne: sql=" + sql)

    const db = await connect()
    const data = await db.query(sql)
   
    logger.debug("findOne: data=" + JSON.stringify(data,null,2))

    if(data?.rowCount===1)
      return data?.rows[0]?.data || data?.rows[0]
    else
      throw notFoundError

  } catch(error) {
    logger.error("findOne: error=" + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    } 
  }
}

function getMongoQuery(arg) {
  var res = {};
  if(typeof arg === 'string') {
    res = queryToMongo(arg);
    const fields = res.options.fields || {};
    delete res.options.fields;
    res.options.projection = fields;
  } 
  return res;
}

function getQuery(arg) {
  var res = {};
  if(typeof arg === 'string') {
    res = queryToMongo(arg);
    const fields = res.options.fields || {};
    delete res.options.fields;
    res.options.projection = fields;
  } 
  return res;
}

const getHost = () => {
  return host
}

const getPort = () => {
  return port
}

module.exports = { 
  connect, 
  getMongoQuery, 
  findMany,
  remove,
  create,
  patch,
  update,
  findOne,
  findStream,
  getQuery,
  getHost,
  getPort,

  createMany

}

