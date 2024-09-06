'use strict';

const plugins = {}
plugins.db = require('./mongo')
// deactivate kafka, as it is not used in the canvas reference implementation
// plugins.queue = require('./kafka')

const { waitForPlugins } = require('./wait')

plugins.waitForPlugins = async () => { await waitForPlugins(plugins) }

module.exports = plugins
