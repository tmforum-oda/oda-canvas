const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const testDataFolder = './testData/'

const packageManagerUtils = {


  /**
  * Function that gets the exposedAPIs from the given segment of a helm chart.
  * @param    {String} componentPackage      Helm chart folder name
  * @param    {String} releaseName           Helm release name
  * @param    {String} componentSegmentName  segment of the component (coreFunction, management, security)
  * @return   {Array}          The array of 0 or more exposed APIs
  */  
  getExposedAPIsFromPackage: function(componentPackage, releaseName, componentSegmentName) {
    try {
      // run the helm template command to generate the component envelope
      const output = execSync('helm template ' + releaseName + ' ' + testDataFolder + componentPackage, { encoding: 'utf-8' });  
        
      // parse the template
      documentArray = YAML.parseAllDocuments(output)

      // assert that the documentArray is an array
      assert.equal(Array.isArray(documentArray), true, "The file should contain at least one YAML document")

      // assert that the file contains at least one YAML document
      assert.ok(documentArray.length > 0, "File should contain at least one YAML document")

      // get the document with kind: component
      const componentDocument = documentArray.find(document => document.get('kind') === 'Component')

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
    } catch (error) {
      // Handle the error here
      assert.ok(false, "Exception thrown when trying to get exposedAPIs from package: " + error.message)

      return []; // or return a default value
    }
  },

  /**
  * Function that checks if a helm chart is already installed, and installs it if not.
  * @param    {String} componentPackage      Helm chart folder name
  * @param    {String} releaseName           Helm release name
  */  
  installPackage: function(componentPackage, releaseName, namespace) {

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
      const output = execSync('helm upgrade ' + releaseName + ' ' + testDataFolder + componentPackage + ' -n ' + namespace, { encoding: 'utf-8' });   
    }
    else {
      // install the helm template command to generate the component envelope
      const output = execSync('helm install ' + releaseName + ' ' + testDataFolder + componentPackage + ' -n ' + namespace, { encoding: 'utf-8' });   
    } 
  },


  /**
  * Function that upgrades a helm chart (after checking that it is already installed).
  * @param    {String} componentPackage      Helm chart folder name
  * @param    {String} releaseName           Helm release name
  */  
  upgradePackage: function(componentPackage, releaseName, namespace) {

    // create an error if the helm chart is not already installed
    const helmList = execSync('helm list -o json  -n ' + namespace, { encoding: 'utf-8' });    
    var found = false
    // look through the helm list and see if there is a chart with name releaseName
    JSON.parse(helmList).forEach(chart => {
      if (chart.name == releaseName) {
        found = true
      }
    })
    if (!found) {
      // throw an error
      assert.ok(false, "The package '" + componentPackage + "' is not installed, so cannot be upgraded")
    }

    // upgrade the helm chart
    const output = execSync('helm upgrade ' + releaseName + ' ' + testDataFolder + componentPackage + ' -n ' + namespace, { encoding: 'utf-8' });   

  },

  /**
   * Uninstall a specified package using the helm uninstall command.
   *  
   * @param {string} releaseName - The name of the release to uninstall.
   * @param {string} namespace - The namespace of the release to uninstall.
   */
    uninstallPackage: function(releaseName, namespace) {

      // only uninstall the helm chart if it is already installed
      const helmList = execSync('helm list -o json  -n ' + namespace, { encoding: 'utf-8' });    
      var found = false
      // look through the helm list and see if there is a chart with name releaseName
      JSON.parse(helmList).forEach(chart => {
        if (chart.name == releaseName) {
          found = true
        }
      })

      if (found) {
        const output = execSync('helm uninstall ' + releaseName + ' -n ' + namespace, { encoding: 'utf-8' });
      }
    },

  /**
   * Upgrade a specified package using the helm upgrade command.
   *
   * @param {string} componentPackage - The name of the package to upgrade.
   * @param {string} releaseName - The name of the release to upgrade.
   * @param {string} namespace - The namespace of the release to upgrade.
   */
  upgradePackage: function(componentPackage, releaseName, namespace) {
    const output = execSync('helm upgrade ' + releaseName + ' ' + testDataFolder + componentPackage + ' -n ' + namespace, { encoding: 'utf-8' });   
  }



}



module.exports = packageManagerUtils