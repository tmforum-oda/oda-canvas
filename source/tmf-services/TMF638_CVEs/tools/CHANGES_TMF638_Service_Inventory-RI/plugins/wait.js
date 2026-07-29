const logger   = require('../logger')
const waitOn = require('wait-on');

const TIMEOUT  = 60000
const INTERVAL = 10000

async function waitForPlugins(plugins) {

    const opts = {
        resources: [
          `tcp:${plugins.queue.getHost()}:${plugins.queue.getPort()}`,
          `tcp:${plugins.db.getHost()}:${plugins.db.getPort()}`
        ],
        delay: 1000, // initial delay in ms
        interval: 5000, // poll interval in ms
        simultaneous: 1, // limit to 1 connection per resource at a time
        timeout: 180000, // timeout in ms
        tcpTimeout: 1000, // tcp timeout in ms
        window: 1000, // stabilization time in ms
        verbose: true
    }

    logger.info("waitForPlugins: resources=" + JSON.stringify(opts.resources))
    
    try {
        await waitOn(opts);
    } catch (err) {
        logger.error(`Error: ${err}`)
        process.exit(1)    
    }
 
}

module.exports = { waitForPlugins }