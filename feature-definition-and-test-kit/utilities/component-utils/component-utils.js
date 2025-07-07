const k8s = require('@kubernetes/client-node')
const fs = require('fs')
const axios = require('axios')

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const HTTP_CREATED = 201
const HTTP_OK = 200
const HTTP_DELETE_SUCCESS = 204

/**
* Helper function to replace a reference (like "href": "/category?name=Internet line of product") with the object details
* @param    {String} inObject     Javascript object to resolve references in
* @param    {String} inAPIURL     Name of the API used to resolve the references
* @return   {String}         String containing the base URL for the API, or null if the API is not found
*/
async function getReference(inObject, inAPIURL) {
  if (inObject['href']) {
    const response = await axios.get(inAPIURL + inObject['href'])
    inObject['id'] = response.data[0]['id']
    inObject['name'] = response.data[0]['name']
    inObject['href'] = response.data[0]['href']
    return inObject
  }
  return inObject
}

/**
* Helper function that resolves references (like "href": "/category?name=Internet line of product") and replaces with the object reference
* @param    {String} inObject     Javascript object to resolve references in
* @param    {String} inAPIURL     Name of the API used to resolve the references
* @return   {String}         String containing the base URL for the API, or null if the API is not found
*/
async function resolveReferences(inObject, inAPIURL) {
  // resolve any references in the inObject payload
  for (const parameter in inObject) {
    const parameterValue = inObject[parameter]
    if (Array.isArray(parameterValue)) {
      for (const index in parameterValue) {
        inObject[parameter][index] = await getReference(parameterValue[index], inAPIURL)
      }
    } else if (typeof parameterValue === 'object' && parameterValue !== null) {
      inObject[parameter] = await getReference(parameterValue, inAPIURL)
    }
  }
  return inObject
}

const componentUtils = {

  /**
  * Function that returns the base URL for a given API instance
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inAPIName              Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
  getAPIURL: async function (inComponentInstance, inAPIName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const APIResourceName = inComponentInstance + '-' + inAPIName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject('oda.tmforum.org', 'v1', inNamespace, 'exposedapis', undefined, undefined, 'metadata.name=' + APIResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    }
    var APIURL = namespacedCustomObject.body.items[0].status.apiStatus.url
    return APIURL
  },

  /**
  * Function that deletes test data from the namd API.
  * @param    {String} inResource           Name of the resource to be deleted
  * @param    {String} inAPIURL             Base URL of the API to load the data into
  * @return   {Boolean}          True if the data was deleted successfully, false otherwise
  */
  deleteTestData: async function (inResource, inAPIURL) {
    let loadedSuccessfully = true

    const response = await axios.get(inAPIURL + '/' + inResource)
    if (response.status !== HTTP_OK) {
      loadedSuccessfully = false
    } else {
      for (const index in response.data) {
        const delResponse = await axios.delete(inAPIURL + '/' + inResource + '/' + response.data[index]['id'])
        if (delResponse.status !== HTTP_DELETE_SUCCESS) {
          loadedSuccessfully = false
        }
      }
    }
    return loadedSuccessfully
  },

  /**
  * Function that loads test data from a file into the namd API.
  * @param    {String} inTestDataFile         Filename of the file containing the test data
  * @param    {String} inAPIURL               Base URL of the API to load the data into
  * @return   {Boolean}          True if the data was loaded successfully, false otherwise
  */
  loadTestDataFromFile: async function (inTestDataFile, inAPIURL) {
    const testData = JSON.parse(fs.readFileSync(inTestDataFile, 'utf8'))
    return this.loadTestDataFromObject(testData, inAPIURL)
  },

  /**
  * Function that loads test data from a dataTable into the namd API.
  * @param    {String} inputResource          Resource that the dataTable refers to
  * @param    {String} dataTable              dataTable containing the test data
  * @param    {String} inAPIURL               Base URL of the API to load the data into
  * @return   {Boolean}          True if the data was loaded successfully, false otherwise
  */
  loadTestDataFromDataTable: async function (inputResource, dataTable, inAPIURL) {
    const resourceData = dataTable.hashes()
    const testDataObject = { payloads: {} }
    testDataObject.payloads[inputResource] = resourceData
    return await componentUtils.loadTestDataFromObject(testDataObject, inAPIURL)
  },

  /**
  * Function that loads test data from a javascript object into the namd API.
  * @param    {String} inTestObject           Object containing the test data
  * @param    {String} inAPIURL               Base URL of the API to load the data into
  * @return   {Boolean}          True if the data was loaded successfully, false otherwise
  */
  loadTestDataFromObject: async function (inTestObject, inAPIURL) {
    let loadedSuccessfully = true
    for (const payload in inTestObject.payloads) {
      const resourceURL = inAPIURL + '/' + payload
      for (const index in inTestObject.payloads[payload]) {
        let resourceObject = inTestObject.payloads[payload][index]
        resourceObject = await resolveReferences(resourceObject, inAPIURL) // resolve any references in the resourceObject payload
        const response = await axios.post(resourceURL, resourceObject)
        if (response.status !== HTTP_CREATED) {
          loadedSuccessfully = false
        }
      }
    }
    return loadedSuccessfully
  },

  /**
  * Function that compares results data to test data from a file.
  * @param    {String} inTestDataFile         Filename of the file containing the test data
  * @param    {String} inReturnData           Object containing the results data
  * @return   {Boolean}          True if the data matches the test data, false otherwise
  */
  validateReturnDataFromFile: async function (inResultDataFile, inReturnData, inAPIURL) {
    const resultData = JSON.parse(fs.readFileSync(inResultDataFile, 'utf8'))
    return this.validateReturnDataFromObject(resultData, inReturnData, inAPIURL)
  },

  /**
  * Function that compares results data to test data from a dataTable.
  * @param    {String} inputResource          Resource that the dataTable refers to
  * @param    {String} dataTable              dataTable containing the test data
  * @param    {String} returnData             Object containing the results data
  * @return   {Boolean}          True if the data matches the test data, false otherwise
  */
  validateReturnDataFromDataTable: async function (inputResource, dataTable, returnData, inAPIURL) {
    const resourceData = dataTable.hashes()
    const testDataObject = { payloads: {} }
    testDataObject.payloads[inputResource] = resourceData
    return await this.validateReturnDataFromObject(testDataObject, returnData, inAPIURL)
  },

  /**
  * Function that compares results data to test data from a javascript object.
  * @param    {String} inTestDataFile         Filename of the file containing the test data
  * @param    {String} inReturnData           Object containing the results data
  * @return   {Boolean}          True if the data matches the test data, false otherwise
  */
  validateReturnDataFromObject: async function (validResultData, inReturnData, inAPIURL) {
    let validatedSuccessfully = true
    // go through each item in test data and compare to return data
    for (const payload in validResultData.payloads) {
      for (const index in validResultData.payloads[payload]) {
        let validResource = validResultData.payloads[payload][index]
        validResource = await resolveReferences(validResource, inAPIURL) // resolve any references in the body payload

        // compare body.name and body.description to return data
        let found = false
        for (const returnDataItem in inReturnData) {
          // compare every key in the validResource to the returnDataItem data
          let keyFound = true
          for (const key in validResource) {
            if (validResource[key] === inReturnData[returnDataItem][key]) {
              keyFound = keyFound && true // if this and previous keys match, keep going
            } else {
              keyFound = false
              break
            }
          }

          if (keyFound === true) {
            found = true
            break
          }
        }
        if (!found) { // if any of the the validResource was not found in the return data, then the test failed
          validatedSuccessfully = false
        }
      }
    }
    return validatedSuccessfully
  }
}
module.exports = componentUtils