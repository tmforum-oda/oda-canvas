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
  URL_PORT: 8639,
  URL_PATH: '/tmf-api/resourceInventoryManagement',
  BASE_VERSION: 'v5',
  CONTROLLER_DIRECTORY: path.join(__dirname, 'controllers'),
  OPENAPI_YAML: 'api/TMF639-Resource_Inventory_Management-v5.0.0.oas.yaml',
  FULL_PATH: 'http://localhost:8639/tmf-api/resourceInventoryManagement/v5',
  EXTERNAL_URL: 'http://localhost:8639/tmf-api/resourceInventoryManagement/v5',

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
  ASYNC_HEADER: 'run_async',

  // Kubernetes configuration for accessing ODA Canvas resources
  KUBERNETES_NAMESPACE: process.env.KUBERNETES_NAMESPACE || 'components',
  KUBERNETES_CONFIG_PATH: process.env.KUBECONFIG || '/var/run/secrets/kubernetes.io/serviceaccount'

}

config.OPENAPI_YAML   = path.join(config.ROOT_DIR, 'api', 'TMF639-Resource_Inventory_Management-v5.0.0.oas.yaml')
config.FULL_PATH      = 'http://localhost:8639/tmf-api/resourceInventoryManagement/v5'
config.EXTERNAL_URL   = 'http://localhost:8639/tmf-api/resourceInventoryManagement/v5'

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
