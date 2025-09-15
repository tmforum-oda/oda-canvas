'use strict';

const logger = require('../logger')
const swaggerUtils = require('../utils/swaggerUtils')

function generateResponseHeaders(context, query, totalSize, docLength) {
  const headers = []
  if(totalSize && totalSize>0) headers.push( {'X-Total-Count': totalSize})
  if(docLength && docLength>0) headers.push( {'X-Result-Count': docLength})

  const skip  = query?.options?.skip  ? parseInt(query.options.skip)  : 0
  const limit = query?.options?.limit ? parseInt(query.options.limit) : 0

  if(limit>0 || skip>0) {
    headers.push(setLinks(context,query,skip,limit,totalSize))
  }

  logger.debug("headers=" + JSON.stringify(headers,null,2))

  return headers

}


function generateLink(context,query,skip,limit,type) {
  const basePath = context.request.url.replace(/\?.*$/,"")
  const hostPath = swaggerUtils.getHostPath(context)
  const url = new URL(hostPath)
  
  logger.debug("generateLink: basePath=" + basePath + " hostPath=" + hostPath + " url=" + url)

  var linkPath = url.protocol
  if(!linkPath.endsWith(':')) linkPath = linkPath + ':'
  linkPath = linkPath + "//"
  linkPath = linkPath + url.hostname
  if(url.port) linkPath = linkPath + ":" + url.port
  if(!basePath.startsWith('/')) linkPath = linkPath + '/'
  linkPath = linkPath + basePath

  return '<' + linkPath + generateQueryString(query,skip,limit) + '>; rel="' + type + '"'
}

function setLinks(context,query,skip,limit,totalSize) {
  const links = [];
  links.push(generateLink(context,query,skip,limit,"self"));
  if(limit>0) {
    if(skip+limit<totalSize) {
      if(skip+2*limit<totalSize) {
        links.push(generateLink(context,query,skip+limit,limit,"next"));
      } else {
        links.push(generateLink(context,query,skip+limit,totalSize-skip-limit,"next"));
      }
      links.push(generateLink(context,query,totalSize-limit,limit,"last"));
    } 
    if(skip-limit>0) {
      links.push(generateLink(context,query,skip-limit,limit,"prev"));
    } else if(skip>0) {
      links.push(generateLink(context,query,0,skip,"prev"));
    }
  }
  return { Link: links.join(', ') }
}


function generateQueryString (query,offset,limit) {
  let res=[]

  logger.debug("query=" + JSON.stringify(query))

  if(query?.options?.projection) {
    let fields=Object.keys(query.options.projection)
    if(fields.length>0) {
      fields = 'fields=' + fields.join(',')
      res.push(fields)
    }
  }

  if(query?.criteria) {
    let criteria=Object.keys(query.criteria)
    if(criteria.length>0) {
      criteria = criteria.map(c => c + '=' + query.criteria[c] )
      res.push(criteria.join(','))
    }
  }

  if(query?.jsonpath) {
    res.push('filter=' + query.jsonpath)
  }

  if(offset>0) {
    res.push('offset=' + offset)
  }

  if(limit>0) {
    res.push('limit=' + limit)
  }

  return res.length==0 ? '' : '?' + res.join('&')

}


module.exports = { 
  generateResponseHeaders 
}

