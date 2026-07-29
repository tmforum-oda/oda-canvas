'use strict';

const logger = require('../logger')

function getHeaderValue(context, value) {
  if(!value) {
    return false
  } else {
    return context?.request?.header(value) || false
  }
}

module.exports = { 
  getHeaderValue 
}

