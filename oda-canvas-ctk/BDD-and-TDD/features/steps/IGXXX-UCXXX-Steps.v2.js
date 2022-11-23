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
const releaseName = 'ctk'
const testDataFolder = './testData/'

let documentArray = []

// verify that the file exists, contains a YAML document, The document includes an ODA Component with at least 1 API in the componentSegment 
Given('An example component helm chart {string} with {string} API in its {string} segment', function (componentHelmChart, numberOfAPIs, componentSegmentName) {
  exposedAPIs = componentUtils.getExposedAPIsFromHelm(componentHelmChart, 'ctk', componentSegmentName)
  // assert that there are the correct number of APIs in the componentSegment
  assert.ok(exposedAPIs.length == numberOfAPIs, "The componentSegment should contain " + numberOfAPIs + " API")
});

When('I install the {string} component helm chart', function (componentHelmChart) {
  componentUtils.installHelmChart(componentHelmChart, releaseName, NAMESPACE)
});

Given('An example component helm chart {string} has been installed', function (componentHelmChart) {
  componentUtils.installHelmChart(componentHelmChart, releaseName, NAMESPACE)
});

Given('the {string} component has a deployment status of {string}', {timeout : 120 * 1000}, async function (componentName, deploymentStatus) {
  let componentResource = null
  var startTime = performance.now()
  var endTime
  while (componentResource == null) {
    componentResource = await componentUtils.getComponentResource(releaseName + '-' + componentName, NAMESPACE)
    endTime = performance.now()
    // assert that the Component resource was found within 100 seconds
    assert.ok(endTime - startTime < 100 * 1000, "The Component resource should be found within 100 seconds")

    //check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('status')) || (!componentResource.status.hasOwnProperty('summary/status')) || (!componentResource.status['summary/status'].hasOwnProperty('deployment_status'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
        // console.log("The component deployment status is ")
        // console.log(componentResource.status['summary/status']['deployment_status'])
        if (!(componentResource.status['summary/status']['deployment_status'] == deploymentStatus)) {
          componentResource = null // reset the componentResource to null so that we can try again
      }
    }
  }
});

When('I upgrade the {string} component helm chart', function (componentHelmChart) {
    // install the helm template command to generate the component envelope
    const output = execSync('helm upgrade ' + releaseName + ' ' + testDataFolder + componentHelmChart + ' -n ' + NAMESPACE, { encoding: 'utf-8' });   
});

Then('I should see the {string} API resource', {timeout : 10 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 5000, "The API resource should be found within 3 seconds")
  }
});

Then('I should not see the {string} API resource', {timeout : 10 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = 'not null'
  var startTime = performance.now()
  var endTime
  while (apiResource != null) {
    apiResource = await componentUtils.getAPIResource(APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was removed within 3 seconds
    assert.ok(endTime - startTime < 5000, "The API resource should be removed within 3 seconds")
  }
});

Then('I should see the {string} API resource with a url on the Service Mesh or Gateway', {timeout : 60 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 50 * 1000, "The url should be found within 50 seconds")

    //check if there is a url on the API resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('apiStatus')) || (!apiResource.status.apiStatus.hasOwnProperty('url'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
});

Then('I should see the {string} API resource with an implementation ready status on the Service Mesh or Gateway', {timeout : 120 * 1000}, async function (APIName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  while (apiResource == null) {
    apiResource = await componentUtils.getAPIResource(APIName, NAMESPACE)
    endTime = performance.now()
    // assert that the API resource was found within 3 seconds
    assert.ok(endTime - startTime < 100 * 1000, "The ready status should be found within 100 seconds")

    //check if there is a url on the API resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('implementation')) || (!apiResource.status.implementation.hasOwnProperty('ready'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    } else if (!(apiResource.status.implementation.ready == true)) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
});

AfterAll(function () {
  // uninstall the helm template command to generate the component envelope
  // const output = execSync('helm uninstall ctk -n ' + NAMESPACE, { encoding: 'utf-8' });    
});
