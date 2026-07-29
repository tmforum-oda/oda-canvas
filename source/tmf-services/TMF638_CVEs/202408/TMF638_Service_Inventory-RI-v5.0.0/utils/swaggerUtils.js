'use strict'

const fs = require('fs')
const jsyaml = require('js-yaml')

const config = require('../config')
const logger = require('../logger')

const { TError, TErrorEnum } = require('../utils/errorUtils')

var spec
var swaggerDoc

function reloadAPI() {
  swaggerDoc=undefined
}

function getSwaggerDoc() {
	if (!swaggerDoc) {
		spec = fs.readFileSync(config.OPENAPI_YAML, 'utf8')
		let api = jsyaml.safeLoad(spec)
		swaggerDoc = expandAllOfs(api,api)

		logger.info("done:: replaceAllRefs")

	}
	return swaggerDoc
}

function getServerAndBasePath() {
	const doc = getSwaggerDoc()
	// let path = config.EXTERNAL_URL || doc?.servers?.[0]?.url || 'http://server:port/basepath'
	let path = doc?.servers?.[0]?.url || config.EXTERNAL_URL || 'http://server:port/basepath'

	if(!path.endsWith('/')) path = path + '/'

	return path

}

function getBasePath() {
	const url = new URL(getServerAndBasePath())	
	return url.pathname
}


function getTypeDefinition(type) {
	var def
	const meta = getSwaggerDoc()
	def = meta?.components?.schemas?.[type]

	logger.debug("getTypeDefinition:: type=" + type + " definition=" + JSON.stringify(def))

	return def
}

function getTypeOfProperty(type,property) {
	let typeDefinition=getTypeDefinition(type)
	const parts = property.split('.')

	logger.debug("getTypeOfProperty:: type=" + JSON.stringify(typeDefinition,null,2) + " property=" + property)

	for( const argument of parts) {
		logger.debug("getTypeOfProperty:: argument=" + argument)

		typeDefinition = typeDefinition?.properties?.[argument] || typeDefinition?.[argument]
		if(!typeDefinition) break;

	}

	logger.debug("getTypeOfProperty:: type=" + JSON.stringify(typeDefinition,null,2) )

	return typeDefinition
}

function getTypeDefinitionByRef(ref) {
	const type = ref.split('/').splice(-1)[0]
	return getTypeDefinition(type)
}

function getTypePath(type) {
	var def
	try {
		const meta = getSwaggerDoc()
		if (meta.components.schemas[type]) {
			def = "components.schemas." + type
		}
	} catch (e) {

	}
	return def
}

function getHostPath(context) {
	return config?.EXTERNAL_URL || "http://localhost"
}

function getMethod(context) {
	return context?.request?.method || 'GET'
}

function getResourceType(context) {
	return context?.classname
}

function getResponseTypeFromUrl(url) {
	const path = url.split('?')[0]

	const type = getResponseTypeByPath(path)

	logger.debug("getResponseTypeFromUrl:: url=" + url + " type=" + type)

	return type
}

function getResponseType(req) {

	logger.debug("getResponseType:: req=" + Object.keys(req.openapi._responseSchema.responses))

	var pathpattern = req?.swagger?.operationParameters?.[0]?.path?.[1]

	logger.debug("getResponseType:: pathpattern=" + pathpattern)

	return getResponseTypeByPath(pathpattern)
}

function getResponseTypeByPath(path) {
	var type
	const swaggerDoc = getSwaggerDoc()

	const paths = Object.keys(swaggerDoc.paths)
	const candidates = paths.filter(p => path.endsWith(p))

	logger.debug("getResponseTypeByPath:: candidates=" + candidates + " len=" + candidates.length)

	if (candidates.length == 1) {
		// lookup the type of the base post or get operation for the url
		//
		// "/productCatalogManagement/v2/catalog/{id}": {
		//    "get": {
		//      "responses": {
		//         "200": {
		//            "schema": {
		//                "items": {
		//                    "$ref": "#/definitions/TMF620Catalog"
		//
		// and without the items part if not returning an array

		var p = swaggerDoc.paths[candidates[0]]

		// logger.debug("getResponseType: p=" + JSON.stringify(p,null,2));

		// not all APIs have support for GET all resources
		// in these cases, we should be able to pick the correct type using the post path
		// TODO: What if not a post operation for these cases?

		// if (p?.post?.responses?.["201"]) {
		// 	p = p.post.responses["201"]
		// } else if (p?.post?.responses?.["200"]) {
		// 	p = p.post.responses["200"]
		// } else if (p?.get?.responses?.["200"]) {
		// 	p = p.get.responses["200"]
		// }

		p = p?.post?.responses?.["201"] || p?.post?.responses?.["200"] || p?.get?.responses?.["200"]

		// p = p?.content?.['application/json'] || p
		p = p?.content?.['application/json'] || p?.content?.['application/json;charset=utf-8'] || p

		type = p?.schema?.items?.$ref || p?.schema?.$ref

		// OAS 3
		// if (p?.content?.['application/json']) {
		// 	p = p.content['application/json'];
		// 	if (p.schema && p.schema.$ref) {
		// 		type = p.schema.$ref
		// 	} else if (p.schema.items.$ref) {
		// 		type = p.schema.items.$ref
		// 	}
		// }
		/* swagger 2
		if(p.schema!==undefined) {
			if(p.schema.$ref !== undefined) {
				type = p.schema.$ref
			} else if(p.schema.items.$ref !== undefined) {
				type = p.schema.items.$ref
			}
		}
		*/

		// now type should be something like  "$ref": "#/definitions/TMF620Catalog"
		// select the last part
		type = type?.split('/').slice(-1)[0] || type
		
	} else {
		logger.info("getResponseType: path not found (path=" + path + ")")
	}
	return type
}

function getPayloadSchema(req) {
	var schema
	var type
	const swaggerDoc = getSwaggerDoc()

	var pathpattern = req.swagger.operationParameters[0].path[1]

	if (swaggerDoc.paths[pathpattern]) {

		var p = swaggerDoc.paths[pathpattern]
		p = p[req.method.toLowerCase()]

		p.parameters.every(function (param) {
			if (param.in === 'body') {
				schema = param.schema;
				return false // break 
			}
			return true // continue with next
		})

		type =  schema?.items?.$ref || schema?.$ref

		// if (schema) {
		// 	if (schema.$ref !== undefined) {
		// 		type = schema.$ref;
		// 	} else if (schema.items.$ref !== undefined) {
		// 		type = schema.items.$ref;
		// 	}
		// }

		// if (type) {
		// 	// now type should be something like  "$ref": "#/definitions/TMF620Catalog"
		// 	// select the last part
		// 	type = type.split('/').slice(-1)[0];
		// 	schema = getTypeDefinition(type);

		// 	return schema;

		// }

		type = type?.split('/').slice(-1)[0]
		if(type) schema = getTypeDefinition(type)
	}

	return schema
}


function getPayload(req) {
	return new Promise(function (resolve, reject) {
		const payloadType = getPayloadType(req)
		if (payloadType) {
			if (req.swagger.params[payloadType]) {
				return resolve(req.swagger.params[payloadType].value)
			}
		}
		reject(new TError(TErrorEnum.INVALID_BODY, "Payload not found"))
	})
}

function getPayloadType(req) {
	var payloadType = null
	req.swagger.operationParameters.every(function (param) {
		if (param.schema.in === 'body') {
			payloadType = param.schema.name
			return false // break 
		}
		return true // continue with next
	})
	return payloadType
}

function getURLScheme() {
	return "http"
}

function getHost() {
	const swaggerDoc = getSwaggerDoc();
	return swaggerDoc.host
}

function hasProperty(obj, path) {
	var arr = path.split('.')
	while (arr.length && (obj = obj[arr.shift()]))
	return (obj)
}

const SERVICE_TYPE = "service_type"

function getRequestServiceType(req) {
	return req?.swagger?.params?.[SERVICE_TYPE]
}

function updateQueryServiceType(query, req, idparam) {

	// logger.debug("query: " + JSON.stringify(query,null,2));

	if (req.swagger.params[SERVICE_TYPE]) {
		query.criteria._serviceType = req.swagger.params[SERVICE_TYPE].value
		if (idparam===SERVICE_TYPE) {
			delete query.criteria.id
		}
	}
	return query
}

function updatePayloadServiceType(payload, req) {

	if (req.swagger.params[SERVICE_TYPE]) {
		payload._serviceType = req.swagger.params[SERVICE_TYPE].value
	}
	return payload
}

function cleanPayloadServiceType(payload, type, args) {

	try {
		if (payload.constructor === Array) {
			payload.forEach(v => {
				delete v._serviceType
				delete v._id
			})
		} else {
			delete payload._serviceType
			delete payload._id
		}
	} catch (e) {
		logger.error("error=" + e)
	}

	const fields = args?.fields?.split(',')

	if (fields==='none' || fields?.includes('none')) {
		const typedef = getTypeDefinition(type)
		const required = typedef?.required || []

		const keep = [...required, ...config?.DEFAULT_FILTERING_FIELDS_KEYS]

		Object.keys(payload).forEach(key => {
			if (!keep.includes(key)) {
				delete payload[key]
			}
		})
	}

	return payload
}

function getResponseCodesFromUrl(url,method) {
	var codes = []
	try {
		const meta = getSwaggerDoc()
		const paths = meta?.paths ? Object.keys(meta?.paths) : []
		const matching = paths.filter(p => url.endsWith(p))

		if(matching?.length==1) {
			const responses = meta.paths[matching[0]]?.[method]?.responses
			if(responses) codes = Object.keys(responses)
		}

	} catch (e) {
		logger.info("getResponseCodesFromUrl:: error=" + e)

	}
	return codes
}


function hasResponseCode(context,code) {
	logger.debug("hasResponseCode: context=" + Object.keys(context) + " code=" + code)
  
	const url = context?.request?.url
	const method = context?.method
  
	if(!url || !method) return false;
  
	const codes = getResponseCodesFromUrl(url,method)
	
	return codes?.includes(code) 
  }

const processedReplaceAllRefs={}
const processingReplaceAllRefs={}

function expandAllOfs(api,doc) {
	var res=doc
	if(!doc) return doc
	try {
		if(doc.allOf) {
			res = [];
			doc.allOf?.forEach(x => {
				if(x['$ref']) {
					const ref    = x['$ref']
					const entity = ref.split('/').splice(-1)[0]

					if(!processingReplaceAllRefs[entity]) {
						processingReplaceAllRefs[entity]=true

						const tmp = processedReplaceAllRefs[entity] || expandAllOfs(api, getValueByPath(api, ref))
						processedReplaceAllRefs[entity] = tmp

						res.push(expandAllOfs(api,tmp))
						processingReplaceAllRefs[entity]=false
					} else {
						logger.info("... recursive reference of " + ref)
						res.push(x)
					}
					
				} else {
					res.push(expandAllOfs(api,x))
				}
			})

			res = mergeArray(res)
			delete doc.allOf
			res = mergeObjects(doc,res)

		} 

		if (Array.isArray(res)) {		
			res = res.map(x => expandAllOfs(api,x))
		} else if(typeof res === 'object') {
			res = Object.fromEntries( Object.entries(res).map(([ key, val ]) => [ key, expandAllOfs(api,val) ]))
		} 

	} catch(error) {
		logger.info("expandAllOfs:: error=" + error)
	}
	
	return res
}

function mergeArray(array) {
	let res={}
	array.forEach(element => {mergeObjects(res,element)})
	return res
}

function mergeObjects(target,delta) {
	Object.keys(delta).forEach(key => {
		if(!target?.[key]) {
			target[key] = delta[key]
		} else if(Array.isArray(delta[key]) && Array.isArray(target[key])) {
			target[key] = target[key].concat(delta[key])
		} else if(typeof delta[key] === 'object') {
			target[key]=mergeObjects(target[key], delta[key])
		} else {
			// logger.warn("scalar value for " + key + " - using the first seen value: " + target?.[key])
		}

	})
	return target
}

function getValueByPath(api,path) {
	let res=api
	let parts = path.replace("#/","").split('/')
	parts.forEach(part => {res=res?.[part]})
	return res
}

module.exports = {
	getSwaggerDoc,
	getTypeDefinition,
	getTypeDefinitionByRef,
	getTypePath,
	getResponseType,
	getMethod,
	getResourceType,
	getResponseTypeByPath,
	getPayloadType,
	getPayloadSchema,
	getPayload,
	getURLScheme,
	getHost,

	getRequestServiceType,
	updateQueryServiceType,
	updatePayloadServiceType,
	cleanPayloadServiceType,
	getHostPath,

	getResponseTypeFromUrl,
	getResponseCodesFromUrl,
	hasResponseCode,

	getTypeOfProperty,
	getServerAndBasePath,
	getBasePath,
        reloadAPI

}
