'use strict';

const swaggerUtils = require('../utils/swaggerUtils')
const queryToMongo = require('query-to-mongo')
const logger = require('../logger')

const { processCommonAttributes, processMissingProperties, processExcludedInPost, replaceWithJavascriptTypes } = require('../utils/operationsUtils')

const { populateMandatoryAttributes } = require('../utils/conformanceUtils')

const { processAssignmentRules } = require('../utils/operations')

const { cleanPayloadServiceType, getResponseTypeFromUrl, getTypeOfProperty } = require('../utils/swaggerUtils')

const { internalError, notFoundError, missingBody } = require('../utils/errorUtils')

const { generateResponseHeaders } = require('../utils/responseHeaders')

const { createMonitor, isAsyncBehaviour, hasResponseCode } = require('./Monitor')

const config = require('../config.js');
const { getTypeDefinition } = require('../utils/swaggerUtils');

const VALID_OPERATORS = ['gt', 'gte', 'lt', 'lte', 'eq', 'ne']

var db
var notify

class Service {

  static setDB(plugin) {
    db = plugin
  }

  static setNotifier(plugin) {
    notify = plugin
  }

  static rejectResponse(error, code = 500) {
    code = error.statusCode || code
    logger.debug("Service.rejectResponse: error= " + error + " code=" + code)
    return { error, code: code }
  }

  static successResponse(payload, code = 200, headerParams = undefined) {
    logger.debug("Service.successResponse: code=" + code + " headers=" + headerParams);
    if (code == 204) payload = null
    return { payload, code, headerParams };
  }


  //
  // index 
  // 
  static async index(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId

    logger.info(`Service::index: ${operationId} ${resourceType}`)

    args = this.updateSortParameter(args,context.request.originalUrl)

    let query = this.getNewQuery(args,resourceType)

    query = this.addMandatoryFilterFields(query,resourceType)

    logger.debug("index:: resourceType=" + resourceType + " query=" + JSON.stringify(query))

    try {
      const resp = await db.findMany(resourceType, query)

      let doc = resp[0]
      const totalSize = resp[1]

      doc = cleanPayloadServiceType(doc)

      logger.debug("index:: resourceType=" + resourceType + " returning " + doc.length + " items")
      logger.debug("index:: resourceType=" + resourceType + " totalSize " + totalSize)

      const responseHeaderParams = generateResponseHeaders(context, query, totalSize, doc.length)

      let code = 200
      const limit = query?.options?.limit ? parseInt(query.options.limit) : 0
      if(limit && limit>0 && doc.length<totalSize && hasResponseCode(context,206)) code=206

      if (notify) notify.publish(context, doc)

      logger.info("responseHeaderParams=" + JSON.stringify(responseHeaderParams))

      return Service.successResponse(doc, code, responseHeaderParams)

      logger.info("index:: done=")

    } catch(error) {
      logger.info("index:: resourceType=" + resourceType + ": error=" + error)
      throw Service.rejectResponse(error)
    }
 

  }

  //
  // remove
  // 
  static async remove(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId

    logger.info(`Service::remove: ${operationId} ${resourceType}`)

    const id = this.getSingleKey(args,resourceType)

    var query = {
      id: id
    }

    try {
      const doc = await db.remove(resourceType, query)
   
      logger.debug("remove:: resourceType=" + resourceType + " id=" + query.id)

      notify.publish(context, doc)

      return Service.successResponse({}, 204)

    } catch(error) {
      logger.debug("remove:: resourceType=" + resourceType + ": error=" + error)
      throw Service.rejectResponse(error)
    }

  }

  //
  // show
  // 
  static async show(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId

    logger.info(`Service::show: ${operationId} ${resourceType}`)

    let query = this.getNewQuery(args,resourceType)

    query = this.addMandatoryFilterFields(query,resourceType)

    const id = this.getSingleKey(args,resourceType)

    query.criteria.id = id

    logger.info("show:: resourceType=" + resourceType + " query=" + JSON.stringify(query))

    try {
      let doc = await db.findOne(resourceType, query)
    
      logger.debug("show:: resourceType=" + resourceType + " doc=" + doc)

      if (doc) {
        doc = cleanPayloadServiceType(doc)
        logger.debug("show:: resourceType=" + resourceType + " id=" + query.criteria.id)

        notify.publish(context, doc)

        const responseHeader = doc?.href ? [{Location: doc.href}] : []

        return Service.successResponse(doc, 200,responseHeader)

      } else {
        throw Service.rejectResponse(notFoundError)
      }

    } catch(error) {
      logger.info("show:: resourceType=" + resourceType + ": error=" + error)

      throw Service.rejectResponse(notFoundError)
    }

  }

  //
  // create
  // 
  static async create(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId
    const url = context.request.url

    logger.info(`Service::create: ${operationId} ${resourceType}`)

    const apiType = getResponseTypeFromUrl(url) || resourceType

    let query = this.getNewQuery(args,resourceType)
    query = this.addMandatoryFilterFields(query,resourceType)

    var payload = args?.body || args

    if (!payload) {
      return missingBody
    }

    try {

      payload = await replaceWithJavascriptTypes(apiType, payload, context.request)
      payload = await processCommonAttributes(apiType, payload, context.request)
      payload = await processAssignmentRules(operationId, payload)

      payload = await processMissingProperties(apiType, payload, context.request)
      payload = await populateMandatoryAttributes(apiType, payload, context.request)

      payload = await processExcludedInPost(apiType, payload, context.request)

      await db.create(resourceType, payload)
    
      payload = cleanPayloadServiceType(payload, apiType, args)

      const responsePayload = this.generateResponsePayload(payload, query)

      let code = 201
      let headerParams = []
      if (isAsyncBehaviour(resourceType,context)) {
        const resp = await this.generateAsyncResponse(context, payload)
        
        if(resp?.length>0 && hasResponseCode(context,202)) {
          code = 202
          headerParams = [...headerParams, ...resp]
        }
  
        notify.publish(context, payload)

        if(doc?.href) headerParams.push({Location: doc.href})

        return Service.successResponse(responsePayload, code, headerParams)
      
      } else {
        notify.publish(context, payload)
        return Service.successResponse(responsePayload, code, headerParams)
      }

    } catch(error) {
      logger.debug("create:: resourceType=" + resourceType + ": error=" + error)
      throw Service.rejectResponse(error)
    }

  }

  //
  // update
  // 
  static async update(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId

    logger.info(`Service::update: ${operationId} ${resourceType}`)

    let payload = args?.payload || args?.body

    const id = this.getSingleKey(args,resourceType)

    var query = {
      id: id
    }

    payload.id = query.id

    logger.debug("update:: resourceType=" + resourceType + " id=" + id)

    try {
      await db.update(resourceType, query, payload)

      query = this.getNewQuery(args,resourceType)
      query = this.addMandatoryFilterFields(query,resourceType)
      query.criteria.id = id
  
      let doc = await db.findOne(resourceType, query)
      
      doc = cleanPayloadServiceType(doc)

      logger.debug("update: resourceType=" + resourceType + " id=" + doc.id)

      notify.publish(context, doc)

      const responseHeader = doc?.href ? [{Location: doc.href}] : []

      return Service.successResponse(doc, 200, responseHeader)
 
    } catch(error) {
      logger.debug("update:: resourceType=" + resourceType + ": error=" + error)
      throw Service.rejectResponse(error)
    }

  }

  //
  // patch
  // 
  static async patch(args, context) {

    const resourceType = context.classname
    const operationId = context.operationId

    logger.info(`Service::patch: ${operationId} ${resourceType}`)

    const payload = args?.payload || args?.body

    const id = this.getSingleKey(args,resourceType)

    var query = {
      id: id
    }

    logger.debug("patch:: resourceType=" + resourceType + " id=" + id)

    if (!payload || Object.keys(payload) == 0) {
      return Service.successResponse(payload, 204)
    }

    try {
      logger.debug("patch: resourceType=" + resourceType + " id=" + payload.id)
      let doc = await db.patch(resourceType, query, payload)

      doc = cleanPayloadServiceType(doc)

      logger.debug("patch: resourceType=" + resourceType + " id=" + payload.id)

      notify.publish(context, doc)

      const responseHeader = doc?.href ? [{Location: doc.href}] : []

      return Service.successResponse(doc, 200, responseHeader)

    } catch(error) {
      logger.debug("patch:: resourceType=" + resourceType + ": error=" + error)
      throw Service.rejectResponse(error)
    }
  }

  //
  // serve 
  // 
  static async serve(args, context) {

    try {
      logger.debug("Service::serve: context=" + Object.keys(context))
      const operation = context.method.toUpperCase()
      const operationId = context.operationId

      logger.info("Service::serve: " + operation + " " + operationId)

      switch (operation) {
        case "POST":
          logger.debug("Service::serve: POST context.operationId=" + context.operationId)
          return this.create(args, context)

        case "DELETE":
          return this.remove(args, context)

        case "GET":
          logger.debug("Service::serve: GET context.operationId=" + context.operationId)
          if (context.operationId.startsWith('list'))
            return this.index(args, context)
          else
            return this.show(args, context)

        case "PATCH":
          return this.patch(args, context)

        case "PUT":
          return this.patch(args, context)

        default:

      }

    } catch (e) {
      logger.info("Service::serve: error=" + e)
      throw Service.rejectResponse(e)
    }

    throw Service.rejectResponse(internalError)

  }

  static getSingleKey(obj,resourceType) {
    let typedef = getTypeDefinition(resourceType)
    typedef = typedef?.properties || typedef

    var res = null;
    if (obj.hasOwnProperty('id')) {
      res = obj.id
      logger.info("getSingleKey:: #1 res=" + res)

    } else if (typeof obj === 'object') {
      res = obj[Object.keys(obj)[0]];

      logger.info("getSingleKey:: #2 res=" + res + " obj=" + JSON.stringify(obj))

    }

    if(typedef?.id && typedef.id?.type=='integer') {
      res=parseInt(res)
      logger.info("getSingleKey:: #3 res=" + res + " obj=" + JSON.stringify(obj))

    }

    return res;
  }

  static getNewQuery(args,resourceType) {
    const filter = args?.filter
    if (filter) delete args.filter

    const sorting = args?.sort
    if(sorting) delete args.sort

    const queryString = this.getQueryString(args)
    let query = this.getQuery(queryString,resourceType)

    if (filter) query.jsonpath = filter
    if (sorting) query.sorting = this.getSorting(sorting)

    const system_query_limit = config.QUERY_LIMIT || 250

    if(query?.options?.limit) {
      query.options.limit = Math.min(query.options.limit, system_query_limit)
    } else {
      query.options = query.options || {}
      query.options.limit = system_query_limit
    }

    return query

  }

  static getSorting(sorting) {
    let res = sorting
    if(!res) return res

    res = {}
    sorting.split(",").forEach(field => {
      const direction=field?.[0]
      const key = field.replace("+","").replace("-","")
      res[key] = direction==='-' ? -1 : 1
    })

    return res
  }

  static getQueryString(args) {

    logger.debug("getQueryString:: args=" + Object.keys(args))

    const nonQueryParams = config?.NOT_QUERY_PARAMS || 
                ['body', '_dynamic_params', 'dynamic']

    const nonDynamic =  Object.keys(args || {})
                        .filter(p => !nonQueryParams.includes(p))
                        .filter(p => args[p])
                        .map(p => p + "=" + args[p])

    const dynamic =  Object.keys(args?.dynamic || {})
                        .filter(p => args.dynamic[p])
                        .map(p => p + "=" + args.dynamic[p])

    const queryString = [...nonDynamic, ...dynamic].join("&")

    logger.debug("getQueryString:: queryString=" + queryString)

    return queryString

  }


  static convertPostfixOperators(query) {
    const criteria = query?.criteria
    if (criteria) {
      logger.debug("convertPostfixOperators: criteria = " + JSON.stringify(criteria))
      Object.keys(criteria).forEach(key => {
        const parts = key.split('.')
        if (parts.length > 1) {
          let op = parts.pop()
          if (VALID_OPERATORS.includes(op)) {
            const newKey = parts.join('.')
            op = "$" + op
            criteria[newKey] = {}
            criteria[newKey][op] = criteria[key]
            delete criteria[key]
          } else {
            logger.debug("convertPostfixOperators:: operator " + op + " not known")
          }
        }
      })
      logger.debug("convertPostfixOperators: rewritten criteria = " + JSON.stringify(criteria))
    }
    return query
  }

  static convertSchemaTypes(query,resourceType) {
    
    if(!resourceType) return query;

    const criteria = query?.criteria
    if (criteria) {
      Object.keys(criteria).forEach(key => {

        const typeOfArg = getTypeOfProperty(resourceType,key)     
        const isDate = typeOfArg?.format === "date-time"

        logger.debug("convertSchemaTypes: typeOfArg=" + JSON.stringify(typeOfArg) + " isDate=" + isDate)

        if(isDate) {
          criteria[key] = this.convertDate(criteria[key])
          logger.debug("convertSchemaTypes: criteria = " + JSON.stringify(criteria))
        }

      })
      logger.debug("convertPostfixOperators: rewritten criteria = " + JSON.stringify(criteria))
    }
    return query
  }

  static convertDate(arg) {
    logger.debug("convertDate:: arg=" + JSON.stringify(arg) + " typeof=" + (typeof arg))
    if(arg instanceof Date) {
      return arg
    } else if(typeof arg !== 'string') {
      const key = Object.keys(arg)[0]
      const res = {}
      res[key] = new Date(arg[key])
      return res
    } else {
      return new Date(arg)
    }
  }

  static getQuery(arg, resourceType) {
    var res = {}
    if (typeof arg === 'string') {
      res = queryToMongo(arg)
      const fields = res.options.fields || {}
      delete res.options.fields
      res.options.projection = fields
    } else {
      res.criteria = {}
    }

    res = this.convertPostfixOperators(res)
    if(resourceType) {
      res = this.convertSchemaTypes(res,resourceType)
    }

    return res
  }

  static addMandatoryFilterFields(query,resourceType) {
    let projection = query?.options?.projection
    if (projection && !this._emptyObject(projection)) {
      if (this._hasNoneValue(projection)) projection = {}
      
      let required={} 
      const typedefinition = getTypeDefinition(resourceType)
      typedefinition?.required?.forEach(prop => required[prop]=1)

      query.options.projection = { ...projection, ...config.DEFAULT_FILTERING_FIELDS, ...required }
   
    }
   
    logger.debug("addMandatoryFilterFields:: query=" + JSON.stringify(query))

    return query
  }

  static _emptyObject(obj) {
    return Object.keys(obj).length === 0
  }

  static _hasNoneValue(obj) {
    return obj && Object.keys(obj).includes('none')
  }

  static _hasProjection(args) {
    let query = this.getNewQuery(args)
    logger.debug("Serve::_hasProjection:: query=" + JSON.stringify(query))
    return query?.options?.projection
  }

  static generateResponsePayload(payload, query) {
    const response_body = {...payload}
    const fields = Object.keys(query?.options?.projection || {})
    if(fields.length>0) {
      const keysToDelete = Object.keys(response_body).filter(k => !fields.includes(k))
      keysToDelete.forEach(key => delete response_body[key])
    }
    return response_body
  }

  static async generateAsyncResponse(context, payload) {

    logger.debug("generateAsyncResponse")
    const header=[]

    try {
      const response = await createMonitor(context, payload, this.create)

      if(response?.payload?.href) {
        const link = { Link: '<' + response.payload.href + '>; rel=related; title=monitor' }
        header.push(link)
      }
      
      return header

    } catch (error) {
      logger.info("generateAsyncResponse: error=" + JSON.stringify(error))
      return header
    }

  }

  //
  // The generator removes leading '-' and '+' in query parameter strings
  // Extract the sort parameter from the original url
  //
  static updateSortParameter(args,originalUrl) {

    logger.debug("updateSortParameter::originalUrl=" + originalUrl)

    const start = originalUrl?.indexOf('?') || -1
    if(start>=0) {
      const queryString = originalUrl?.substring(start)?.replace('?','') || ''
      let sort = queryString.split('&').filter(p => p.startsWith('sort'))
      sort = sort?.[0]?.split('=')?.[1]
      if(sort) args.sort=sort

      logger.debug("updateSortParameter::sort=" + sort)

    }
    return args
  }

}

module.exports = Service
