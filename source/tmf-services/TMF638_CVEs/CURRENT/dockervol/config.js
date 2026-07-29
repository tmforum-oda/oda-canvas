const path = require('path')
const fs   = require('fs')

const contents = fs.readFileSync(__dirname + "/config.json")
const jsonConfig = JSON.parse(contents)

const config = {
  ROOT_DIR: __dirname,
  URL_PATH: '',
  URL_PORT: '',
  CONTROLLER_DIRECTORY: path.join(__dirname, 'controllers'),
  OPENAPI_YAML: '',
  EXTERNAL_URL: '',
  SCHEMA_URL: '',
  FILESERVER_PORT: 3000,

  DEFAULT_FILTERING_FIELDS: { id: 1, href: 1, '@type': 1 },
  DEFAULT_FILTERING_FIELDS_KEYS: [ 'id', 'href', '@type' ],

  TOPIC: 'event',
  HUB: 'EventsSubscription',
  SUBSCRIPTION: 'subscription',
  INTERNAL_EVENT: 'ri-internal-event',

  MONITOR: 'Monitor',
  MONITOR_PATH: 'monitor',
  ASYNC_HEADER: 'run_async'

}

// import all properties from the config.json
Object.keys(jsonConfig).forEach(key => {
  config[key] = jsonConfig[key]
})

// we need to either build the URL_PATH on the way in OR set the URL_PATH to include the API's url
if (config.apiUrl && String(config.apiUrl).length > 0) {
  config.URL_PATH = config.apiUrl
  config.EXTERNAL_URL = config.apiUrl
} else {
  throw new Error('Missing required configuration value: apiUrl');
}

if (config.exposedPort && String(config.exposedPort).length > 0) {
  config.URL_PORT = config.exposedPort
} else {
  throw new Error('Missing required configuration value: exposedPort');
}

config.OPENAPI_YAML = path.join(config.ROOT_DIR, 'api', 'openapi.yaml')

if(config.apiNum && String(config.apiNum).length > 0) {
  config.SUBSCRIPTION   = `${config.apiNum}-${config.SUBSCRIPTION}`,
  config.INTERNAL_EVENT =`${config.apiNum}-${config.INTERNAL_EVENT}`
} else {
  throw new Error('Missing required configuration value: apiNum');
}

module.exports = config;
