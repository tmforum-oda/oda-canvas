const config = require('./config');
const logger = require('./logger');
const ExpressServer = require('./expressServer');

const Service = require('./services/Service')
const NotificationHandler = require('./services/NotificationHandler')

const plugins = require('./plugins/plugins')

// const db = require('./plugins/mongoUtils')
// const queue = require('./plugins/kafka')

Service.setDB(plugins.db)
Service.setNotifier(NotificationHandler)

NotificationHandler.setDB(plugins.db)
NotificationHandler.setQueue(plugins.queue)

const launchServer = async () => {
  try {
    this.expressServer = new ExpressServer(config.URL_PORT, config.OPENAPI_YAML);
    await this.expressServer.launch();
    logger.info('Express server running');
  } catch (error) {
    logger.error(error);
    await this.close();
  }
};

launchServer().catch(e => logger.error(e));
