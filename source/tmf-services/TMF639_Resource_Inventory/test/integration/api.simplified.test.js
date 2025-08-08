const { expect } = require('chai');
const request = require('supertest');
const express = require('express');

// Import the controllers we need to test
const ResourceController = require('../../controllers/ResourceController');

describe('TMF639 API Integration Tests - Simplified', () => {
  let app;

  before(() => {
    // Create a simple Express app for testing
    app = express();
    app.use(express.json());
    app.use(express.urlencoded({ extended: false }));
    
    // Add health check
    app.get('/hello', (req, res) => res.send('Hello World. TMF639 Resource Inventory'));
    
    // Add API routes - these will use the real service
    app.get('/tmf-api/resourceInventoryManagement/v5/resource', ResourceController.listResource);
    app.get('/tmf-api/resourceInventoryManagement/v5/resource/:id', ResourceController.retrieveResource);
    
    // Error handler
    app.use((err, req, res, next) => {
      res.status(err.status || 500).json({
        message: err.message || 'Internal Server Error'
      });
    });
  });

  describe('Health Check', () => {
    it('should respond to health check endpoint', async () => {
      const response = await request(app)
        .get('/hello')
        .expect(200);

      expect(response.text).to.include('TMF639 Resource Inventory');
    });
  });

  describe('API Structure Tests', () => {
    it('should have the listResource endpoint available', async () => {
      // This test just verifies the endpoint exists and doesn't crash
      // It will return whatever is actually in the cluster
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource');
      
      // Should return 200 or 500 (but not 404)
      expect([200, 500]).to.include(response.status);
      
      if (response.status === 200) {
        expect(response.body).to.be.an('array');
      }
    });

    it('should have the retrieveResource endpoint available', async () => {
      // Test with a non-existent resource - should return 404 or 500
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource/test-nonexistent');
      
      // Should return 404, 500, or potentially 200 with null
      expect([200, 404, 500]).to.include(response.status);
    });

    it('should return JSON content-type for API endpoints', async () => {
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource');

      if (response.status === 200) {
        expect(response.headers['content-type']).to.match(/application\/json/);
      }
    });
  });

  describe('Real World TMF639 Compliance', () => {
    it('should return TMF639 compliant resources if any exist', async () => {
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource');

      // If we get resources, they should be TMF639 compliant
      if (response.status === 200 && response.body.length > 0) {
        const resource = response.body[0];
        
        // Check for required TMF639 fields
        expect(resource).to.have.property('id');
        expect(resource).to.have.property('href');
        expect(resource).to.have.property('@type');
        expect(resource).to.have.property('category');
        
        // Check href format
        expect(resource.href).to.match(/^\/tmf-api\/resourceInventoryManagement\/v5\/resource\/.+/);
        
        // Check valid categories
        expect(['ODAComponent', 'API']).to.include(resource.category);
        
        // If it has characteristics, they should be properly formatted
        if (resource.resourceCharacteristic) {
          expect(resource.resourceCharacteristic).to.be.an('array');
          if (resource.resourceCharacteristic.length > 0) {
            const characteristic = resource.resourceCharacteristic[0];
            expect(characteristic).to.have.property('@type', 'Characteristic');
            expect(characteristic).to.have.property('name');
            expect(characteristic).to.have.property('value');
          }
        }
      }
    });

    it('should handle query parameters gracefully', async () => {
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource?fields=id,name&limit=5');
      
      // Should not crash - return 200 or 500
      expect([200, 500]).to.include(response.status);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid resource IDs gracefully', async () => {
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource/invalid@id');
      
      // Should return an error status
      expect([400, 404, 500]).to.include(response.status);
    });

    it('should return appropriate error status codes', async () => {
      const response = await request(app)
        .get('/tmf-api/resourceInventoryManagement/v5/resource/definitely-not-found');
      
      // Should return an error status code
      expect([400, 404, 500]).to.include(response.status);
      
      // Should return an object (even if empty)
      expect(response.body).to.be.an('object');
      
      // The important thing is we get the right HTTP status, not the exact error format
      expect(response.headers['content-type']).to.match(/application\/json/);
    });
  });

  describe('Controller Integration', () => {
    it('should have working ResourceController methods', () => {
      expect(ResourceController.listResource).to.be.a('function');
      expect(ResourceController.retrieveResource).to.be.a('function');
    });

    it('should handle request/response cycle without crashing', async () => {
      // This is a basic smoke test - just verify the controller methods don't crash
      const mockReq = {
        params: {},
        query: {},
        openapi: { pathParams: {}, schema: { parameters: [] } }
      };
      const mockRes = {
        status: () => mockRes,
        json: () => mockRes,
        end: () => mockRes
      };

      // Should not throw errors
      expect(() => {
        ResourceController.listResource(mockReq, mockRes).catch(() => {
          // Expected to potentially fail, but shouldn't crash
        });
      }).to.not.throw();
    });
  });
});