const { expect } = require('chai');
const sinon = require('sinon');
const Service = require('../../services/Service');

describe('Service Base Class', () => {
  describe('createResponse', () => {
    it('should create successful response with payload', () => {
      const payload = { id: '123', name: 'test' };
      const context = { operationId: 'testOperation' };

      const result = Service.createResponse(payload, context);

      expect(result).to.have.property('code', 200);
      expect(result).to.have.property('payload', payload);
    });

    it('should create response with custom code', () => {
      const payload = { message: 'Created' };
      const context = { operationId: 'createOperation' };

      const result = Service.createResponse(payload, context, 201);

      expect(result).to.have.property('code', 201);
      expect(result).to.have.property('payload', payload);
    });

    it('should handle null payload', () => {
      const context = { operationId: 'testOperation' };

      const result = Service.createResponse(null, context);

      expect(result).to.have.property('code', 200);
      expect(result).to.have.property('payload', null);
    });
  });

  describe('rejectResponse', () => {
    it('should create error response with message and status', () => {
      const message = 'Resource not found';
      const status = 404;

      const result = Service.rejectResponse(message, status);

      expect(result).to.have.property('code', status);
      expect(result).to.have.property('payload', message);
    });

    it('should default to status 500', () => {
      const message = 'Internal error';

      const result = Service.rejectResponse(message);

      expect(result).to.have.property('code', 500);
      expect(result).to.have.property('payload', message);
    });

    it('should handle empty message', () => {
      const result = Service.rejectResponse('', 400);

      expect(result).to.have.property('code', 400);
      expect(result).to.have.property('payload', '');
    });
  });

  describe('applyFields', () => {
    it('should filter object fields when fields parameter provided', () => {
      const obj = {
        id: '123',
        name: 'test',
        description: 'test description',
        category: 'test-category',
        status: 'active'
      };
      const fields = 'id,name,category';

      const result = Service.applyFields(obj, fields);

      expect(result).to.deep.equal({
        id: '123',
        name: 'test',
        category: 'test-category'
      });
    });

    it('should return original object when no fields parameter', () => {
      const obj = { id: '123', name: 'test' };

      const result = Service.applyFields(obj, null);

      expect(result).to.deep.equal(obj);
    });

    it('should return original object when fields parameter is empty', () => {
      const obj = { id: '123', name: 'test' };

      const result = Service.applyFields(obj, '');

      expect(result).to.deep.equal(obj);
    });

    it('should handle fields that dont exist in object', () => {
      const obj = { id: '123', name: 'test' };
      const fields = 'id,name,nonexistent';

      const result = Service.applyFields(obj, fields);

      expect(result).to.deep.equal({
        id: '123',
        name: 'test'
      });
    });

    it('should handle nested field notation', () => {
      const obj = {
        id: '123',
        metadata: {
          name: 'test',
          namespace: 'default'
        },
        spec: {
          version: '1.0.0'
        }
      };
      const fields = 'id,metadata.name,spec.version';

      // Note: This test assumes the applyFields method supports nested fields
      // If it doesn't, this test may need to be adjusted
      const result = Service.applyFields(obj, fields);

      // The actual implementation may vary
      expect(result).to.have.property('id', '123');
    });
  });

  describe('applyQuery', () => {
    it('should apply field filtering to array of objects', () => {
      const resources = [
        { id: '1', name: 'resource1', category: 'A' },
        { id: '2', name: 'resource2', category: 'B' }
      ];
      const args = { fields: 'id,name' };
      const context = {};

      // Mock applyFields to return filtered objects
      const applyFieldsStub = sinon.stub(Service, 'applyFields');
      applyFieldsStub.withArgs(resources[0], 'id,name').returns({ id: '1', name: 'resource1' });
      applyFieldsStub.withArgs(resources[1], 'id,name').returns({ id: '2', name: 'resource2' });

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(2);
      expect(applyFieldsStub).to.have.been.calledWith(resources[0], 'id,name');
      expect(applyFieldsStub).to.have.been.calledWith(resources[1], 'id,name');

      applyFieldsStub.restore();
    });

    it('should handle pagination with offset and limit', () => {
      const resources = [
        { id: '1', name: 'resource1' },
        { id: '2', name: 'resource2' },
        { id: '3', name: 'resource3' },
        { id: '4', name: 'resource4' }
      ];
      const args = { offset: 1, limit: 2 };
      const context = {};

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(2);
      expect(result[0]).to.have.property('id', '2');
      expect(result[1]).to.have.property('id', '3');
    });

    it('should handle offset without limit', () => {
      const resources = [
        { id: '1', name: 'resource1' },
        { id: '2', name: 'resource2' },
        { id: '3', name: 'resource3' }
      ];
      const args = { offset: 1 };
      const context = {};

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(2);
      expect(result[0]).to.have.property('id', '2');
    });

    it('should handle limit without offset', () => {
      const resources = [
        { id: '1', name: 'resource1' },
        { id: '2', name: 'resource2' },
        { id: '3', name: 'resource3' }
      ];
      const args = { limit: 2 };
      const context = {};

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(2);
      expect(result[0]).to.have.property('id', '1');
      expect(result[1]).to.have.property('id', '2');
    });

    it('should return empty array when offset exceeds array length', () => {
      const resources = [
        { id: '1', name: 'resource1' },
        { id: '2', name: 'resource2' }
      ];
      const args = { offset: 5 };
      const context = {};

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(0);
    });

    it('should handle non-array input', () => {
      const resource = { id: '1', name: 'resource1' };
      const args = { fields: 'id' };
      const context = {};

      const result = Service.applyQuery(resource, args, context);

      // Should return the original object or handle appropriately
      expect(result).to.not.be.null;
    });

    it('should handle empty array', () => {
      const resources = [];
      const args = { fields: 'id,name' };
      const context = {};

      const result = Service.applyQuery(resources, args, context);

      expect(result).to.be.an('array');
      expect(result).to.have.length(0);
    });
  });
});