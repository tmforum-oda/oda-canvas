'use strict';

const {validationRules, validationRulesType2} = require('../utils/rules');
const {TError, TErrorEnum} = require('../utils/errorUtils');

const {getPayloadType} = require('../utils/swaggerUtils');

//
// Rule validation
// 

// Example rules

  // [{ $: { $eitherOf: ["id", "href", "state", "orderDate", "completionDate", 
  //                     "expectedCompletionDate", "startDate"]}},
  // { $: {$eitherOf: ["orderItem"]}},
  // { "orderItem":  {$notEmpty: true}},
  // { "orderItem.state": {$presentIf: "action"}},
  // { "orderItem.appointment": {$eitherOf: ["id", "href"]}},
  // { "orderItem.orderItemRelationship": {$eitherOf: ["type", "id"]}},
  // { "orderItem": {$eitherOf: ["action", "id", "service"]}},
  // { "orderItem.service.serviceSpecification": {$eitherOf: ["id", "href"]}},  
  // { "orderItem.service.serviceRelationship": {$eitherOf: ["type", "service"] }},
  // { "orderItem.service.serviceCharacteristic": {$eitherOf: ["name", "valueType", "value"]}},
  // { "orderItem.service.place": {$eitherOf: ["id", "href"]}},
  // { "orderItem.service.place": {$present: ["role"]}},
  // { "orderItem.action": {$notEqual: "add", $eitherOf: ["service.id", "service.href"]}},
  // { "orderRelationship": {$eitherOf: ["id", "href"]}},
  // { "relatedParty": {$eitherOf: ["id", "href"]}},
  // { "note": {$eitherOf: ["author", "text"]}}


function validateRequest(req, operation, doc) {
  return new Promise(function(resolve, reject) {

    // first try the Type2 rules
    var payloadType = getPayloadType(req);
    if(payloadType!==null) {
      
      if(payloadType.startsWith("TMF")) {
        payloadType = payloadType.substring(6);
      }

      console.log(operation + ' :: validate request :: payloadType=' + payloadType);

      const op = req.method.toUpperCase();  

      if(validationRulesType2[payloadType]!==undefined) {
         const rule = validationRulesType2[payloadType][op]
         if(rule) {
            console.log(operation + ' :: validate request :: validationRulesType2 found');

            const error = processRules(rule,doc);
            if(error.length>0) {
              var errString = error.join("\n").replace(/"/g, "");
              return reject(new TError(TErrorEnum.INVALID_BODY,errString))
            } else {
              return resolve(doc);
            }
          } else {
            console.log(operation + ' :: validationRulesType2 does not include ' + op);
            // flow through to 'old' ruleset
        }
      } else {
        console.log(operation + ' :: validationRulesType2 does not include ' + payloadType);
        // flow through to 'old' ruleset
      }
    }

    const rule = validationRules[operation];
    if(rule) {
      console.log(operation + ' :: validate request');

      const error = processRules(rule,doc);
      if(error.length>0) {
        errString = error.join("\n").replace(/"/g, "");
        return reject(new TError(TErrorEnum.INVALID_BODY,errString))
      } else {
        console.log("validateRequest: rule not found for operation: " + operation);
        return resolve(doc)
      }
    }
    resolve(doc)
  })
}

function processRules(rules,obj) {
  var error = [];
  if(Array.isArray(rules)) {
    rules.forEach(rule => {
      const path = Object.keys(rule)[0];
      const err = processRule(rule,obj,path);
      error = error.concat(err); 
    })
  }
  return error
}

function processRule(rule,obj,path,lastLabel) {
  var error = []; 
  lastLabel = lastLabel || "";
  //
  // If obj is array with content, we check the rule for elements
  //
  if(Array.isArray(obj) && obj.length>0) {
    obj.forEach(item => {
      const err = processRule(rule,item,path,lastLabel);
      error = error.concat(err);
    });
    return error
  }

  var label = Object.keys(rule)[0];
  var parts = split2s(label,".");
  var criteria = rule[label];

  // if not a keyword (starting with $ and we have an array of criteria for the item/label
  if(label.substring(0,1)==='$' && Array.isArray(criteria) && criteria.length>0) {
    criteria.forEach(item => {
      // console.log("list of criteria:" + JSON.stringify(item));
      const err = processRule({$: item},obj,path,lastLabel);
      error = error.concat(err);
    });
    return error
  }

  if(label === '$') {
    const criteriaType=Object.keys(criteria)[0];
    switch(criteriaType) {
      case "$notEqual":
        return checkNotEqual(criteria,obj,path,lastLabel);
      case "$equal":
        return checkEqual(criteria,obj,path,lastLabel);
      case "$present":
        return checkPresent(criteria,obj,path,lastLabel);
      case "$eitherOf":
        return checkEitherOf(criteria,obj,path,lastLabel);
      case "$notEmpty":
        return checkNotEmpty(criteria,obj,path,lastLabel);
      case "$presentIf":
        return checkPresentIf(criteria,obj,path,lastLabel);
      case "$and":
        return checkAndRule(criteria,obj,path,lastLabel);
      case "$in":
        return checkInRule(criteria,obj,path,lastLabel);
      case "$noneOf":
        return checkNoneOf(criteria,obj,path,lastLabel);
      default:
        console.log("### unprocessed operation: " + criteriaType);
        return error;
      }
  } else if (obj.hasOwnProperty(parts[0])) {
    if(parts.length==1) {
      // a rule like {"orderItem": {$eitherOf: [...]}}
      // rewrite to "$" rule type as we process the embedded object
      var nextObj = (typeof obj[parts[0]] == 'object') ? obj[parts[0]] : obj;
      return processRule({$: criteria}, nextObj, path, parts[0]); // obj[parts[0]], path, parts[0]);
    } else {
      // a rule like {"orderItem.appointment": {...}}
      // rewrite the rule, i.e. removing the first part in the path

      var subrule = {};
      subrule[parts[1]] = criteria; 
      return processRule(subrule, obj[parts[0]], path, parts[0]);
    }
  }
  return error
}

function checkNotEmpty(criteria,obj,path,lastLabel) {
  var error = [];
  // console.log("checkNotEmpty: " + JSON.stringify(criteria));
  if(criteria.$notEmpty) {
    if(Array.isArray(obj) && obj.length==0) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res);
    }
  }
  return error
}

function checkEitherOf(criteria,obj,path,lastLabel) {
  // Example: {$eitherOf: ["action", "id", "service"]}}
  var error = [];
  // console.log("checkEitherOf: " + JSON.stringify(criteria));
  // console.log("          obj: " + JSON.stringify(obj));
  // console.log("         path: " + path);
  // console.log("    lastLabel: " + lastLabel);
  if(criteria.$eitherOf) {
    var failure=true;
    criteria.$eitherOf.forEach(item => {
      if(hasProperty(obj,item)) {
      // if(obj.hasOwnProperty(item)) {
        failure=false;
      }
    });
    if(failure) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res);
    } 
  }
  return error
}

function checkNoneOf(criteria,obj,path,lastLabel) {
  // Example: {$noneOf: ["action", "id", "service"]}}
  var error = [];
  if(criteria.$noneOf) {
    var failure=false;
    criteria.$noneOf.forEach(item => {
      failure = failure || hasProperty(obj,item);
    });
    if(failure) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res);
    }
  }
  return error
}

function checkInRule(criteria,obj,path,lastLabel) {
  // Example: {$in: ["action", "id", "service"]}}
  var error = [];
  // console.log("checkInRule: " + JSON.stringify(criteria));
  // console.log("        obj: " + JSON.stringify(obj));
  // console.log("       path: " + path);
  // console.log("  lastLabel: " + lastLabel);
  if(criteria.$in) {
    var failure=true;
    criteria.$in.forEach(item => {
      failure = failure & (obj[lastLabel] !== item)
    });
    if(failure) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res)
    } 
  }
  return error
}

function checkPresent(criteria,obj,path,lastLabel) {
  var error = [];
  if(criteria.$present) {
    var failure=false;
    criteria.$present.forEach(item => {
      if(!hasProperty(obj,item)) { 
        failure=true;
      }
    });
    if(failure) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res);
    }
  }
  return error
}

function checkPresentIf(criteria,obj,path,lastLabel) {
  // example: { "orderItem.state": {$presentIf: "action"}}
  var error = [];
  if(criteria.$presentIf) {
    if(! hasProperty(obj,criteria.$presentIf)) { // obj.hasOwnProperty(criteria.$presentIf)) {
      const res = path + ":" + JSON.stringify(criteria);
      error.push(res);
    }
  }
  return error
}

function checkNotEqual(criteria,obj,path,lastLabel) {
  // example: { "orderItem.action": {$notEqual: "add", $eitherOf: ["service.id", "service.href"]}}
  //    orderItem -> obj
  //    criteria -> {$notEqual: "add", $eitherOf: ["service.id", "service.href"]}
  //    lastLabel -> action
  var error = [];
  if(criteria.$notEqual && (obj[lastLabel] !== criteria.$notEqual)) {
    var subrule = cloneObject(criteria);
    delete subrule.$notEqual;
    const err = processRule({$: subrule},obj,path,lastLabel);
    if(err.length>0) {
      const res = path + ":" + JSON.stringify(criteria);
      // error = error.concat(err);
      // console.log("XXX: " + res);
      error.push(res)
    }
  }
  return error
}

function checkEqual(criteria,obj,path,lastLabel) {
  // example: { "orderItem.action": {$equal: "add", $eitherOf: ["service.id", "service.href"]}}
  //    orderItem -> obj
  //    criteria -> {$notEqual: "add", $eitherOf: ["service.id", "service.href"]}
  //    lastLabel -> action
  var error = [];
  if(criteria.$equal && (obj[lastLabel] === criteria.$equal)) {
    var subrule = cloneObject(criteria);
    delete subrule.$equal;
    if(Object.keys(subrule).length>0) {
      const err = processRule({$: subrule},obj,path,lastLabel);
      if(err.length>0) {
        const res = path + ":" + JSON.stringify(criteria);
        error.push(res)
      }
    }
  } else {
    const res = path + ":" + JSON.stringify(criteria);
    error.push(res);
  }
  return error
}

function checkAndRule(criteria,obj,path,lastLabel) {
  var error = [];
  if(criteria.$and && Array.isArray(criteria.$and)) {
    var err = processRule({$: criteria.$and[0]},obj,path,lastLabel);
    if(err.length===0) {
      // the condition is fulfilled, check rest
      var criterias = cloneObject(criteria.$and);
      criterias.shift();
      criterias.forEach(rule => {
        const issue = processRule(rule,obj,path);
        err = err.concat(issue)
      })
      if(err.length>0) {
        // return the error related to the complete rule
        const res = path + ":" + JSON.stringify(criteria);
        error.push(res)
      }
    }
  }
  return error
}

  
function generateState(stateRules, states) {
  var state=null;
  stateRules.forEach(item => {
    const newState = Object.keys(item)[0];
    const rule = item[newState];
    var match=true;
    Object.keys(rule).forEach(func => {
      const allowed = rule[func];
      switch(func) {
        case "$all":
        match = match && states.every(x => {return x == allowed;});
        break;
        case "$atLeastOne":
        match = match && states.has(allowed);
        break;
        case "$allIn":
        match = match && states.every(x => {return arrayContains(x,allowed);});
        break;
        default:
        match=false
      }
    });
    if(match){
      state = newState
    }
  });
  return state
}
 
function arrayContains(value, array) {
  if(Array.isArray(array)) {
    return (array.indexOf(value)>-1)
  } else {
    return false
  }
}
 
function split2s(str, delim) {
  var p=str.indexOf(delim);
  if (p !== -1) {
      return [str.substring(0,p), str.substring(p+1)]
  } else {
      return [str]
  }
}

function cloneObject(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function hasProperty (obj, path) {
  var arr = path.split('.');
  while (arr.length && (obj = obj[arr.shift()]));
  return (obj !== undefined)
}

module.exports = { validateRequest }

