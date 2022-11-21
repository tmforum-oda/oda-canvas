const { Given, When, Then, After, AfterAll } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
const componentUtils = require('component-utils');
const { exists } = require('fs');
const fs = require('fs')
const YAML = require('yaml')
const execSync = require('child_process').execSync;


chai.use(chaiHttp)
const NAMESPACE = 'components'
const HTTP_OK = 200

const testDataFolder = './testData/'
let componentInstanceName = ''
let documentArray = []
let testAPI
let testComponentName

// verify that the file exists, contains a YAML document, The document includes an ODA Component with at least 1 API in the componentSegment 
Given('An example component helm chart {string} with at least one API in its {string} segment', function (componentHelmChart, componentSegmentName) {

  // run the helm template command to generate the component envelope
  const output = execSync('helm template ctk ' + testDataFolder + componentHelmChart, { encoding: 'utf-8' });  
  
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
  } else if (componentSegmentName == 'management') {
    exposedAPIs = componentSegment.items
  } else if (componentSegmentName == 'security') {
    exposedAPIs = [componentSegment.get('partyrole')]
    exposedAPIs[0].set('name', 'partyrole')
  } else {
    assert.ok(false, "componentSegmentName should be one of 'coreFunction', 'management' or 'security'")
  }
  // assert that there is at least 1 API in the componentSegment
  assert.ok(exposedAPIs.length > 0, "The componentSegment should contain at least one API")

  // we will test the first API in the componentSegment
  testAPI = exposedAPIs[0]
});

When('I install the {string} component helm chart', function (componentHelmChart) {

  // only install the helm chart if it is not already installed
  const helmList = execSync('helm list -o json  -n ' + NAMESPACE, { encoding: 'utf-8' });    
  var found = false
  // look through the helm list and see if there is a chart with name 'ctk'
  JSON.parse(helmList).forEach(chart => {
    if (chart.name == 'ctk') {
      found = true
    }
  })

  if (!found) {
    // install the helm template command to generate the component envelope
    const output = execSync('helm install ctk ' + testDataFolder + componentHelmChart + ' -n ' + NAMESPACE, { encoding: 'utf-8' });   
  }
});

Then('I should see the {string} API resource in the Kubernetes cluster', {timeout : 10 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(testComponentName, APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 5000, "The API resource should be found within 3 seconds")
  }
});

Then('I should see the {string} API resource with a public url in the Kubernetes cluster', {timeout : 60 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(testComponentName, APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 50 * 1000, "The public url should be found within 50 seconds")

    //check if there is a public url on the API resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('apiStatus')) || (!apiResource.status.apiStatus.hasOwnProperty('url'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
});

Then('I should see the {string} API resource with an implementation ready status in the Kubernetes cluster', {timeout : 120 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(testComponentName, APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 100 * 1000, "The ready status should be found within 100 seconds")

    //check if there is a public url on the API resource status

    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('implementation')) || (!apiResource.status.implementation.hasOwnProperty('ready'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    } else if (!(apiResource.status.implementation.ready == true)) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
});

AfterAll(function () {
  // uninstall the helm template command to generate the component envelope
  const output = execSync('helm uninstall ctk -n ' + NAMESPACE, { encoding: 'utf-8' });    
});
