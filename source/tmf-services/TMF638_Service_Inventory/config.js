const path = require('path')
const fs   = require('fs')

const contents = fs.readFileSync(__dirname + "/config.json")
const jsonConfig = JSON.parse(contents)

const SERVER_URL = process.env.SERVER_URL
if (SERVER_URL) {
  jsonConfig["servers"][0]["url"] = SERVER_URL
}

const config = {
  ROOT_DIR: __dirname,
  URL_PORT: 8638,
  URL_PATH: 'http://info.canvas.svc.cluster.local/tmf-api/serviceInventoryManagement/v5',
  
  BASE_VERSION: 'v5',
  CONTROLLER_DIRECTORY: path.join(__dirname, 'controllers'),
  OPENAPI_YAML: '',
  FULL_PATH: '',
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

config.OPENAPI_YAML   = path.join(config.ROOT_DIR, 'api', 'openapi.yaml')
config.FULL_PATH      =  `${config.URL_PATH}:${config.URL_PORT}/${config.BASE_VERSION}`
config.EXTERNAL_URL   = config.FULL_PATH

if(jsonConfig.servers && jsonConfig.servers.length>0) {
  config.EXTERNAL_URL = jsonConfig.servers[0].url;
} 

// import all properties from the config.json
Object.keys(jsonConfig).forEach(key => {
  config[key] = jsonConfig[key]
})

if(config.tmfid) {
  config.SUBSCRIPTION   = `${config.tmfid}-${config.SUBSCRIPTION}`,
  config.INTERNAL_EVENT =`${config.tmfid}-${config.INTERNAL_EVENT}`
}

module.exports = config;
