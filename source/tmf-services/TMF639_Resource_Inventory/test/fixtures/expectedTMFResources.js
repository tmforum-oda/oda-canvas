const expectedComponentResource = {
  id: 'test-component',
  href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component',
  '@type': 'LogicalResource',
  '@baseType': 'Resource',
  name: 'test-component',
  description: 'Test ODA Component for unit testing',
  category: 'ODAComponent',
  resourceSpecification: {
    '@type': 'ResourceSpecificationRef',
    id: 'ODAComponent',
    name: 'microservice',
    version: '1.0.0'
  },
  resourceCharacteristic: [
    {
      '@type': 'Characteristic',
      name: 'namespace',
      value: 'components'
    },
    {
      '@type': 'Characteristic',
      name: 'deploymentStatus',
      value: 'Complete'
    },
    {
      '@type': 'Characteristic',
      name: 'id',
      value: 'TEST001'
    },
    {
      '@type': 'Characteristic',
      name: 'name',
      value: 'testcomponent'
    },
    {
      '@type': 'Characteristic',
      name: 'functionalBlock',
      value: 'CoreCommerce'
    },
    {
      '@type': 'Characteristic',
      name: 'status',
      value: 'specified'
    },
    {
      '@type': 'Characteristic',
      name: 'publicationDate',
      value: '2024-01-15T00:00:00.000Z'
    },
    {
      '@type': 'Characteristic',
      name: 'maintainers',
      value: [
        {
          name: 'Test Developer',
          email: 'test@example.com'
        }
      ]
    },
    {
      '@type': 'Characteristic',
      name: 'owners',
      value: [
        {
          name: 'Test Owner',
          email: 'owner@example.com'
        }
      ]
    }
  ],
  resourceStatus: 'available',
  operationalState: 'enable',
  administrativeState: 'unlocked',
  usageState: 'active',
  startDate: '2024-01-15T10:30:00Z',
  place: [{
    id: 'components',
    name: 'components',
    '@type': 'Namespace'
  }],
  relatedResource: [
    {
      '@type': 'ResourceRef',
      id: 'test-component-api',
      href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component-api',
      name: 'test-component-api',
      '@referredType': 'LogicalResource',
      category: 'API',
      relationshipType: 'exposes'
    },
    {
      '@type': 'ResourceRef',
      id: 'test-component-metrics',
      href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component-metrics',
      name: 'test-component-metrics',
      '@referredType': 'LogicalResource',
      category: 'API',
      relationshipType: 'exposes'
    }
  ]
};

const expectedAPIResource = {
  id: 'test-component-api',
  href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component-api',
  '@type': 'LogicalResource',
  '@baseType': 'Resource',
  name: 'test-component-api',
  description: 'Exposed API: testapi',
  category: 'API',
  resourceSpecification: {
    '@type': 'ResourceSpecificationRef',
    id: 'API',
    name: 'API'
  },
  resourceCharacteristic: [
    {
      '@type': 'Characteristic',
      name: 'namespace',
      value: 'components'
    },
    {
      '@type': 'Characteristic',
      name: 'apiName',
      value: 'testapi'
    },
    {
      '@type': 'Characteristic',
      name: 'url',
      value: 'https://localhost/test-component/api/v1'
    },
    {
      '@type': 'Characteristic',
      name: 'implementation',
      value: 'test-api-service'
    },
    {
      '@type': 'Characteristic',
      name: 'specification',
      value: [
        {
          url: 'https://example.com/api/test-v1.0.0.yaml'
        }
      ]
    },
    {
      '@type': 'Characteristic',
      name: 'apiDocs',
      value: 'https://localhost/test-component/api/v1/docs'
    }
  ],
  resourceStatus: 'available',
  operationalState: 'enable',
  administrativeState: 'unlocked',
  usageState: 'active',
  startDate: '2024-01-15T10:35:00Z',
  place: [{
    id: 'components',
    name: 'components',
    '@type': 'Namespace'
  }],
  relatedResource: [
    {
      '@type': 'ResourceRef',
      id: 'test-component',
      href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component',
      name: 'test-component',
      '@referredType': 'LogicalResource',
      category: 'ODAComponent',
      relationshipType: 'exposedBy'
    }
  ]
};

const expectedInProgressComponentResource = {
  id: 'test-component-installing',
  href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component-installing',
  '@type': 'LogicalResource',
  '@baseType': 'Resource',
  name: 'test-component-installing',
  description: 'Test component in installation progress',
  category: 'ODAComponent',
  resourceSpecification: {
    '@type': 'ResourceSpecificationRef',
    id: 'ODAComponent',
    name: 'microservice',
    version: '0.9.0'
  },
  resourceStatus: 'installing',
  operationalState: 'enable',
  administrativeState: 'unlocked',
  usageState: 'active',
  startDate: '2024-01-15T11:00:00Z',
  place: [{
    id: 'components',
    name: 'components',
    '@type': 'Namespace'
  }],
  relatedResource: []
};

const expectedFailedComponentResource = {
  id: 'test-component-failed',
  href: '/tmf-api/resourceInventoryManagement/v5/resource/test-component-failed',
  '@type': 'LogicalResource',
  '@baseType': 'Resource',
  name: 'test-component-failed',
  description: 'Test component with failed deployment',
  category: 'ODAComponent',
  resourceSpecification: {
    '@type': 'ResourceSpecificationRef',
    id: 'ODAComponent',
    name: 'microservice',
    version: '0.8.0'
  },
  resourceStatus: 'reserved',
  operationalState: 'disable',
  administrativeState: 'unlocked',
  usageState: 'active',
  startDate: '2024-01-15T11:30:00Z',
  place: [{
    id: 'components',
    name: 'components',
    '@type': 'Namespace'
  }],
  relatedResource: []
};

module.exports = {
  expectedComponentResource,
  expectedAPIResource,
  expectedInProgressComponentResource,
  expectedFailedComponentResource
};