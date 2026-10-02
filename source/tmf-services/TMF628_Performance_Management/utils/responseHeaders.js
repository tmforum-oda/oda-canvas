'use strict';

const logger = require('../logger');
const config = require('../config');

function generateResponseHeaders(totalSize, docLength, offset, limit) {
  const headers = [];
  if(totalSize && totalSize>0) headers.push({'X-Total-Count': totalSize});
  if(docLength && docLength>0) headers.push({'X-Result-Count': docLength});

  // Generate pagination Link headers if offset/limit are provided
  if(limit && limit>0 || offset && offset>0) {
    const links = generateLinks(offset || 0, limit || 0, totalSize);
    if(links.length > 0) {
      headers.push({ 'Link': links.join(', ') });
    }
  }

  logger.debug("headers=" + JSON.stringify(headers,null,2));

  return headers;
}

function generateLinks(offset, limit, totalSize) {
  const links = [];
  const basePath = config.EXTERNAL_URL + '/performanceMeasurement';
  
  // Self link
  links.push(generateLink(basePath, offset, limit, "self"));
  
  if(limit > 0) {
    // Next link
    if(offset + limit < totalSize) {
      if(offset + 2*limit < totalSize) {
        links.push(generateLink(basePath, offset + limit, limit, "next"));
      } else {
        links.push(generateLink(basePath, offset + limit, totalSize - offset - limit, "next"));
      }
      // Last link
      const lastOffset = Math.floor((totalSize - 1) / limit) * limit;
      links.push(generateLink(basePath, lastOffset, limit, "last"));
    }
    
    // Previous link
    if(offset - limit > 0) {
      links.push(generateLink(basePath, offset - limit, limit, "prev"));
    } else if(offset > 0) {
      links.push(generateLink(basePath, 0, offset, "prev"));
    }
    
    // First link
    if(offset > 0) {
      links.push(generateLink(basePath, 0, limit, "first"));
    }
  }
  
  return links;
}

function generateLink(basePath, offset, limit, rel) {
  let link = basePath + '?';
  const params = [];
  
  if(offset > 0) params.push('offset=' + offset);
  if(limit > 0) params.push('limit=' + limit);
  
  link += params.join('&');
  return '<' + link + '>; rel="' + rel + '"';
}

module.exports = { 
  generateResponseHeaders 
};
