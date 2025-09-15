# TMF639 Resource Inventory Test Suite

This directory contains comprehensive unit and integration tests for the TMF639 Resource Inventory service.

## Test Structure

```
test/
├── fixtures/           # Mock data and expected results
│   ├── mockKubernetesData.js      # Mock ODA Components and ExposedAPIs
│   └── expectedTMFResources.js    # Expected TMF639 Resource format
├── helpers/            # Test utilities and setup
│   └── testSetup.js               # Global test configuration
├── unit/              # Unit tests for individual components
│   ├── KubernetesResourceService.test.js  # Kubernetes integration tests
│   ├── ResourceService.test.js            # Business logic tests  
│   ├── ResourceController.test.js         # Controller layer tests
│   ├── Service.test.js                    # Base service tests
│   └── simple.test.js                     # Basic infrastructure tests
└── integration/       # End-to-end API tests
    └── api.test.js                        # Full API integration tests
```

## Test Coverage

### Unit Tests
- **KubernetesResourceService**: Tests Kubernetes API integration, resource conversion, status mapping
- **ResourceService**: Tests business logic, error handling, TMF639 compliance
- **ResourceController**: Tests HTTP request handling, parameter extraction, response formatting
- **Service Base Class**: Tests common utilities, field filtering, pagination

### Integration Tests
- **API Endpoints**: Tests complete request/response cycle
- **TMF639 Compliance**: Validates output format against TMF639 specification
- **Error Handling**: Tests HTTP status codes and error responses

## Mock Data

The test fixtures include:
- Mock ODA Components (Complete, InProgress, Failed states)
- Mock ExposedAPIs (Ready and NotReady states)
- Expected TMF639 Resource format outputs
- Component-API relationships

## Test Features

✅ **Kubernetes Integration Testing**: Mock Kubernetes API responses  
✅ **TMF639 Format Validation**: Verify output compliance  
✅ **Status Mapping Testing**: Test all component/API status transitions  
✅ **Error Handling**: Test 404, 500, and other error scenarios  
✅ **Field Filtering**: Test query parameter handling  
✅ **Pagination**: Test offset/limit functionality  
✅ **Relationship Mapping**: Test Component-ExposedAPI relationships  
✅ **HTTP Integration**: Test full request/response cycle  

## Running Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests only  
npm run test:integration

# Run with coverage
npm run test:coverage

# Run specific test file
npx mocha test/unit/KubernetesResourceService.test.js
```

## Test Dependencies

- **Mocha**: Test framework
- **Chai**: Assertion library
- **Sinon**: Mocking and stubbing
- **Supertest**: HTTP integration testing
- **NYC**: Code coverage reporting

## Coverage Goals

- Lines: 80%+
- Functions: 80%+  
- Branches: 70%+
- Statements: 80%+