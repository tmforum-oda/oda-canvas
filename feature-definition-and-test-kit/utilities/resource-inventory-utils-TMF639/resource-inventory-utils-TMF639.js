// Utility functions for querying the Resource Inventory TM Forum API (TMF639)
// API base URL: http://localhost:8639
// Supports ODAComponent and ExposedAPI resource queries for BDD tests

const axios = require('axios');
const assert = require('assert');

const API_BASE_URL = 'http://localhost:8639/tmf-api/resourceInventoryManagement/v5';

const resourceInventoryUtilsTMF639 = {
  /**
   * Query the Resource Inventory API for all resources
   * @returns {Promise<Array>} Array of resource objects
   */
  getAllResources: async function () {
    const url = `${API_BASE_URL}/resource`; // Adjust path if needed
    const response = await axios.get(url);
    return response.data;
  },

  /**
   * Find a resource by name and category using GET /resource/{id}
   * @param {string} resourceName
   * @param {string} category (ODAComponent | ExposedAPI)
   * @returns {Promise<Object|null>} Resource object or null
   */
  findResource: async function (resourceName) {
    try {
      const url = `${API_BASE_URL}/resource/${encodeURIComponent(resourceName)}`;
      const response = await axios.get(url);
      if (response.data) {
        return response.data;
      }
      return null;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return null;
      }
      throw err;
    }
  },

  /**
   * Query resources using a filter string (e.g., category=ODAComponent)
   * @param {string} filter - filter string (e.g., 'category=ODAComponent')
   * @returns {Promise<Array>} Array of resource objects
   */
  getResourcesByFilter: async function (filter) {
    const url = `${API_BASE_URL}/resource?filter=${encodeURIComponent(filter)}`;
    const response = await axios.get(url);
    return response.data;
  },  
};

module.exports = resourceInventoryUtilsTMF639;
