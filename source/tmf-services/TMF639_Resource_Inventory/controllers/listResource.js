const ResourceController = require('./ResourceController');
const logger = require('../logger');

logger.info('Loading listResource controller');
logger.debug('ResourceController.listResource:', typeof ResourceController.listResource);

module.exports = ResourceController.listResource;
