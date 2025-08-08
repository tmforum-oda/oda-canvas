const mockODAComponent = {
  metadata: {
    name: 'test-component',
    namespace: 'components',
    labels: {
      'app.kubernetes.io/name': 'test-component'
    },
    creationTimestamp: '2024-01-15T10:30:00Z'
  },
  spec: {
    type: 'microservice',
    version: '1.0.0',
    description: 'Test ODA Component for unit testing',
    componentMetadata: {
      id: 'TEST001',
      name: 'testcomponent',
      functionalBlock: 'CoreCommerce',
      status: 'specified',
      publicationDate: '2024-01-15T00:00:00.000Z',
      maintainers: [
        {
          name: 'Test Developer',
          email: 'test@example.com'
        }
      ],
      owners: [
        {
          name: 'Test Owner',
          email: 'owner@example.com'
        }
      ]
    }
  },
  status: {
    deployment_status: 'Complete',
    summary: {
      status: 'Complete',
      message: 'Component deployed successfully'
    }
  }
};

const mockExposedAPI = {
  metadata: {
    name: 'test-component-api',
    namespace: 'components',
    labels: {
      'oda.tmforum.org/componentName': 'test-component'
    },
    creationTimestamp: '2024-01-15T10:35:00Z'
  },
  spec: {
    name: 'testapi',
    implementation: 'test-api-service',
    specification: [
      {
        url: 'https://example.com/api/test-v1.0.0.yaml'
      }
    ]
  },
  status: {
    implementation: {
      ready: true
    },
    apiStatus: {
      url: 'https://localhost/test-component/api/v1',
      developerUI: 'https://localhost/test-component/api/v1/docs'
    }
  }
};

const mockExposedAPINotReady = {
  metadata: {
    name: 'test-component-metrics',
    namespace: 'components',
    labels: {
      'oda.tmforum.org/componentName': 'test-component'
    },
    creationTimestamp: '2024-01-15T10:36:00Z'
  },
  spec: {
    name: 'metrics',
    implementation: 'test-metrics-service'
  },
  status: {
    implementation: {
      ready: false
    },
    apiStatus: {
      url: 'https://localhost/test-component/metrics'
    }
  }
};

const mockComponentInProgress = {
  metadata: {
    name: 'test-component-installing',
    namespace: 'components',
    creationTimestamp: '2024-01-15T11:00:00Z'
  },
  spec: {
    type: 'microservice',
    version: '0.9.0',
    description: 'Test component in installation progress'
  },
  status: {
    deployment_status: 'InProgress',
    summary: {
      status: 'InProgress',
      message: 'Installation in progress'
    }
  }
};

const mockComponentFailed = {
  metadata: {
    name: 'test-component-failed',
    namespace: 'components',
    creationTimestamp: '2024-01-15T11:30:00Z'
  },
  spec: {
    type: 'microservice',
    version: '0.8.0',
    description: 'Test component with failed deployment'
  },
  status: {
    deployment_status: 'Failed',
    summary: {
      status: 'Failed',
      message: 'Deployment failed due to resource constraints'
    }
  }
};

module.exports = {
  mockODAComponent,
  mockExposedAPI,
  mockExposedAPINotReady,
  mockComponentInProgress,
  mockComponentFailed
};