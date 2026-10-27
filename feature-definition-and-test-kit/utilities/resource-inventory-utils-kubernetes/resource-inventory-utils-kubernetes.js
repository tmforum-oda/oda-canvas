const k8s = require('@kubernetes/client-node')
const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const testDataFolder = './testData/'

const GROUP = "oda.tmforum.org"
const VERSION = "v1"
const EXPOSED_APIS_PLURAL = "exposedapis"
const DEPENDENT_APIS_PLURAL = "dependentapis"
const COMPONENTS_PLURAL = "components"


const resourceInventoryUtils = {

  /**
  * Function that returns the custom API resource 
  * @param    {String} inCustomCRDPluralName  Plural name of the custom resource type
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inResourceName         Name of the API that is requested
  * @param    {String} inReleaseName          Release name of the component instance
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}         The API resource object, or null if the API is not found
  */
  getCustomResource: async function (inCustomCRDPluralName, inResourceName, inComponentName, inReleaseName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const customResourceName = inReleaseName + '-' + inComponentName + '-' + inResourceName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, inCustomCRDPluralName, undefined, undefined, 'metadata.name=' + customResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },  

  // Helper functions for normalizing comparisions for API resources
  _eqCI: function (a, b) {
    if (a === undefined || a === null) return false;
    if (b === undefined || b === null) return false;
    return String(a).toLowerCase() === String(b).toLowerCase();
  },

  _hasComponentOwnerRef: function (obj, componentName) {
    const refs = obj?.metadata?.ownerReferences || [];
    return refs.some(r => r?.kind === 'Component' && r?.name === componentName);
  },

  _isReady: function (obj, kind) {
    if (kind === 'ExposedAPI') {
      return obj?.status?.implementation?.ready === true
    }
    // DependentAPI: status.implementation.ready (seen in your sample)
    if (kind === 'DependentAPI') {
      return obj?.status?.implementation?.ready === true;
    }
    return false;
  },

  _normalizeVersion: function (v) {
    if (v === undefined || v === null) return null;
    const s = String(v).trim().toLowerCase();
    if (/^\d+$/.test(s)) return `v${s}`;     // "4" -> "v4"
    if (/^v\d+$/.test(s)) return s;          // "v4" -> "v4"
    return s;                                // leave as-is (e.g., "v5.0" if that ever appears)
  },
  
  _inferVersionFromUrl: function (url) {
    if (!url) return null;
    const s = String(url).toLowerCase();
  
    // common patterns: "/v4", "v4.0.0", "-v4.", "_v4", etc.
    const m =
      s.match(/\/v(\d+)(\/|$)/) ||
      s.match(/(?:^|[^a-z0-9])v(\d+)(?:\D|$)/);
  
    return m ? `v${m[1]}` : null;
  },

  _getSpecVersions: function (obj) {
    // spec.specification is an array with { version: v4 } etc
    const specs = obj?.spec?.specification || [];
    // 1) explicit versions
    const explicit = specs
      .map(s => this._normalizeVersion(s?.version))
      .filter(Boolean);

    if (explicit.length > 0) return explicit;

    // 2) infer from urls
    const inferred = specs
      .map(s => this._inferVersionFromUrl(s?.url))
      .filter(Boolean);

    if (inferred.length > 0) return inferred;

    // 3) final default
    return ['v4'];
  },

  /**
   * Generic finder for ExposedAPI/DependentAPI CRs.
   * Matching order:
   * 1) legacy direct name match (component-api)
   * 2) list + filter by component (label selector preferred, then ownerRef fallback)
   * 3) filter by spec.name
   * 4) if options.version -> filter by spec.specification[].version
   * 5) if still >1 and options.segmentName and CR has spec.segment -> filter by spec.segment
   * 6) deterministic pick: prefer ready, else newest
   */
  _findApiResource: async function (plural, apiName, componentName, namespace, options = {}, kindHint = 'ExposedAPI') {
	// console.log(`_findApiResource called with plural=${plural}, apiName=${apiName}, componentName=${componentName}, namespace=${namespace}, options=${JSON.stringify(options)}, kindHint=${kindHint}`);
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);

    const versionOpt = options?.version;           // e.g. "v4"
    const segmentOpt = options?.segmentName;       // e.g. "coreFunction"

    // ---- 1) legacy fast path: metadata.name == "<componentName>-<apiName>"
    try {
      const legacyName = `${componentName}-${apiName}`;
	  // console.log(`1) listNamespacedCustomObject(g=${GROUP}, v=${VERSION}, ns=${namespace}, name=${legacyName}`);
      const legacyResp = await k8sCustomApi.listNamespacedCustomObject(
        GROUP, VERSION, namespace, plural,
        undefined, undefined,
        `metadata.name=${legacyName}`
      );
      const legacyItems = legacyResp?.body?.items || [];
      if (legacyItems.length > 0) return legacyItems[0];
    } catch (_) {
      // ignore and continue
    }

    // ---- 2) list candidates (prefer label selector)
    let candidates = [];
    try {
      const labelSelector = `oda.tmforum.org/componentName=${componentName}`;
	  // console.log(`2) listNamespacedCustomObject(g=${GROUP}, v=${VERSION}, ns=${namespace}, labelSelector=${labelSelector}`);
      const resp = await k8sCustomApi.listNamespacedCustomObject(
        GROUP, VERSION, namespace, plural,
        undefined, undefined,
        undefined,            // fieldSelector
        labelSelector         // labelSelector
      );
      candidates = resp?.body?.items || [];
    } catch (_) {
      candidates = [];
    }

    // ownerRef fallback if label selector yielded nothing
    if (!candidates || candidates.length === 0) {
	  // console.log(`2b) listNamespacedCustomObject(g=${GROUP}, v=${VERSION}, ns=${namespace}, ownerRef=${componentName})`);
        		
      const resp = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, namespace, plural);
      const all = resp?.body?.items || [];
      candidates = all.filter(o => this._hasComponentOwnerRef(o, componentName));
    }

	// for full debug info use: console.log(`CANDIDATES: ${JSON.stringify(candidates, null, 2)}`);
	// console.log(`CANDIDATES: ${JSON.stringify(candidates.map(o => o?.metadata?.name))}`);

    if (!candidates || candidates.length === 0) return null;

    // ---- 3) filter by spec.name
	// console.log(`3) filter apiName=${apiName} in candidates by spec.name`);
    let matches = candidates.filter(o => this._eqCI(o?.spec?.name, apiName));
    if (matches.length === 0) return null;

    // ---- 4) if version provided, filter by spec.specification[].version
    if (versionOpt) {
	  // console.log(`4) filter _getSpecVersions versionOpt=${versionOpt}`);
      const vMatches = matches.filter(o => {
        const versions = this._getSpecVersions(o);
        return versions.some(v => this._eqCI(v, versionOpt));
      });
      if (vMatches.length > 0) matches = vMatches;
    }

    // ---- 5) if still >1 and segment provided, use it only if CR actually has spec.segment
    if (matches.length > 1 && segmentOpt) {
	  // console.log(`5) filterfilter segmentOpt=${segmentOpt}`);
      const hasAnySegment = matches.some(o => o?.spec?.segment !== undefined && o?.spec?.segment !== null);
      if (hasAnySegment) {
        const sMatches = matches.filter(o => this._eqCI(o?.spec?.segment, segmentOpt));
        if (sMatches.length > 0) matches = sMatches;
      }
    }

    // ---- 6) deterministic pick: prefer ready, else newest
    const checkReady = options?.checkReady === true;
    let pool = matches;

    if (checkReady) {
	  // console.log(`6) filter isReady ${kindHint}`);
      const ready = matches.filter(o => this._isReady(o, kindHint));
      if (ready.length > 0) {
        pool = ready;
      }
    }

    pool.sort((a, b) => {
      const ta = new Date(a?.metadata?.creationTimestamp || 0).getTime();
      const tb = new Date(b?.metadata?.creationTimestamp || 0).getTime();
      return tb - ta; // newest first
    });

	// for full debug info use: console.log(`POOL: ${JSON.stringify(pool, null, 2)}`);
	// console.log(`POOL: ${JSON.stringify(pool.map(o => o?.metadata?.name))}`);
	
    return pool[0] || null;
  },

  /**
  * Function that returns the custom ExposedAPI resource given ExposedAPI name
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inExposedAPIName       Name of the ExposedAPI that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}        The ExposedAPI resource object, or null if the ExposedAPI is not found
  */
  getExposedAPIResource: async function (inExposedAPIName, inComponentName, inNamespace, options = {}) {
    return await this._findApiResource(
      EXPOSED_APIS_PLURAL,
      inExposedAPIName,
      inComponentName,
      inNamespace,
      options,
      'ExposedAPI'
    )
  },

  /**
  * Function that returns the custom DependentAPI resource given DependentAPI name
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inDependentAPIName     Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}          The DependentAPI resource object, or null if the DependentAPI is not found
  */
  getDependentAPIResource: async function (inDependentAPIName, inComponentName, inNamespace, options = {}) {
    return await this._findApiResource(
      DEPENDENT_APIS_PLURAL,
      inDependentAPIName,
      inComponentName,
      inNamespace,
      options,
      'DependentAPI'
    )
  },

  /**
  * Function that returns the custom Component resource given Component Name
  * @param    {String} inComponentName        Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
  getComponentResource: async function (inComponentName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)

    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, COMPONENTS_PLURAL, undefined, undefined, 'metadata.name=' + inComponentName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  /**
  * Function that returns the custom Component resource of a specific version, given Component Name
  * @param    {String} inComponentName        Name of the API that is requested
  * @param    {String} inComponentVersion     Version of the component spec that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
  getComponentResourceByVersion: async function (inComponentName, inComponentVersion, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, inComponentVersion, inNamespace, COMPONENTS_PLURAL, undefined, undefined, 'metadata.name=' + inComponentName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // Component not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  // API Gateway CRs (Kong and APISIX)
  //
  // The Kong and APISIX operators name every resource they create after the ExposedAPI
  // resource, which the Component operator names <componentName>-<apiName>, with a -v<N>
  // suffix when the API declares a major version (e.g. ctk-productcatalogmanagement-productcatalogmanagement-v4).

  /**
  * Function that returns the gateway custom resource created for an ExposedAPI
  * @param    {String} group, version, plural   The custom resource type to list
  * @param    {String} inNamespace              Namespace to look in
  * @param    {String} inNamePrefix             Resource name before the ExposedAPI name (e.g. 'kong-api-route')
  * @param    {String} inComponentName          Name of the component (e.g. 'ctk-productcatalogmanagement')
  * @param    {String} inApiName                Name of the ExposedAPI in the component spec (e.g. 'productcatalogmanagement')
  * @return   {Object}         The resource object, or null if not found
  */
  _findGatewayResource: async function (group, version, plural, inNamespace, inNamePrefix, inComponentName, inApiName) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const baseName = `${inNamePrefix}-${inComponentName}-${inApiName}`
    const isMatch = (resourceName) => {
      if (resourceName === baseName) return true
      const versionSuffix = resourceName.startsWith(`${baseName}-v`) ? resourceName.slice(baseName.length + 2) : ''
      return versionSuffix.length > 0 && /^[0-9]+$/.test(versionSuffix)
    }

    const response = await k8sCustomApi.listNamespacedCustomObject(group, version, inNamespace, plural)
    const items = response.body.items || []
    const match = items.find(item => isMatch(item.metadata.name))
    if (!match) {
      console.log(`${plural} ${baseName}[-v<N>] not found in namespace ${inNamespace}. Found: ${JSON.stringify(items.map(item => item.metadata.name))}`)
      return null
    }
    return match
  },

  /**
  * Function that returns the Kong HTTPRoute for an ExposedAPI
  * @param    {String} inComponentName        Name of the component
  * @param    {String} inApiName              Name of the ExposedAPI in the component spec
  * @param    {String} [inNamespace='components'] Namespace of the ExposedAPI
  * @return   {Object}         The HTTPRoute object, or null if not found
  */
  getHTTPRouteForComponent: async function (inComponentName, inApiName, inNamespace = 'components') {
    return await this._findGatewayResource('gateway.networking.k8s.io', 'v1', 'httproutes',
      inNamespace, 'kong-api-route', inComponentName, inApiName)
  },

  /**
  * Function that returns a KongPlugin for an ExposedAPI
  * @param    {String} inComponentName        Name of the component
  * @param    {String} inApiName              Name of the ExposedAPI in the component spec
  * @param    {String} inPluginPrefix         Plugin name prefix used by the Kong operator (e.g. 'rate-limit', 'apiauthentication')
  * @param    {String} [inNamespace='components'] Namespace of the ExposedAPI
  * @return   {Object}         The KongPlugin object, or null if not found
  */
  getKongPluginForComponent: async function (inComponentName, inApiName, inPluginPrefix, inNamespace = 'components') {
    return await this._findGatewayResource('configuration.konghq.com', 'v1', 'kongplugins',
      inNamespace, inPluginPrefix, inComponentName, inApiName)
  },

  /**
  * Function that returns the ApisixRoute for an ExposedAPI
  * @param    {String} inComponentName        Name of the component
  * @param    {String} inApiName              Name of the ExposedAPI in the component spec
  * @param    {String} [inNamespace='istio-ingress'] Namespace where the APISIX operator creates routes
  * @return   {Object}         The ApisixRoute object, or null if not found
  */
  getApisixRouteForComponent: async function (inComponentName, inApiName, inNamespace = 'istio-ingress') {
    return await this._findGatewayResource('apisix.apache.org', 'v2', 'apisixroutes',
      inNamespace, 'apisix-api-route', inComponentName, inApiName)
  },

  /**
  * Function that returns the combined ApisixPluginConfig for an ExposedAPI
  * @param    {String} inComponentName        Name of the component
  * @param    {String} inApiName              Name of the ExposedAPI in the component spec
  * @param    {String} [inNamespace='istio-ingress'] Namespace where the APISIX operator creates plugin configs
  * @return   {Object}         The ApisixPluginConfig object, or null if not found
  */
  getApisixPluginForComponent: async function (inComponentName, inApiName, inNamespace = 'istio-ingress') {
    return await this._findGatewayResource('apisix.apache.org', 'v2', 'apisixpluginconfigs',
      inNamespace, 'combined-apisixpluginconfig', inComponentName, inApiName)
  },

  /**
   * Function that returns the logs from the ODA operator pod
   */
  getOperatorLogs: async function (inOperatorLabel, inContainerName) {
    // use the kubernetes API to get the logs from the ODA operator pod
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
    const podList = await k8sCoreApi.listNamespacedPod('canvas', undefined, undefined, undefined, undefined, 'app=' + inOperatorLabel)
    const operatorPod = podList.body.items[0]
    const operatorPodName = operatorPod.metadata.name
    const operatorPodNamespace = operatorPod.metadata.namespace
    var operatorLogs
    if (inContainerName) {
      operatorLogs = await k8sCoreApi.readNamespacedPodLog(operatorPodName, operatorPodNamespace, container=inContainerName)
    } else {
      operatorLogs = await k8sCoreApi.readNamespacedPodLog(operatorPodName, operatorPodNamespace)
    }
    return operatorLogs.body
  },

  /**
   * Function that checks if the PDB Management Operator is ready
   * @return   {Boolean}                  True if operator is ready, false otherwise
   */
  isPDBOperatorReady: async function () {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const response = await k8sAppsApi.readNamespacedDeployment(
        'canvas-pdb-management-operator',
        'canvas'
      )
      return response.body.status && response.body.status.readyReplicas > 0
    } catch (error) {
      return false
    }
  },

  /**
   * Function that gets a PDB resource
   * @param    {String} pdbName           Name of the PDB
   * @param    {String} inNamespace       Namespace of the PDB
   * @return   {Object}                 The PDB resource object, or null if not found
   */
  getPDBResource: async function (pdbName, inNamespace) {
    try {
      // Use execSync to get PDB via kubectl as a workaround
      const result = execSync(
        `kubectl get pdb ${pdbName} -n ${inNamespace} -o json 2>/dev/null`,
        { encoding: 'utf-8' }
      );
      return JSON.parse(result);
    } catch (error) {
      // If kubectl returns error (PDB not found), return null
      if (error.status === 1 || error.message.includes('NotFound')) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Function that lists what is left of a Helm release in a namespace: the Components, Pods and
   * PersistentVolumeClaims whose names start with '<release name>-'
   * @param    {String} inReleaseName     Release name of the component instance
   * @param    {String} inNamespace       Namespace where the component instance was running
   * @return   {String[]}                 'Kind/name' of each remaining resource, empty when none is left
   */
  getReleaseResources: async function (inReleaseName, inNamespace) {
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const prefix = inReleaseName + '-'
    const components = (await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, COMPONENTS_PLURAL)).body.items
    const pods = (await k8sCoreApi.listNamespacedPod(inNamespace)).body.items
    const pvcs = (await k8sCoreApi.listNamespacedPersistentVolumeClaim(inNamespace)).body.items
    return [
      ...components.map(item => 'Component/' + item.metadata.name),
      ...pods.map(item => 'Pod/' + item.metadata.name),
      ...pvcs.map(item => 'PersistentVolumeClaim/' + item.metadata.name)
    ].filter(name => name.split('/')[1].startsWith(prefix))
  },

  /**
   * Function that ensures a namespace exists
   * @param    {String} namespaceName     Name of the namespace
   */
  ensureNamespaceExists: async function (namespaceName) {
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
    try {
      await k8sCoreApi.readNamespace(namespaceName);
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        // Namespace doesn't exist, create it
        const namespace = {
          apiVersion: 'v1',
          kind: 'Namespace',
          metadata: {
            name: namespaceName
          }
        };
        try {
          await k8sCoreApi.createNamespace(namespace);
          console.log(`Created namespace: ${namespaceName}`);
        } catch (createError) {
          console.warn(`Failed to create namespace ${namespaceName}:`, createError.message);
        }
      }
    }
  },

  /**
   * Function that creates a deployment for testing purposes
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where to create the deployment
   * @param    {Number} replicas          Number of replicas
   * @param    {Object} annotations       Annotations to add to the deployment
   * @param    {Object} labels           Labels to add to the deployment
   * @return   {Object}                   The created deployment object
   */
  createTestDeployment: async function (deploymentName, inNamespace, replicas, annotations = {}, labels = {}) {
    try {
      // Ensure namespace exists first
      await this.ensureNamespaceExists(inNamespace);
      
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      
      // Try to delete existing deployment first to ensure clean state
      try {
        await k8sAppsApi.deleteNamespacedDeployment(deploymentName, inNamespace)
        // Wait a moment for deletion to complete
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (deleteError) {
        // Ignore if deployment doesn't exist (404 error)
        if (deleteError.response && deleteError.response.statusCode !== 404) {
          console.warn(`Warning: Failed to delete existing deployment ${deploymentName}:`, deleteError.message);
        }
      }
      
      const deployment = {
        apiVersion: 'apps/v1',
        kind: 'Deployment',
        metadata: {
          name: deploymentName,
          namespace: inNamespace,
          annotations: annotations,
          labels: {
            app: deploymentName,
            ...labels
          }
        },
        spec: {
          replicas: replicas,
          selector: {
            matchLabels: {
              app: deploymentName
            }
          },
          template: {
            metadata: {
              labels: {
                app: deploymentName,
                ...labels
              }
            },
            spec: {
              containers: [{
                name: 'test-container',
                image: 'nginx:latest',
                resources: {
                  requests: {
                    memory: '64Mi',
                    cpu: '50m'
                  },
                  limits: {
                    memory: '128Mi',
                    cpu: '100m'
                  }
                }
              }]
            }
          }
        }
      }

      const response = await k8sAppsApi.createNamespacedDeployment(inNamespace, deployment)
      return response.body
    } catch (error) {
      console.error(`Failed to create deployment ${deploymentName} in namespace ${inNamespace}:`, error.message);
      
      // If it's a conflict error (409), the deployment might already exist, just ignore
      if (error.response && error.response.statusCode === 409) {
        console.log(`Deployment ${deploymentName} already exists, continuing...`);
        return null;
      }
      
      throw error;
    }
  },

  /**
   * Function that scales a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace of the deployment
   * @param    {Number} replicas          New number of replicas
   */
  scaleTestDeployment: async function (deploymentName, inNamespace, replicas) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const patch = [{
        op: 'replace',
        path: '/spec/replicas',
        value: replicas
      }]
      
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      console.error(`Failed to scale deployment ${deploymentName}:`, error.message);
      
      // Fallback to kubectl
      try {
        const { execSync } = require('child_process');
        const scaleCmd = `kubectl scale deployment ${deploymentName} --replicas=${replicas} -n ${inNamespace}`;
        execSync(scaleCmd, { encoding: 'utf-8' });
        console.log(`Successfully scaled ${deploymentName} using kubectl fallback`);
      } catch (kubectlError) {
        console.error(`Kubectl fallback also failed:`, kubectlError.message);
        console.log(`Warning: Could not scale deployment ${deploymentName}, continuing with test...`);
        // Don't throw error to allow test to continue
      }
    }
  },

  /**
   * Function that updates deployment annotations
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace of the deployment
   * @param    {Object} annotations       New annotations
   */
  updateDeploymentAnnotations: async function (deploymentName, inNamespace, annotations) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      
      // First, get the current deployment to check if annotations exist
      const currentDeployment = await k8sAppsApi.readNamespacedDeployment(deploymentName, inNamespace);
      const currentAnnotations = currentDeployment.body.metadata.annotations || {};
      
      // Merge with new annotations
      const mergedAnnotations = { ...currentAnnotations, ...annotations };
      
      const patch = [{
        op: currentDeployment.body.metadata.annotations ? 'replace' : 'add',
        path: '/metadata/annotations',
        value: mergedAnnotations
      }]
      
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      console.error(`Failed to update annotations for deployment ${deploymentName} in namespace ${inNamespace}:`, error.message);
      // Don't throw error to avoid breaking tests - just log it
      return null;
    }
  },

  /**
   * Function that creates an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy
   * @param    {String} inNamespace       Namespace where to create the policy
   * @param    {Object} spec              Policy specification
   * @return   {Object}                   The created policy object
   */
  createAvailabilityPolicy: async function (policyName, inNamespace, spec) {
    try {
      // Ensure namespace exists first
      await this.ensureNamespaceExists(inNamespace);
      
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      
      // Check if policy already exists
      try {
        const existing = await k8sCustomApi.getNamespacedCustomObject(
          'availability.oda.tmforum.org',
          'v1alpha1',
          inNamespace,
          'availabilitypolicies',
          policyName
        );
        if (existing) {
          // Policy already exists, just return it
          return existing.body;
        }
      } catch (getError) {
        // Policy doesn't exist, proceed to create it
      }
      
      const policy = {
        apiVersion: 'availability.oda.tmforum.org/v1alpha1',
        kind: 'AvailabilityPolicy',
        metadata: {
          name: policyName,
          namespace: inNamespace
        },
        spec: spec
      }

      const response = await k8sCustomApi.createNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policy
      )
      return response.body
    } catch (error) {
      // Silently handle 409 Conflict errors (policy already exists)
      if (error.response && error.response.statusCode === 409) {
        return null;
      }
      
      // For webhook validation tests, throw the error with the validation message
      if (error.response && error.response.statusCode >= 400 && error.response.statusCode < 500) {
        const errorMessage = error.response.body && error.response.body.message 
          ? error.response.body.message
          : error.message;
        throw new Error(errorMessage);
      }
      
      console.error(`Failed to create AvailabilityPolicy ${policyName} in namespace ${inNamespace}:`, error.message);
      // Don't throw the error here for other types of failures - let tests handle them
      return null;
    }
  },

  /**
   * Function that gets an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy to get
   * @param    {String} inNamespace       Namespace where the policy is located
   * @return   {Object}                   The AvailabilityPolicy resource object
   */
  getAvailabilityPolicy: async function (policyName, inNamespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      const response = await k8sCustomApi.getNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      );
      return response.body;
    } catch (error) {
      console.error(`Failed to get AvailabilityPolicy ${policyName} in namespace ${inNamespace}:`, error.message);
      return null;
    }
  },

  /**
   * Function that updates an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy to update
   * @param    {String} inNamespace       Namespace where the policy is located
   * @param    {Object} spec              The new spec for the policy
   */
  updateAvailabilityPolicy: async function (policyName, inNamespace, spec) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      
      // Get the existing policy first
      const existingPolicy = await k8sCustomApi.getNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      );
      
      // Update the spec
      const updatedPolicy = {
        ...existingPolicy.body,
        spec: spec
      };

      const response = await k8sCustomApi.replaceNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName,
        updatedPolicy
      )
      return response.body
    } catch (error) {
      // For webhook validation tests, throw the error with the validation message
      if (error.response && error.response.statusCode >= 400 && error.response.statusCode < 500) {
        const errorMessage = error.response.body && error.response.body.message 
          ? error.response.body.message
          : error.message;
        throw new Error(errorMessage);
      }
      
      console.error(`Failed to update AvailabilityPolicy ${policyName} in namespace ${inNamespace}:`, error.message);
      return null;
    }
  },

  /**
   * Function that deletes an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy to delete
   * @param    {String} inNamespace       Namespace where the policy is located
   */
  deleteAvailabilityPolicy: async function (policyName, inNamespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      await k8sCustomApi.deleteNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      )
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (policy already deleted)
    }
  },

  /**
   * Function that deletes a test deployment
   * @param    {String} deploymentName    Name of the deployment to delete
   * @param    {String} inNamespace       Namespace where the deployment is located
   */
  deleteTestDeployment: async function (deploymentName, inNamespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      await k8sAppsApi.deleteNamespacedDeployment(deploymentName, inNamespace)
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (deployment already deleted)
    }
  },

  /**
   * Function that deletes a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where the deployment should be deleted
   */
  deleteTestDeployment: async function (deploymentName, inNamespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      await k8sAppsApi.deleteNamespacedDeployment(deploymentName, inNamespace)
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (deployment already deleted)
    }
  },

  /**
   * Function that scales a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where the deployment exists
   * @param    {Number} replicas          Number of replicas to scale to
   */
  scaleTestDeployment: async function (deploymentName, inNamespace, replicas) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const patch = [
        {
          op: 'replace',
          path: '/spec/replicas',
          value: replicas
        }
      ]
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      console.error(`Failed to scale deployment ${deploymentName}: ${error.message}`);
      
      // Try kubectl scale as fallback
      try {
        execSync(`kubectl scale deployment ${deploymentName} --replicas=${replicas} -n ${inNamespace}`, { encoding: 'utf-8' });
        console.log(`Successfully scaled ${deploymentName} using kubectl fallback`);
        return;
      } catch (kubectlError) {
        console.error(`Kubectl fallback also failed: ${kubectlError.message}`);
      }
      
      // If both methods fail, just log and continue (don't break the test)
      console.warn(`Warning: Could not scale deployment ${deploymentName}, continuing with test...`);
    }
  },

  /**
   * Function that deletes an availability policy
   * @param    {String} policyName        Name of the policy
   * @param    {String} inNamespace       Namespace where the policy should be deleted
   */
  deleteAvailabilityPolicy: async function (policyName, inNamespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      await k8sCustomApi.deleteNamespacedCustomObject(
        'oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      )
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (policy already deleted)
    }
  }
}

module.exports = resourceInventoryUtils
