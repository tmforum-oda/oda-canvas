const axios = require('axios');
const qs = require('qs');

const dotenv = require('dotenv');

dotenv.config();

// assert the environment variables are set
if (!process.env.KEYCLOAK_USER || !process.env.KEYCLOAK_PASSWORD || !process.env.KEYCLOAK_BASE_URL || !process.env.KEYCLOAK_REALM) {
  console.log('Please set the environment variables KEYCLOAK_USER, KEYCLOAK_PASSWORD, KEYCLOAK_BASE_URL and KEYCLOAK_REALM');
  process.exit(1);
}

const config = {
  user: process.env.KEYCLOAK_USER,
  password: process.env.KEYCLOAK_PASSWORD,
  baseURL: process.env.KEYCLOAK_BASE_URL,
  realm: process.env.KEYCLOAK_REALM
};

const clientId = 'admin-cli';

const identityManagerUtils = {

  /**
   * Private function that allows us to get a token for accessing the API
   * @param   {string}   baseURL         The base URL for the Keycloak API
   * @param   {string}   userName        The username we'll use to access the API
   * @param   {password} password        The password for userName
   * @return  {string}                   The authorisation token
   */
  getToken: async function(baseURL, userName, password) {
    const userData = { username: userName, password: password, grant_type: 'password', client_id: clientId };
    const headers = {'content-type': 'application/x-www-form-urlencoded'};
    const res = await axios({
      url: '/realms/master/protocol/openid-connect/token',
      baseURL: baseURL,
      method: 'post',
      headers: headers,
      data: qs.stringify(userData),
    }).catch(err => {
      console.log('This is the error: ');
      console.log(err);
    });
    return res.data.access_token;
  },

  /**
   * Function that calls the Keycloak API and gets the role for a client in a component
   * @param    {String} clientName        Name of the client we're checking
   * @param    {String} componentName   Name of the component
   * @return   {Array}                  The array of 0 or more roles for the client
   */  
  getRolesForClient: async function(clientName) {
    // Get the token for authn/authz against the Keycloak API
    const token = await identityManagerUtils.getToken(config.baseURL, config.user, config.password);
    const headers = { Authorization: 'Bearer ' + token };
    // Get the ID for the canvassystem client
    res = await axios({
      url: '/admin/realms/'  + config.realm + '/clients',
      baseURL: config.baseURL,
      method: 'get',
      headers: headers,
      params: { clientId: clientName }
    }).catch(err => {
      console.log(err);
    });
    canvassystemID = res.data[0].id;

    // Get the list of roles for canvassystem client
    res = await axios({
      url: '/admin/realms/'  + config.realm + '/clients/' + canvassystemID + '/roles',
      baseURL: config.baseURL,
      method: 'get',
      headers: headers
    }).catch(err => {
      console.log(err);
    });
    roleList = res.data.map(({name}) => name);
    return roleList;
  }
}



module.exports = identityManagerUtils