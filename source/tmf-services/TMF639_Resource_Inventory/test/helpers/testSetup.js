const sinon = require('sinon');
const chai = require('chai');
const sinonChai = require('sinon-chai');

// Configure chai
chai.use(sinonChai);

// Global test setup
beforeEach(function() {
  // Reset sinon stubs before each test
  sinon.restore();
});

// Helper function to create mock Kubernetes API responses
function createMockKubernetesResponse(items = []) {
  return {
    body: {
      items: items
    }
  };
}

// Helper function to create mock single resource response
function createMockSingleResourceResponse(resource) {
  return {
    body: resource
  };
}

// Helper function to create 404 error
function createNotFoundError() {
  const error = new Error('Not found');
  error.response = { statusCode: 404 };
  return error;
}

// Helper function to create generic API error
function createApiError(message = 'API Error', statusCode = 500) {
  const error = new Error(message);
  error.response = { statusCode };
  return error;
}

module.exports = {
  createMockKubernetesResponse,
  createMockSingleResourceResponse,
  createNotFoundError,
  createApiError
};