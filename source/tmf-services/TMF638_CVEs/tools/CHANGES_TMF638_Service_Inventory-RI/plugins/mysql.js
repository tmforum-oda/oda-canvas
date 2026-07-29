'use strict';

const logger = require('../logger')

const queryToMongo = require('query-to-mongo')

const {internalError,  notFoundError, notImplemented, 
      accessDenied, invalidQueryString, TError } = require('../utils/errorUtils')

const config = require('../config')

const mysql = require('mysql2')

let _db

const host = process.env.DB_HOST || config.DB_HOST || 'localhost'
const port = process.env.DB_PORT || config.DB_PORT || '3306'

async function connect() {
  try {
    if(_db) {
      // await _db.connect()
      return _db
    } else {
  
      const user = process.env.DB_USER || config.DB_USER
      const password = process.env.DB_PASSWORD || config.DB_PASSWORD

      const database = process.env.DB_DATABASE || config.DB_DATABASE || 'tmf'

      const connectDetails = {
        connectionLimit : 10,
        host     : host,
        port     : port,
        user     : user,
        password : password,
        database : database
      }

      logger.info("mysql::connect:: connectDetails=" + JSON.stringify(connectDetails))

      const pool = mysql.createPool(connectDetails)
  
      _db = pool.promise();

      logger.info("mysql::connect:: _db=" + _db)

      return(_db)

    }

  } catch(error) {
    logger.info("mysql::connect error=" + error)
    _db=undefined
    if(error.toString().contains('Access denied for user')) {
      throw accessDenied
    } else {
      throw internalError
    }
  }
}


async function create(resourceType,payload) {
  try {
    const db = await connect()

    const createTableSQL = `
        CREATE TABLE IF NOT EXISTS ${resourceType} (
            id SERIAL PRIMARY KEY,
            data JSON
        );`

    await db.query(createTableSQL)
  
    const data = Array.isArray(payload) ? payload : [payload]

    const insert = data.forEach(d => JSON.stringify(d) )

    const insertSQL = 'INSERT INTO ' + resourceType + '(data) VALUES($1)'
    
    await db.query(insertSQL, insert)


    return payload

  } catch(error) {
    logger.debug("create: error=" + error)
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    }   
  }
}


async function findMany(resourceType,query) {
  let sql=''
  try {
    const db = await connect()
 
    let conditions     = getQueryConditions(query)
    let offsetAndLimit = getOffsetAndLimit(query)
    let ordering       = getOrdering(query)

    logger.debug("findMany: query=" + JSON.stringify(query))

    sql = `SELECT count(*) AS count FROM ${resourceType} ${conditions}`;

    logger.debug("findMany: sql=" + sql)

    const stats = await db.query(sql)
    const totalSize=getCount(stats)

    const fieldSelection = getFieldSelection(query)
      
    sql = `SELECT ${fieldSelection} FROM ${resourceType} ${conditions} ${offsetAndLimit} ${ordering}`

    logger.debug("findMany sql: " + sql)
    
    const resp = await db.query(sql)
    const rows = resp[0]

    const result = rows.map(x => x?.data ? x.data : x).map(x => removeNulls(x))

    logger.debug("findMany rows: " + JSON.stringify(result,null,2))

    return [result,totalSize]

  } catch(error) {
    logger.info("mysql::error: " + error)
    logger.info("mysql::sql: " + sql)

    if(error?.toString()?.contains('Access denied for user')) {
      throw accessDenied
    } else if(JSON.stringify(error).includes("doesn't exist")) {
      return [[],0]

    } else if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    } 
  }
}


function findStream(resourceType,query) {
  return new Promise((resolve, reject) => {
    connect()
    .then(db => {
      // db.collection(resourceType)
      // .find(query.criteria, query.options)
      // .then(res => resolve(res))
      // .catch(() => reject(internalError))
      db.collection(resourceType)
      .find(query.criteria, query.options, (error,client) => {
        if(client!==undefined) resolve(client)
        reject(internalError)
      })
    })
    .catch(error => { logger.debug("findStream: error=" + error); reject(internalError) })
  })
}

async function remove(resourceType,query) {
  logger.debug("remove: query=" + JSON.stringify(query))

  try {
    const id = getId(query)
    if(!id) return invalidQueryString
    
    const db = await connect()
  
    const conditions = getQueryConditions(query)
    let sql = `DELETE FROM ${resourceType} ${conditions}`

    logger.debug("remove sql: " + sql)

    await db.query(sql)
    
    return {}

  } catch(error) {
    logger.debug("remove error: " + error);
    if(error instanceof TError) {
      throw error
    } else {
      throw internalError
    }     
  }
}

function getId(query) {
  logger.debug("getId: query=" + JSON.stringify(query))
  return query?.id || query?.criteria?.id
}

function getProjection(query) {
  var res = [];
  if(query?.options?.projection) {
    res = Object.keys(query.options.projection)
  }
  return res
}

function getFieldSelection(query) {
  const projection = getProjection(query)        
  var selection;
  if(projection.length>0) 
    // JSON_EXTRACT(data, '$.id') 
    selection = projection.map(p => "JSON_EXTRACT(data, '$." + p + "') as " + '"' + p + '"').join(",")
  else
    selection = "*"
  return selection;
}

function getOffsetAndLimit(query) {
  var res = "";

  const offset = query?.options?.skip || 0
  const limit  = query?.options?.limit || 0

  if(offset>0 && limit==0) limit=1000

  if(offset>0 && limit>0) {
    res = ` LIMIT ${offset-1}, ${limit}`
  } else if(limit>0) {
    res = ` LIMIT ${limit}`
  }

  return res
}

function getCount(stats) {
  const res = stats?.[0]?.[0]?.count || 0
  return res
}

function getQueryConditions(query) {
  logger.debug("getQueryConditions: query=" + JSON.stringify(query))
  let res=[]
  const criteria = query?.criteria
  
  const id = getId(query)
  if(id) {
    res.push(`id='${id}'`)
  }

  if(criteria) {
    let args = Object.keys(criteria)
    res.push(...args.map(arg => getQueryPath(arg) + getQueryCondition(criteria[arg])))
  }

  let result = res.join('AND')

  if(result.length>0) result = ' WHERE ' + result

  return result
}

function getQueryPath(arg) {
  return " JSON_EXTRACT(data, '$." + arg + "')"
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
    return arg
}

function getOrdering(query) {
  let res = ''

  const sort = query?.sorting
  if (sort) {
    res = Object.keys(sort).map(k => {
      const order = sort[k] > 0 ? "ASC" : "DESC"
      return `JSON_EXTRACT(data, '$.${k}') ${order}`
    })
    res = res.join(', ')
    if(res!='') res = 'ORDER BY ' + res
  }

  return res
}

async function patch(resourceType,query,payload) {
  try {
    logger.debug("patch: query=" + JSON.stringify(query))
    logger.debug("patch: payload=" + JSON.stringify(payload))

    const current = await findOne(resourceType,query)
   
    const patched = patchObject(current,payload)
    logger.debug("patch: patched=" + JSON.stringify(patched))

    await update(resourceType, query, patched)

    return patched
  
  } catch(error) {
    logger.info("patch: error=" + error)
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

    let patchSQL = 'UPDATE ' + resourceType + ' SET data = CAST(? AS JSON)'

    if(id) {
      const condition = getQueryConditions(query)
      patchSQL = patchSQL  + condition
    } else {
      throw invalidQueryString
    }

    if(!payload.id) {
      payload.id = id
    }

    logger.debug("update: sql=" + patchSQL)

    await db.query(patchSQL, [JSON.stringify(payload)])
  
    return payload

  } catch(error) {
    logger.info("update: error=" + error)
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
  try{
    logger.debug("findOne")

    const id = getId(query)
    if(!id) throw invalidQueryString

    const db = await connect()
 
    const conditions     = getQueryConditions(query)
    const fieldSelection = getFieldSelection(query)
    let sql = `SELECT ${fieldSelection} FROM ${resourceType} ${conditions}`

    logger.debug("findOne sql: " + sql)

    const resp = await db.query(sql)
    const rows = resp[0]

    logger.debug("findOne: data=" + JSON.stringify(rows[0],null,2))

    let result = rows?.[0]?.[0]?.data || rows?.[0]?.data || rows?.[0]?.[0] || []

    if(result.length==0) {
      throw notFoundError
    } else { 
      const keys = Object.keys(result)
      keys.forEach(key => {
        if(result[key]==null) {
          delete result[key]
        }
      })
    }

    return result
    
  } catch(error) {
    logger.debug("findOne: error=" + error)
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

function removeNulls(arg) {
  Object.keys(arg).filter(k => arg[k]===null).forEach(k => delete arg[k])
  return arg
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

