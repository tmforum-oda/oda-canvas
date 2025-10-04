const { expect } = require('chai');
const sinon = require('sinon');
const sinonChai = require('sinon-chai');
const chai = require('chai');

chai.use(sinonChai);

const ResourceController = require('../../controllers/ResourceController');
const ResourceService = require('../../services/ResourceService');
const Controller = require('../../controllers/Controller');

describe('ResourceController', () => {
  let mockRequest, mockResponse, mockService;

  beforeEach(() => {
    mockRequest = {
      params: { id: 'test-resource' },
      openapi: {
        pathParams: { id: 'test-resource' },
        schema: {
          parameters: [{ name: 'id', in: 'path' }]
        }
      },
      query: {},
      body: {}
    };

    mockResponse = {
      status: sinon.stub().returnsThis(),
      json: sinon.stub(),
      end: sinon.stub(),
      setHeader: sinon.stub()
    };

    // Mock ResourceService methods
    mockService = {
      listResource: sinon.stub(),
      retrieveResource: sinon.stub()
    };
  });

  afterEach(() => {
    sinon.restore();
  });

  describe('listResource', () => {
    it('should handle successful list request', async () => {
      const mockServiceResponse = {
        code: 200,
        payload: [
          {
            id: 'resource1',
            name: 'Test Resource 1',
            category: 'ODAComponent'
          },
          {
            id: 'resource2',
            name: 'Test Resource 2',
            category: 'API'
          }
        ]
      };

      // Mock Controller.handleRequest to simulate successful service call
      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      // Mock ResourceService.listResource
      const listResourceStub = sinon.stub(ResourceService, 'listResource').resolves(mockServiceResponse);

      await ResourceController.listResource(mockRequest, mockResponse);

      expect(handleRequestStub).to.have.been.calledWith(
        mockRequest,
        mockResponse,
        ResourceService.listResource
      );
      
      handleRequestStub.restore();
      listResourceStub.restore();
    });

    it('should handle service errors in list request', async () => {
      const mockServiceError = {
        code: 500,
        payload: 'Internal server error'
      };

      // Mock Controller.handleRequest to simulate service error
      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      // Mock ResourceService.listResource to return error
      const listResourceStub = sinon.stub(ResourceService, 'listResource').resolves(mockServiceError);

      await ResourceController.listResource(mockRequest, mockResponse);

      expect(handleRequestStub).to.have.been.calledOnce;
      
      handleRequestStub.restore();
      listResourceStub.restore();
    });

    it('should pass request parameters to service', async () => {
      mockRequest.query = {
        fields: 'id,name,category',
        offset: '0',
        limit: '10'
      };

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          // Verify that Controller.collectRequestParams is called
          const params = Controller.collectRequestParams(request);
          expect(params).to.have.property('dynamic');
          expect(params.dynamic).to.deep.include({
            fields: 'id,name,category',
            offset: '0',
            limit: '10'
          });
          
          const result = await serviceOperation(params, { request });
          Controller.sendResponse(response, result);
        }
      );

      const listResourceStub = sinon.stub(ResourceService, 'listResource').resolves({
        code: 200,
        payload: []
      });

      await ResourceController.listResource(mockRequest, mockResponse);

      expect(handleRequestStub).to.have.been.calledOnce;
      
      handleRequestStub.restore();
      listResourceStub.restore();
    });
  });

  describe('retrieveResource', () => {
    it('should handle successful retrieve request', async () => {
      const mockServiceResponse = {
        code: 200,
        payload: {
          id: 'test-resource',
          name: 'Test Resource',
          category: 'ODAComponent'
        }
      };

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves(mockServiceResponse);

      await ResourceController.retrieveResource(mockRequest, mockResponse);

      expect(handleRequestStub).to.have.been.calledWith(
        mockRequest,
        mockResponse,
        ResourceService.retrieveResource
      );
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });

    it('should handle resource not found', async () => {
      const mockServiceResponse = {
        code: 404,
        payload: 'Resource with id test-resource not found'
      };

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves(mockServiceResponse);

      await ResourceController.retrieveResource(mockRequest, mockResponse);

      expect(handleRequestStub).to.have.been.calledOnce;
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });

    it('should handle missing openapi object', async () => {
      // Remove openapi from request
      delete mockRequest.openapi;

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          // Verify that the controller sets up openapi object
          expect(request.openapi).to.be.an('object');
          expect(request.openapi.pathParams).to.deep.equal({ id: 'test-resource' });
          expect(request.openapi.schema).to.be.an('object');
          
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves({
        code: 200,
        payload: { id: 'test-resource' }
      });

      await ResourceController.retrieveResource(mockRequest, mockResponse);

      expect(mockRequest.openapi).to.exist;
      expect(mockRequest.openapi.pathParams.id).to.equal('test-resource');
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });

    it('should extract ID from request params', async () => {
      mockRequest.params.id = 'custom-resource-id';
      delete mockRequest.openapi;

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          expect(request.openapi.pathParams.id).to.equal('custom-resource-id');
          
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves({
        code: 200,
        payload: { id: 'custom-resource-id' }
      });

      await ResourceController.retrieveResource(mockRequest, mockResponse);
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });

    it('should handle missing ID parameter', async () => {
      delete mockRequest.params.id;
      delete mockRequest.openapi;

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          expect(request.openapi.pathParams.id).to.be.undefined;
          
          const result = await serviceOperation();
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves({
        code: 500,
        payload: 'Missing resource ID'
      });

      await ResourceController.retrieveResource(mockRequest, mockResponse);
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });

    it('should pass fields parameter to service', async () => {
      mockRequest.query.fields = 'id,name,category';

      const handleRequestStub = sinon.stub(Controller, 'handleRequest').callsFake(
        async (request, response, serviceOperation) => {
          const params = Controller.collectRequestParams(request);
          expect(params).to.have.property('dynamic');
          expect(params.dynamic.fields).to.equal('id,name,category');
          
          const result = await serviceOperation(params, { request });
          Controller.sendResponse(response, result);
        }
      );

      const retrieveResourceStub = sinon.stub(ResourceService, 'retrieveResource').resolves({
        code: 200,
        payload: { id: 'test-resource', name: 'Test', category: 'ODAComponent' }
      });

      await ResourceController.retrieveResource(mockRequest, mockResponse);
      
      handleRequestStub.restore();
      retrieveResourceStub.restore();
    });
  });

  describe('error handling', () => {
    it('should handle Controller.handleRequest errors in listResource', async () => {
      const error = new Error('Controller error');
      const handleRequestStub = sinon.stub(Controller, 'handleRequest').throws(error);

      try {
        await ResourceController.listResource(mockRequest, mockResponse);
        expect.fail('Should have thrown an error');
      } catch (err) {
        expect(err).to.equal(error);
      }
      
      handleRequestStub.restore();
    });

    it('should handle Controller.handleRequest errors in retrieveResource', async () => {
      const error = new Error('Controller error');
      const handleRequestStub = sinon.stub(Controller, 'handleRequest').throws(error);

      try {
        await ResourceController.retrieveResource(mockRequest, mockResponse);
        expect.fail('Should have thrown an error');
      } catch (err) {
        expect(err).to.equal(error);
      }
      
      handleRequestStub.restore();
    });
  });

  describe('module exports', () => {
    it('should export listResource function', () => {
      expect(ResourceController).to.have.property('listResource');
      expect(ResourceController.listResource).to.be.a('function');
    });

    it('should export retrieveResource function', () => {
      expect(ResourceController).to.have.property('retrieveResource');
      expect(ResourceController.retrieveResource).to.be.a('function');
    });

    it('should only export expected functions', () => {
      const exportedKeys = Object.keys(ResourceController);
      expect(exportedKeys).to.have.length(2);
      expect(exportedKeys).to.include('listResource');
      expect(exportedKeys).to.include('retrieveResource');
    });
  });
});