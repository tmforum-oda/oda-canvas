// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const componentUtils = require('component-utils');

const { When, Then, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);

// Create an HTTPS agent that ignores self-signed certificates
const https = require('https');
const agent = new https.Agent({
  rejectUnauthorized: false
});

const NAMESPACE = 'components';
const DEBUG_LOGS = true;

setDefaultTimeout(60 * 1000);

/**
 * Query the product agent component using its exposed API.
 *
 * Reuses the same style as productcatalog functional steps:
 * - resolve API URL from the component name + ExposedAPI name
 * - invoke the API over HTTPS
 * - store the response on the Cucumber world for later assertions
 *
 * Expected ExposedAPI name for the agent: 'agentquery'
 *
 * @param {string} componentName - The component name, e.g. 'pa-1-productagent'
 * @param {string} inputText - The natural-language query to send to the agent
 * @returns {Promise<void>}
 */
When('I query the {string} component with input {string}', async function (componentName, inputText) {
  console.log('\n=== Starting Product Agent Query ===');
  console.log(`Querying agent component '${componentName}' with input '${inputText}'`);

  try {
    const agentAPIURL = await componentUtils.getAPIURL(componentName, 'agentquery', NAMESPACE);
    assert.notEqual(agentAPIURL, null, `Can't find Product Agent API for component '${componentName}'`);

    console.log(`✅ Successfully located Product Agent API: ${agentAPIURL}`);

    const requestBody = {
      requestId: 'bdd-agent-query-001',
      agent: {
        agentId: 'product-agent-poc',
        version: 'v1'
      },
      task: {
        type: 'generic-query',
        input: {
          text: inputText
        }
      },
      caller: {
        type: 'user',
        id: 'bdd-test'
      },
      responseMode: 'sync',
      executionOptions: {
        maxToolCalls: 1,
        allowModelReasoning: true
      },
      metadata: {
        channel: 'bdd'
      }
    };

    if (DEBUG_LOGS) {
      console.log('Agent request body:', JSON.stringify(requestBody, null, 2));
      console.log('Agent request URL:', `${agentAPIURL}/query`);
    }
    
    console.log('Sending request to Product Agent API...');
    const response = await chai.request(agentAPIURL)
      .post('/query')
      .agent(agent)
      .trustLocalhost(true)
      .disableTLSCerts()
      .send(requestBody);

    this.agentResponse = response;
    this.agentResponseBody = response.body;

    assert.equal(response.status, 200, `Expected HTTP 200 from Product Agent API but got ${response.status}`);

    console.log(`✅ Successfully received Product Agent response with HTTP status ${response.status}`);

    if (DEBUG_LOGS) {
      console.log('Agent response body:', JSON.stringify(this.agentResponseBody, null, 2));
    }

    console.log('=== Product Agent Query Complete ===');
  } catch (error) {
    console.error(`❌ Error during Product Agent query: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Input text: '${inputText}'`);
    console.error(`- Error type: ${error.constructor.name}`);

    if (error.response) {
      this.agentResponse = error.response;
      this.agentResponseBody = error.response.body;
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }

    console.error('Possible causes:');
    console.error('- Agent ExposedAPI URL not accessible');
    console.error('- Product Agent component not properly deployed');
    console.error('- Canvas API Gateway / Service Mesh route not configured correctly');
    console.error('- Agent request payload rejected by the API');

    console.log('=== Product Agent Query Failed ===');
    throw error;
  }
});

/**
 * Verify the logical response status returned by the product agent.
 *
 * @param {string} componentName - The component name, e.g. 'pa-1-productagent'
 * @param {string} expectedStatus - Expected status, e.g. 'completed' or 'not_found'
 * @returns {Promise<void>}
 */
Then('the response status from the {string} component should be {string}', async function (componentName, expectedStatus) {
  console.log('\n=== Starting Product Agent Response Status Verification ===');
  console.log(`Verifying response status from component '${componentName}' is '${expectedStatus}'`);

  try {
    assert.ok(this.agentResponseBody, 'Expected agent response body to be available');
    assert.ok(
      this.agentResponseBody.hasOwnProperty('status'),
      "Expected response body to contain a 'status' field"
    );

    const actualStatus = this.agentResponseBody.status;
    assert.equal(
      actualStatus,
      expectedStatus,
      `Expected response status '${expectedStatus}' but found '${actualStatus}'`
    );

    console.log(`✅ Successfully verified response status '${expectedStatus}'`);
    console.log('=== Product Agent Response Status Verification Complete ===');
  } catch (error) {
    console.error(`❌ Error during Product Agent response status verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Expected status: '${expectedStatus}'`);
    if (this.agentResponseBody) {
      console.error(`- Actual response body: ${JSON.stringify(this.agentResponseBody, null, 2)}`);
    }
    console.log('=== Product Agent Response Status Verification Failed ===');
    throw error;
  }
});

/**
 * Verify the product agent response contains expected text in the answer body.
 *
 * @param {string} componentName - The component name, e.g. 'pa-1-productagent'
 * @param {string} expectedText - Text expected to appear in answer.text
 * @returns {Promise<void>}
 */
Then('the response from the {string} component should contain {string}', async function (componentName, expectedText) {
  console.log('\n=== Starting Product Agent Response Content Verification ===');
  console.log(`Verifying response from component '${componentName}' contains '${expectedText}'`);

  try {
    assert.ok(this.agentResponseBody, 'Expected agent response body to be available');
    assert.ok(
      this.agentResponseBody.hasOwnProperty('answer'),
      "Expected response body to contain an 'answer' object"
    );
    assert.ok(
      this.agentResponseBody.answer && this.agentResponseBody.answer.hasOwnProperty('text'),
      "Expected response body to contain 'answer.text'"
    );

    const answerText = this.agentResponseBody.answer.text;
    assert.ok(
      typeof answerText === 'string' && answerText.length > 0,
      'Expected answer.text to be a non-empty string'
    );

    assert.ok(
      answerText.toLowerCase().includes(expectedText.toLowerCase()),
      `Expected answer text to contain '${expectedText}', but got '${answerText}'`
    );

    console.log(`✅ Successfully verified response contains '${expectedText}'`);
    console.log('=== Product Agent Response Content Verification Complete ===');
  } catch (error) {
    console.error(`❌ Error during Product Agent response content verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Expected text: '${expectedText}'`);
    if (this.agentResponseBody) {
      console.error(`- Actual response body: ${JSON.stringify(this.agentResponseBody, null, 2)}`);
    }
    console.log('=== Product Agent Response Content Verification Failed ===');
    throw error;
  }
});

/**
 * Verify the product agent response is grounded in tool results.
 *
 * Current contract expectation:
 * response.answer.grounding.sourceOfTruth === 'tool-results'
 *
 * @param {string} componentName - The component name, e.g. 'pa-1-productagent'
 * @returns {Promise<void>}
 */
Then('the response from the {string} component should be grounded in tool results', async function (componentName) {
  console.log('\n=== Starting Product Agent Grounding Verification ===');
  console.log(`Verifying response from component '${componentName}' is grounded in tool results`);

  try {
    assert.ok(this.agentResponseBody, 'Expected agent response body to be available');
    assert.ok(
      this.agentResponseBody.hasOwnProperty('answer'),
      "Expected response body to contain an 'answer' object"
    );
    assert.ok(
      this.agentResponseBody.answer && this.agentResponseBody.answer.hasOwnProperty('grounding'),
      "Expected response body to contain 'answer.grounding'"
    );
    assert.ok(
      this.agentResponseBody.answer.grounding.hasOwnProperty('sourceOfTruth'),
      "Expected response body to contain 'answer.grounding.sourceOfTruth'"
    );

    const sourceOfTruth = this.agentResponseBody.answer.grounding.sourceOfTruth;
    assert.equal(
      sourceOfTruth,
      'tool-results',
      `Expected grounding sourceOfTruth to be 'tool-results' but found '${sourceOfTruth}'`
    );

    console.log(`✅ Successfully verified response grounding source is 'tool-results'`);
    console.log('=== Product Agent Grounding Verification Complete ===');
  } catch (error) {
    console.error(`❌ Error during Product Agent grounding verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    if (this.agentResponseBody) {
      console.error(`- Actual response body: ${JSON.stringify(this.agentResponseBody, null, 2)}`);
    }
    console.log('=== Product Agent Grounding Verification Failed ===');
    throw error;
  }
});