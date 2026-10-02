const path = require('path');
const fs   = require('fs');

const contents = fs.readFileSync(__dirname + "/config.json");
const jsonConfig = JSON.parse(contents);

const SERVER_URL = process.env.SERVER_URL;
if (SERVER_URL) {
  jsonConfig["servers"][0]["url"] = SERVER_URL;
}

const config = {
  ROOT_DIR: __dirname,
  URL_PORT: 8628,
  URL_PATH: '/tmf-api/performance',
  BASE_VERSION: 'v5',
  CONTROLLER_DIRECTORY: path.join(__dirname, 'controllers'),
  OPENAPI_YAML: 'api/TMF628-Performance-v5.0.0.oas.yaml',
  FULL_PATH: 'http://localhost:8628/tmf-api/performance/v5',
  EXTERNAL_URL: 'http://localhost:8628/tmf-api/performance/v5',

  DEFAULT_FILTERING_FIELDS: { id: 1, href: 1, '@type': 1 },
  DEFAULT_FILTERING_FIELDS_KEYS: [ 'id', 'href', '@type' ],

  // Query limit for pagination
  QUERY_LIMIT: 250

};

config.OPENAPI_YAML = path.join(config.ROOT_DIR, 'api', 'TMF628-Performance-v5.0.0.oas.yaml');
config.FULL_PATH    = 'http://localhost:8628/tmf-api/performance/v5';
config.EXTERNAL_URL = 'http://localhost:8628/tmf-api/performance/v5';

if(jsonConfig.servers && jsonConfig.servers.length>0) {
  config.EXTERNAL_URL = jsonConfig.servers[0].url;
}

module.exports = config;
