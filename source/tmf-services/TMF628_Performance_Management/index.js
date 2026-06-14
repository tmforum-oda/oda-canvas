const config = require('./config');
const logger = require('./logger');
const ExpressServer = require('./expressServer');

const launchServer = async () => {
  try {
    this.expressServer = new ExpressServer(config.URL_PORT, config.OPENAPI_YAML);
    await this.expressServer.launch();
    logger.info('TMF628 Performance Management Express server running');
  } catch (error) {
    logger.error(error);
    await this.close();
  }
};


launchServer().catch(e => logger.error(e));
