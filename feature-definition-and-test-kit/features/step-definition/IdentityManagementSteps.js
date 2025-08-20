// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const identityManagerUtils = require('identity-manager-utils-keycloak');
const componentUtils = require('component-utils');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)

const NAMESPACE = 'components'
const COMPONENT_DEPLOY_TIMEOUT = 100 * 1000 // 100 seconds

setDefaultTimeout( 20 * 1000);

/**
 * Check for role to be assigned to the canvassystem client in identity management.
 *
 * @param {string} canvassystemClientName - the client name of the canvas system to check.
 * @param {string} componentName - The name of the component to check.
 * @returns {Promise<void>} - A Promise that resolves when the component is available.
 */
Then('I should see the predefined role assigned to the {string} client for the {string} component in the identity platform', async function (canvassystemClientName, componentName) {
  console.log('\n=== Verifying Predefined Role Assignment to Canvas System Client ===');
  let componentResource = null
  let canvassystemRole = null
  var startTime = performance.now()
  var endTime

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(global.currentReleaseName + '-' + componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")

    // check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('spec')) || (!componentResource.spec.hasOwnProperty('securityFunction')) || (!componentResource.spec.securityFunction.hasOwnProperty('canvasSystemRole'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
      canvassystemRole = componentResource.spec.securityFunction.canvasSystemRole;
      allClientRoles = await identityManagerUtils.getRolesForClient(canvassystemClientName);
      //return 'pending';
      assert.ok(allClientRoles.includes(canvassystemRole), 'The predefine role for the canvassystem client should be correctly assigned in the identity platform');
    }
  }
});

When('I POST a new PermissionSpecificationSet to the {string} component with the following details:', async function (componentName, dataTable) {
  console.log('\n=== Starting PermissionSpecificationSet Creation Test ===');
  
  // Extract all rows from the dataTable
  const permissionSpecDataRows = dataTable.hashes(); // Get all rows of data
  console.log(`Processing ${permissionSpecDataRows.length} PermissionSpecificationSet(s)`);
  
  // Get the ExposedAPI resource to find the correct API URL and path
  const exposedAPIResource = await resourceInventoryUtils.getExposedAPIResource('userrolesandpermissions', componentName, NAMESPACE);
  
  // Assert that the ExposedAPI resource was found
  assert.ok(exposedAPIResource, 'The userrolesandpermissions ExposedAPI resource should be available');
  assert.ok(exposedAPIResource.status && exposedAPIResource.status.apiStatus && exposedAPIResource.status.apiStatus.url, 'The ExposedAPI should have a URL in its status');
  
  // Get the base API URL from the ExposedAPI status
  const baseApiURL = exposedAPIResource.status.apiStatus.url;
  
  // Store created resources for potential use in subsequent steps
  global.createdPermissionSpecs = [];
  
  // Process each row in the dataTable
  for (let i = 0; i < permissionSpecDataRows.length; i++) {
    const permissionSpecData = permissionSpecDataRows[i];
    console.log(`Creating PermissionSpecificationSet ${i + 1}/${permissionSpecDataRows.length}: '${permissionSpecData.name}' via TMF672 API: ${baseApiURL}`);
    
    // Create the PermissionSpecificationSet payload based on TMF672 specification
    const permissionSpecPayload = {
      '@type': 'PermissionSpecificationSet',
      '@baseType': 'PermissionSpecificationSet',
      name: permissionSpecData.name,
      description: permissionSpecData.description,
      involvementRole: permissionSpecData.involvementRole || 'DefaultRole',
      permissionSpecification: [
        {
          '@type': 'PermissionSpecification',
          '@baseType': 'PermissionSpecification',
          name: permissionSpecData.name,
          description: permissionSpecData.description,
          function: "DefaultRole",
          action: "all"   
        }
      ]
    };
    
    try {
      // Make the POST request to create the PermissionSpecificationSet
      const response = await chai.request(baseApiURL)
        .post('/permissionSpecificationSet')
        .set('User-Agent', 'Canvas-BDD-Test')
        .trustLocalhost(true)
        .disableTLSCerts()
        .send(permissionSpecPayload);
      
      // Assert that the request was successful (201 Created)
      assert.ok(response.status === 201, `Expected status 201 but got ${response.status} for PermissionSpecificationSet '${permissionSpecData.name}'`);
      
      // Store the created resource details
      global.createdPermissionSpecs.push(response.body);
      
      console.log(`✅ Successfully created PermissionSpecificationSet '${permissionSpecData.name}' with ID: ${response.body.id}`);
      
    } catch (error) {
      console.error(`❌ Error creating PermissionSpecificationSet '${permissionSpecData.name}':`, error.message);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
        console.error('Response body:', JSON.stringify(error.response.body, null, 2));
      }
      if (error.request) {
        console.error('Request details:');
        console.error('- Method:', error.request.method);
        console.error('- URL:', error.request.url);
        console.error('- Headers:', error.request.headers);
      }
      console.log(`=== PermissionSpecificationSet Creation Test Failed for '${permissionSpecData.name}' ===`);
      throw error;
    }
  }
  
  // Store the last created resource for backward compatibility
  global.lastCreatedPermissionSpec = global.createdPermissionSpecs[global.createdPermissionSpecs.length - 1];
  
  console.log(`✅ Successfully created all ${permissionSpecDataRows.length} PermissionSpecificationSet(s)`);
  console.log('=== PermissionSpecificationSet Creation Test Complete ===');
});

Then('the role {string} should be created in the Identity Platform for {string} component', async function (roleName, componentName) {
  console.log('\n=== Starting Identity Platform Role Verification ===');
  console.log(`Verifying role '${roleName}' exists for component '${componentName}'`);

  // Wait a moment for the async processing to complete
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  try {
    // Get all roles for the specified component from Keycloak
    const componentRoles = await identityManagerUtils.getRolesForClient(componentName);

    // Check if the role exists
    const roleExists = componentRoles.includes(roleName);

    if (roleExists) {
      console.log(`✅ Role verification successful: '${roleName}' exists in Identity Platform for component '${componentName}'`);
    } else {
      console.error(`❌ Role verification failed: '${roleName}' not found in Identity Platform for component '${componentName}'`);
      console.error('This could indicate:');
      console.error('- Canvas Identity Config operator is not running');
      console.error('- Event notification was not received by identity listener');
      console.error('- Identity listener failed to process the PermissionSpecificationSet event');
      console.error('- Keycloak integration is not configured correctly');
    }
    
    assert.ok(roleExists, `Role '${roleName}' should exist in Identity Platform for client '${componentName}'. Found roles: ${componentRoles.join(', ')}`);
    
    console.log('=== Identity Platform Role Verification Complete ===');
    
  } catch (error) {
    console.error('❌ Error during Identity Platform role verification:', error.message);
    console.error('Error details:');
    console.error(`- Target role: '${roleName}'`);
    console.error(`- Target client: '${componentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    if (error.code) {
      console.error(`- Error code: ${error.code}`);
    }
    
    console.error('Possible causes:');
    console.error('- Keycloak service is not accessible');
    console.error('- Invalid Keycloak credentials or configuration');
    console.error('- Network connectivity issues to Identity Platform');
    console.error('- Canvas Identity Config operator is not properly configured');
    
    console.log('=== Identity Platform Role Verification Failed ===');
    throw error;
  }
});

Given('the role {string} exists in the Identity Platform for {string} component', async function (roleName, componentName) {
  console.log('\n=== Checking Role Existence in Identity Platform ===');
  console.log(`Checking for existing role: '${roleName}'`);
  
 
  try {
    // Get all roles for the specified client from Keycloak
    const componentRoles = await identityManagerUtils.getRolesForClient(componentName);
    
    // Check if the role exists
    const roleExists = componentRoles.includes(roleName);
    
    if (roleExists) {
      console.log(`✅ Role '${roleName}' already exists in Identity Platform for client '${componentName}'`);
      // Store the role information for potential use in subsequent steps
      global.existingRole = { name: roleName, client: componentName };
    } else {
      console.log(`⚠️  Role '${roleName}' does not exist in Identity Platform for client '${componentName}'`);
      console.log('This step is verifying a precondition - the role should already exist.');
      console.log('If this is expected, the test scenario should create the role first.');
      
      // For a Given step, we should fail if the precondition is not met
      assert.ok(roleExists, `Precondition failed: Role '${roleName}' should already exist in Identity Platform for client '${componentName}'. Found roles: ${componentRoles.join(', ')}`);
    }
    
    console.log('=== Identity Platform Role Existence Check Complete ===');
    
  } catch (error) {
    console.error('❌ Error during Identity Platform role existence check:', error.message);
    console.error('Error details:');
    console.error(`- Target role: '${roleName}'`);
    console.error(`- Target client: '${componentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    if (error.code) {
      console.error(`- Error code: ${error.code}`);
    }
    
    console.error('Possible causes:');
    console.error('- Keycloak service is not accessible');
    console.error('- Invalid Keycloak credentials or configuration');
    console.error('- Network connectivity issues to Identity Platform');
    console.error('- Canvas Identity Config operator is not properly configured');
    console.error('- Client does not exist in Keycloak');
    
    console.log('=== Identity Platform Role Existence Check Failed ===');
    throw error;
  }
});

When('I DELETE the PermissionSpecificationSet {string} from the {string} component', async function (permissionSpecName, componentName) {
  console.log('\n=== Starting PermissionSpecificationSet Deletion Test ===');
  console.log(`Target PermissionSpecificationSet to delete: '${permissionSpecName}'`);
  console.log(`Target component: '${componentName}'`);

  // Get the ExposedAPI resource to find the correct API URL
  const exposedAPIResource = await resourceInventoryUtils.getExposedAPIResource('userrolesandpermissions', componentName, NAMESPACE);
  
  assert.ok(exposedAPIResource, 'The userrolesandpermissions ExposedAPI resource should be available');
  assert.ok(exposedAPIResource.status && exposedAPIResource.status.apiStatus && exposedAPIResource.status.apiStatus.url, 'The ExposedAPI should have a URL in its status');
  
  const baseApiURL = exposedAPIResource.status.apiStatus.url;
  
  try {
    // First, find the permission specification set by name
    const getResponse = await chai.request(baseApiURL)
      .get(`/permissionSpecificationSet?name=${permissionSpecName}`)
      .set('User-Agent', 'Canvas-BDD-Test')
      .trustLocalhost(true)
      .disableTLSCerts();
    
    assert.ok(getResponse.status === 200, `Expected status 200 but got ${getResponse.status}`);
    assert.ok(getResponse.body.length > 0, `PermissionSpecificationSet '${permissionSpecName}' should exist`);
    
    const permissionSpecId = getResponse.body[0].id;
    
    // Delete the permission specification set
    const deleteResponse = await chai.request(baseApiURL)
      .delete(`/permissionSpecificationSet/${permissionSpecId}`)
      .set('User-Agent', 'Canvas-BDD-Test')
      .trustLocalhost(true)
      .disableTLSCerts();
    
    assert.ok([204, 200].includes(deleteResponse.status), `Expected status 204 or 200 but got ${deleteResponse.status}`);
    
    // Store the deleted resource details for verification
    global.lastDeletedPermissionSpec = { id: permissionSpecId, name: permissionSpecName };
    
    console.log(`✅ Successfully deleted PermissionSpecificationSet '${permissionSpecName}' with ID: ${permissionSpecId}`);
    console.log('=== PermissionSpecificationSet Deletion Test Complete ===');
    
  } catch (error) {
    console.error('❌ Error deleting PermissionSpecificationSet:', error.message);
    console.error('Error details:');
    console.error(`- Target PermissionSpecificationSet: '${permissionSpecName}'`);
    console.error(`- Component: '${componentName}'`);
    console.error(`- API URL: ${baseApiURL}`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    if (error.request) {
      console.error('Request details:');
      console.error(`- Method: ${error.request.method}`);
      console.error(`- URL: ${error.request.url}`);
      console.error(`- Headers: ${JSON.stringify(error.request.headers, null, 2)}`);
    }
    
    if (error.code) {
      console.error(`- Error code: ${error.code}`);
    }
    
    console.error('Possible causes:');
    console.error('- PermissionSpecificationSet does not exist (may have been deleted already)');
    console.error('- TMF672 API endpoint not accessible through Canvas');
    console.error('- Canvas ExposedAPI resource not properly configured');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    console.error('- TMF672 API implementation does not support DELETE operation');
    
    console.log('=== PermissionSpecificationSet Deletion Test Failed ===');
    throw error;
  }
});

Then('the role {string} should be removed from the Identity Platform for {string} component', async function (roleName, componentName) {
  console.log('\n=== Verifying Role Removal from Identity Platform ===');
  console.log(`Verifying role '${roleName}' has been removed from component '${componentName}'`);

  // Wait a moment for the async processing to complete
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  try {
    // Get all roles for the specified component from Keycloak
    const componentRoles = await identityManagerUtils.getRolesForClient(componentName);

    // Check if the role no longer exists
    const roleExists = componentRoles.includes(roleName);
    
    assert.ok(!roleExists, `Role '${roleName}' should not exist in Identity Platform for client '${componentName}'. Found roles: ${componentRoles.join(', ')}`);
    
    console.log(`Verified role '${roleName}' was removed from Identity Platform for client '${componentName}'`);
    
  } catch (error) {
    console.error(`Error checking role removal in Identity Platform: ${error.message}`);
    throw error;
  }
});

Given('the {string} component has an existing PermissionSpecificationSet {string}', async function (componentName, permissionSpecName) {
  console.log('\n=== Starting PermissionSpecificationSet Setup Verification ===');
  console.log(`Required PermissionSpecificationSet: '${permissionSpecName}'`);
  
  // Get the ExposedAPI resource to find the correct API URL
  const exposedAPIResource = await resourceInventoryUtils.getExposedAPIResource('userrolesandpermissions', componentName, NAMESPACE);
  
  assert.ok(exposedAPIResource, 'The userrolesandpermissions ExposedAPI resource should be available');
  assert.ok(exposedAPIResource.status && exposedAPIResource.status.apiStatus && exposedAPIResource.status.apiStatus.url, 'The ExposedAPI should have a URL in its status');
  
  const baseApiURL = exposedAPIResource.status.apiStatus.url;
  
  try {
    // Check if the permission specification set already exists
    const getResponse = await chai.request(baseApiURL)
      .get(`/permissionSpecificationSet?name=${permissionSpecName}`)
      .set('User-Agent', 'Canvas-BDD-Test')
      .trustLocalhost(true)
      .disableTLSCerts();
    
    if (getResponse.status === 200 && getResponse.body.length > 0) {
      console.log(`✅ PermissionSpecificationSet '${permissionSpecName}' already exists`);
      global.existingPermissionSpec = getResponse.body[0];
      console.log('=== PermissionSpecificationSet Setup Verification Complete (Found Existing) ===');
      return;
    }
    
    console.log(`⚠️  PermissionSpecificationSet '${permissionSpecName}' does not exist - creating it for test setup`);
    
    // Create the permission specification set if it doesn't exist
    const permissionSpecPayload = {
      '@type': 'PermissionSpecificationSet',
      '@baseType': 'PermissionSpecificationSet',
      name: permissionSpecName,
      description: `Test permission specification set for ${permissionSpecName}`,
      involvementRole: 'TestRole',
      permissionSpecification: [
        {
          '@type': 'PermissionSpecification',
          '@baseType': 'PermissionSpecification',
          name: permissionSpecName,
          description: `Test permission for ${permissionSpecName}`,
          function: "TestRole",
          action: "all"              
        }
      ]
    };
    
    const response = await chai.request(baseApiURL)
      .post('/permissionSpecificationSet')
      .set('User-Agent', 'Canvas-BDD-Test')
      .trustLocalhost(true)
      .disableTLSCerts()
      .send(permissionSpecPayload);
    
    assert.ok(response.status === 201, `Expected status 201 but got ${response.status}`);
    global.existingPermissionSpec = response.body;
    
    console.log(`✅ Successfully created PermissionSpecificationSet '${permissionSpecName}' for testing with ID: ${response.body.id}`);
    console.log('=== PermissionSpecificationSet Setup Verification Complete (Created New) ===');
    
  } catch (error) {
    console.error('❌ Error during PermissionSpecificationSet setup verification:', error.message);
    console.error('Error details:');
    console.error(`- Target component package: '${componentPackage}'`);
    console.error(`- Required PermissionSpecificationSet: '${permissionSpecName}'`);
    console.error(`- Component name: '${componentName}'`);
    console.error(`- API URL: ${baseApiURL}`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    if (error.request) {
      console.error('Request details:');
      console.error(`- Method: ${error.request.method}`);
      console.error(`- URL: ${error.request.url}`);
      console.error(`- Headers: ${JSON.stringify(error.request.headers, null, 2)}`);
    }
    
    if (error.code) {
      console.error(`- Error code: ${error.code}`);
    }
    
    console.error('Possible causes:');
    console.error('- Canvas ExposedAPI resource not ready or misconfigured');
    console.error('- TMF672 API endpoint not accessible');
    console.error('- Component not properly deployed with permission specification API');
    console.error('- Network connectivity issues to Canvas API Gateway/Service Mesh');
    console.error('- Authentication/authorization issues with Canvas APIs');
    
    console.log('=== PermissionSpecificationSet Setup Verification Failed ===');
    throw error;
  }
});

Then('the client {string} should be removed from the Identity Platform', async function (componentName) {
  console.log('\n=== Starting Identity Platform Client Removal Verification ===');
  console.log(`Verifying client '${componentName}' has been removed from Identity Platform`);
  
  // Wait a moment for the async processing to complete
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  try {
    // Check if the client still exists in Keycloak
    const clientExists = await identityManagerUtils.clientExists(componentName);
    
    if (!clientExists) {
      console.log(`✅ Client removal verification successful: '${componentName}' has been removed from Identity Platform`);
    } else {
      console.error(`❌ Client removal verification failed: '${componentName}' still exists in Identity Platform`);
      console.error('This could indicate:');
      console.error('- Canvas Identity Config operator is not running');
      console.error('- Component deletion event was not received by identity listener');
      console.error('- Identity listener failed to process the component deletion event');
      console.error('- Keycloak integration is not configured correctly');
      console.error('- Client deletion is not implemented in the identity management workflow');
    }
    
    assert.ok(!clientExists, `Client '${componentName}' should not exist in Identity Platform after removal`);
    
    console.log('=== Identity Platform Client Removal Verification Complete ===');
    
  } catch (error) {
    console.error('❌ Error during Identity Platform client removal verification:', error.message);
    console.error('Error details:');
    console.error(`- Target client: '${componentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    if (error.code) {
      console.error(`- Error code: ${error.code}`);
    }
    
    console.error('Possible causes:');
    console.error('- Keycloak service is not accessible');
    console.error('- Invalid Keycloak credentials or configuration');
    console.error('- Network connectivity issues to Identity Platform');
    console.error('- Canvas Identity Config operator is not properly configured');
    console.error('- Client removal functionality not implemented in identity management');
    
    console.log('=== Identity Platform Client Removal Verification Failed ===');
    throw error;
  }
});