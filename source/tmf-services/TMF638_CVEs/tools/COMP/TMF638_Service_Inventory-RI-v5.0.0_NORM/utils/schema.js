'use strict'

const { getSwaggerDoc } = require('./swaggerUtils');

function replaceRefs(doc, source, replaced, processing, circular) {
    let res
    replaced   = replaced   || {}
    processing = processing || {}
    circular   = circular   || []

    if(!doc) return {data: {}, circular: []}

    if (typeof doc !== 'object' && !Array.isArray(doc) ) return {data: doc, circular: []}

    if(Array.isArray(doc)) {
        res = doc.map(element => {
            const result = replaceRefs(element,source)
            circular = [...new Set(circular.concat(result.circular))] 
            return result.data
        })
        return {data: res, circular: circular} 
    }
    
    res={}
    Object.keys(doc).filter(key=>key!=="example").forEach(key => {
        if(key==='$ref') {
            const reference = doc[key]
            if(replaced[reference]) {
                res = replaced[reference]
            } else if(processing[reference]) {
                res={ "$ref": reference }
                circular.push(reference)
            } else {
                processing[reference]=true
                const referenced = getElement(source,doc[key])
                const result = replaceRefs(referenced,source,replaced,processing,circular)
                res = result.data
                circular = [...new Set(circular.concat(result.circular))] 
                replaced[reference] = res
                processing[reference]=false
            }
            return {data: res, circular: circular}

        } else {
            const result = replaceRefs(doc[key],source,replaced,processing,circular)
            res[key] = result.data
            circular = [...new Set(circular.concat(result.circular))] 
        }
    })

    return {data: res, circular: circular}
}

function getElement(source, key) {
    let res=source
    key.replace("#/","").split("/").forEach(p => res=res?.[p])
    return res
}


function expandReferences(doc,source) {
    let max=10
    let flattened = replaceRefs(doc,source)
    while(flattened?.circular?.length>0 && max>0) {
        flattened = replaceRefs(flattened.data,flattened.data)
        max--
    }
    return flattened.data
}

function expandAPIReferences() {
    const apidoc = getSwaggerDoc()
    let expanded = expandReferences(apidoc.components,apidoc)
    return expanded?.schemas || expanded
}

module.exports = {
    expandAPIReferences
}