const k8s = require('@kubernetes/client-node')
const fs = require('fs')
const axios = require('axios')
const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const HTTP_CREATED = 201
const HTTP_OK = 200
const HTTP_DELETE_SUCCESS = 204
const testDataFolder = './testData/'

const GROUP = "oda.tmforum.org"
const VERSION = "v1beta2"
const APIS_PLURAL = "apis"
const COMPONENTS_PLURAL = "components"

let testComponentName

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
  * Function that returns the custom API resource given API instance
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inAPIName              Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}         The API resource object, or null if the API is not found
  */
  getAPIResource: async function (inAPIName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const APIResourceName = testComponentName + '-' + inAPIName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, APIS_PLURAL, undefined, undefined, 'metadata.name=' + APIResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  /**
  * Function that returns the custom Component resource given Component Name
  * @param    {String} inComponentName        Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
    getComponentResource: async function (inComponentName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)

    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, COMPONENTS_PLURAL, undefined, undefined, 'metadata.name=' + inComponentName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },
  
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
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, APIS_PLURAL, undefined, undefined, 'metadata.name=' + APIResourceName)
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
  },

  /**
  * Function that gets the exposedAPIs from the given segment of a helm chart.
  * @param    {String} componentHelmChart    Helm chart folder name
  * @param    {String} releaseName           Helm release name
  * @param    {String} componentSegmentName  segment of the component (coreFunction, management, security)
  * @return   {Array}          The array of 0 or more exposed APIs
  */  
  getExposedAPIsFromHelm: function(componentHelmChart, releaseName, componentSegmentName) {

    // run the helm template command to generate the component envelope
    const output = execSync('helm template ' + releaseName + ' ' + testDataFolder + componentHelmChart, { encoding: 'utf-8' });  
      
    // parse the template
    documentArray = YAML.parseAllDocuments(output)

    // assert that the documentArray is an array
    assert.equal(Array.isArray(documentArray), true, "The file should contain at least one YAML document")

    // assert that the file contains at least one YAML document
    assert.ok(documentArray.length > 0, "File should contain at least one YAML document")

    // get the document with kind: component
    const componentDocument = documentArray.find(document => document.get('kind') === 'component')
    testComponentName = componentDocument.get('metadata').get('name')

    // get the spec of the component
    const componentSpec = componentDocument.get('spec')

    // Find the componentSegment with the name componentSegmentName
    let componentSegment
    componentSpec.items.forEach(item => {
      if (item.key == componentSegmentName) {
        componentSegment = item.value
      }
    })

    let exposedAPIs = []

    if (componentSegmentName == 'coreFunction') {
      exposedAPIs = componentSegment.items.filter(item => item.key == 'exposedAPIs')[0].value.items
    } else if (componentSegmentName == 'managementFunction') {
      exposedAPIs = componentSegment.items
    } else if (componentSegmentName == 'securityFunction') {
      exposedAPIs = [componentSegment.items]
    } else {
      assert.ok(false, "componentSegmentName should be one of 'coreFunction', 'managementFunction' or 'securityFunction'")
    }

    return exposedAPIs
  },

  /**
  * Function that checks if a helm chart is already installed, and installs it if not.
  * @param    {String} componentHelmChart    Helm chart folder name
  * @param    {String} releaseName           Helm release name
  */  
  installHelmChart: function(componentHelmChart, releaseName, namespace) {

    // only install the helm chart if it is not already installed
    const helmList = execSync('helm list -o json  -n ' + namespace, { encoding: 'utf-8' });    
    var found = false
    // look through the helm list and see if there is a chart with name releaseName
    JSON.parse(helmList).forEach(chart => {
      if (chart.name == releaseName) {
        found = true
      }
    })

    if (found) {
      const output = execSync('helm upgrade ' + releaseName + ' ' + testDataFolder + componentHelmChart + ' -n ' + namespace, { encoding: 'utf-8' });   
    }
    else {
      // install the helm template command to generate the component envelope
      const output = execSync('helm install ' + releaseName + ' ' + testDataFolder + componentHelmChart + ' -n ' + namespace, { encoding: 'utf-8' });   
    } 
  } 
}
module.exports = componentUtils