'use strict';

const logger = require('../logger')

const queryToMongo = require('query-to-mongo')

const MongoClient = require('mongodb').MongoClient

const {internalError, notFoundError, TError, TErrorEnum } = require('../utils/errorUtils')

const {applyJSONPath}  = require('../utils/jsonpath')

const config = require('../config')

const DATABASE = config?.DATABASE || "tmf"

var mongodb 

const host = process.env.dbhost || config.db_host || localhost
const port = process.env.dbport || config.db_port || 27017

async function connect() {
  try {
    if(mongodb) {
      const res = await mongodb.stats()
      if(!res) {
        mongodb=undefined
        throw internalError
      }
      return(mongodb)
    } else {
      const dbprot = process.env.dbprot || config.db_prot || "mongodb"

      const mongourl = dbprot + "://" + host + ":" + port 
      const client = await MongoClient.connect(mongourl, { useNewUrlParser: true, useUnifiedTopology: true })
      mongodb = await client?.db(DATABASE)

      if(!client || !mongodb) {
        throw internalError
      }

      return(mongodb)
    }

  } catch(error) {
    logger.info("mongo::connect err=" + error)
    mongodb=undefined
    throw error
  }
}

async function findMany(resourceType,query) {    
  try {
    logger.debug("mongo::findMany resourceType=" + resourceType + " query=" + JSON.stringify(query,null,0))

    const criteria = generateCriteria(query?.criteria)
  
    const db = await connect()
    const totalSize = await db?.collection(resourceType).countDocuments(criteria, {})
  
    logger.info("mongo::findMany query=" + JSON.stringify(query,null,2))

    let doc
    if(query?.sorting) {
      const cursor = db?.collection(resourceType).find(criteria)

      if(query?.sorting)  cursor.sort(query.sorting)
      if(query?.options?.skip)  cursor.skip(query.options.skip)
      if(query?.options?.limit) cursor.limit(query.options.limit)
      if(query?.options?.projection) cursor.project(query?.options?.projection)

      doc = await cursor.toArray()

      cursor.close()

    } else {
      doc = await db?.collection(resourceType).find(criteria, query?.options).toArray()
    }

    doc = await applyJSONPath(doc,query?.jsonpath) 
  
    return([doc,totalSize])

  } catch(error) {
    logger.info("mongo::findMany error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }

}


async function findStream(resourceType,query) {
  query = query || {}
  try {

    logger.debug("mongo::findStream resourceType=" + resourceType + " query=" + JSON.stringify(query))

    const db = await connect()

    const stream =  await db?.collection(resourceType).find(query?.criteria || {}, query?.options || {}).stream()

    logger.debug("mongo::findStream resourceType=" + resourceType + " stream=" + stream)

    return stream

  } catch(e) { 
      logger.info("findStream: error=" + e)
      throw(internalError)
  }

}


async function remove(resourceType,query) {
  try {
    logger.debug("mongo::remove query=" + JSON.stringify(query))

    const db = await connect()

    const doc =  await db?.collection(resourceType).deleteOne(query)
        
    logger.debug("mongo::remove: doc=" + JSON.stringify(doc,null,0))
         
    if (doc?.deletedCount == 1) {
      return({})
    } else if(doc?.deletedCount == 0) {
      throw(notFoundError)
    } else{ 
      throw(internalError)
    }

  } catch(error) {
    logger.info("mongo::remove error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }
}

async function create(resourceType,payload) {
  try {
    logger.debug("mongo::create resourceType=" + resourceType)

    const db = await connect()

    await db?.collection(resourceType).insertOne(payload)
                 
    return(payload)

  } catch(error) {
    logger.info("mongo::create error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }
}

async function createMany(resourceType,payload) {
  try {
    logger.debug("mongo::createMany resourceType=" + resourceType)

    const db = await connect()

    await db?.collection(resourceType).insertMany(payload)
                 
    return(payload)

  } catch(error) {
    logger.info("mongo::createMany error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }
}

async function patch(resourceType,query,payload) {
  try {
    logger.debug("mongo::patch resourceType=" + resourceType + " query=" + JSON.stringify(query))

    const db = await connect()

    const old = await db?.collection(resourceType).findOne(query)
       
    if(!old) throw(notFoundError)

    const updateValue = { ...old, ...payload }

    await db?.collection(resourceType).updateOne(query, {$set: updateValue}, {upsert: false})

    return db?.collection(resourceType).findOne(query)

  } catch(error) {
    logger.info("mongo::patch error=" + error)
    if(error instanceof TError) 
      throw(error)
    else if(error.toString().contains('Resource not found')) {
      throw(notFoundError)
    } else 
      throw(internalError)  
  }

}

async function update(resourceType,query,payload) {
  try {
    logger.debug("mongo::update resourceType=" + resourceType + " query=" + JSON.stringify(query))

    const db = await connect()

    const old = await db?.collection(resourceType).findOne(query)
 
    if(!old) throw(notFoundError)

    const updateValue = { ...old, ...payload }

    const resp = await db?.collection(resourceType).replaceOne(query, updateValue)
  
    if(resp.result && resp.result.n==1) {
      return(payload)
    } else {
      throw(internalError)
    }

  } catch(error) {
    logger.info("mongo::update error=" + error)
    if(error instanceof TError) 
      throw(error)
    else
      throw(internalError)  
  }

}


async function findOne(resourceType,query) {
  try {
    logger.debug("mongo::findOne resourceType=" + resourceType + " query=" + JSON.stringify(query))

    const criteria = generateCriteria(query.criteria)

    const db = await connect()

    let doc = await db?.collection(resourceType).findOne(criteria,query.options)
 
    if(doc) {
      doc = applyJSONPath(doc,query?.jsonpath)
      return (doc)
    } else {
      throw(notFoundError)
    }

  } catch(error) {
    logger.debug("mongo::findOne error=" + error)

    if(error instanceof TError) 
      throw(error)
    else if(error.toString().includes('Not found')) {
      throw(notFoundError)
    } else
      throw(internalError)  
  }
}

function generateCriteria(criteria) {
  if(!criteria) return {}

  const res = {...criteria}
  Object.keys(res).filter(k => typeof res[k] !== 'object').forEach(k => { res[k] = { $eq: res[k]} }) 
              
  logger.debug("mongo::generateCriteria criteria=" + JSON.stringify(res))

  return res

}

const getHost = () => {
  return host
}

const getPort = () => {
  return port
}

module.exports = { 
  connect, 
  findMany,
  remove,
  create,
  patch,
  update,
  findOne,
  findStream,
  createMany,
  getHost,
  getPort
}

