'use strict'

function getId(query) {
    return query?.criteria?.id || query?.id
}

function getFieldSelection(query) {
    return Object.keys(query?.options?.projection || {})
}

function getOffset(query) {
    return query?.options?.skip
}

function getLimit(query) {
    return query?.options?.limit
}

module.exports = {
    getId,
    getFieldSelection,
    getOffset,
    getLimit
}
