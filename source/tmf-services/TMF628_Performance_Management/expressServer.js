const http = require('http');
const fs = require('fs');
const path = require('path');
const swaggerUI = require('swagger-ui-express');
const jsYaml = require('js-yaml');
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const OpenApiValidator = require('express-openapi-validator');
const logger = require('./logger');
const config = require('./config');

const cleanPath = (path) => path.replace(/\/\//,'/');

class ExpressServer {
  constructor(port, openApiYaml) {
    this.port = port;
    this.app = express();
    this.openApiPath = openApiYaml;
    try {
      this.schema = jsYaml.load(fs.readFileSync(openApiYaml));
    } catch (e) {
      logger.error('failed to start TMF628 Performance Management Express Server', e.message);
    }

    this.setupMiddleware();
  }

  setupMiddleware() {
    const basePath = '/tmf-api/performance/v5';
    logger.info(`TMF628 Performance Management basePath: ${basePath}`);
    
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: false }));
    this.app.use(cookieParser());
    
    // Simple test to see that the server is up and responding
    this.app.get('/hello', (req, res) => res.send(`Hello World. TMF628 Performance Management - path: ${this.openApiPath}`));
    
    const openapi = config.OPENAPI || '/openapi';

    // Send the openapi document
    this.app.get(cleanPath(`${basePath}${openapi}`), (req, res) => res.sendFile((path.join(__dirname, 'api', 'TMF628-Performance-v5.0.0.oas.yaml'))));

    // View the openapi document in a visual interface
    this.app.use(cleanPath(`${basePath}/api-docs`), swaggerUI.serve, swaggerUI.setup(this.schema));

    // Redirects
    this.app.get(`${openapi}`, function(req, res) {
      res.redirect(cleanPath(`${basePath}${openapi}`));
    });

    this.app.get('/api-docs', function(req, res) {
      res.redirect(cleanPath(`${basePath}/api-docs`));
    });

    this.app.get('/', function(req, res) {
      res.send('TMF628 Carbon Intensity Performance Management API is running');
    });
  }

  launch() {
    try {
      const SOURCE_DATE_EPOCH = process.env.SOURCE_DATE_EPOCH;
      const GIT_COMMIT_SHA = process.env.GIT_COMMIT_SHA;
      const CICD_BUILD_TIME = process.env.CICD_BUILD_TIME;
      if (SOURCE_DATE_EPOCH) {
        logger.info(`SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}`);
      }
      if (GIT_COMMIT_SHA) {
        logger.info(`GIT_COMMIT_SHA=${GIT_COMMIT_SHA}`);
      }
      if (CICD_BUILD_TIME) {
        logger.info(`CICD_BUILD_TIME=${CICD_BUILD_TIME}`);
      }
      
      // Add middleware to log all requests for debugging
      this.app.use((req, res, next) => {
        logger.info(`Request: ${req.method} ${req.path} - URL: ${req.url}`);
        next();
      });
      
      logger.info('Loading OpenApiValidator with apiSpec:', this.openApiPath);
      
      // Create a router for TMF628 basepath
      const tmfRouter = express.Router();
      
      // OpenAPI Validator
      tmfRouter.use(OpenApiValidator.middleware({
        apiSpec: this.openApiPath,
        validateRequests: true,
        validateResponses: true,
        unknownFormats: ['base64']
      }));
      
      // Load controllers and set up routes
      const controllers = require('./controllers');
      
      // Standard TMF628 GET operations
      tmfRouter.get('/performanceMeasurement', controllers.PerformanceMeasurementController.listPerformanceMeasurement);
      tmfRouter.get('/performanceMeasurement/:id', controllers.PerformanceMeasurementController.retrievePerformanceMeasurement);
      
      // Extended operation for dynamic data updates (non-standard TMF628)
      tmfRouter.patch('/performanceMeasurement/:id', controllers.PerformanceMeasurementController.updatePerformanceMeasurement);
      
      // Admin endpoints for data management
      tmfRouter.post('/admin/reload', controllers.PerformanceMeasurementController.reloadDataFromFile);
      tmfRouter.get('/admin/stats', controllers.PerformanceMeasurementController.getDataStatistics);
      
      logger.info('Registered routes:');
      logger.info('  GET    /performanceMeasurement       - List all measurements');
      logger.info('  GET    /performanceMeasurement/:id   - Get measurement by ID');
      logger.info('  PATCH  /performanceMeasurement/:id   - Update measurement fields');
      logger.info('  POST   /admin/reload                 - Reload data from file');
      logger.info('  GET    /admin/stats                  - Get data statistics');
      
      // Error handler for router
      tmfRouter.use((err, req, res, next) => {
        res.status(err.status || 500).json({
          message: err.message || err,
          errors: err.errors || '',
        });
      });
      
      // Mount the router at the TMF628 basepath
      this.app.use('/tmf-api/performance/v5', tmfRouter);
      logger.info(`TMF628 Performance Management validator installed`);
  
      // Global error handler
      this.app.use((err, req, res, next) => {
        res.status(err.status || 500).json({
          message: err.message || err,
          errors: err.errors || '',
        });
      });

      logger.info(`Starting server...`);
      http.createServer(this.app).listen(this.port);
      logger.info(`Express server listening on port ${this.port}`);
    } catch (error) {
      logger.error(error);
      throw error;
    }
  }

  async close() {
    if (this.server !== undefined) {
      await this.server.close();
      logger.info(`Server on port ${this.port} shut down`);
    }
  }
}

module.exports = ExpressServer;
