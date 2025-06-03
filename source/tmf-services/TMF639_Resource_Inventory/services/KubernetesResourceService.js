const k8s = require('@kubernetes/client-node');
const logger = require('../logger');
const config = require('../config');

class KubernetesResourceService {
    constructor() {
        this.k8sConfig = new k8s.KubeConfig();
        this.init();
    }

    init() {
        try {
            // Load config from cluster (in-cluster config when running in pod)
            // or from local kubeconfig file
            if (process.env.KUBERNETES_SERVICE_HOST) {
                this.k8sConfig.loadFromCluster();
            } else {
                this.k8sConfig.loadFromDefault();
            }
            
            this.customObjectsApi = this.k8sConfig.makeApiClient(k8s.CustomObjectsApi);
            this.coreApi = this.k8sConfig.makeApiClient(k8s.CoreV1Api);
            
            logger.info('Kubernetes client initialized successfully');
        } catch (error) {
            logger.error('Failed to initialize Kubernetes client:', error);
            throw error;
        }
    }

    /**
     * Get ODA Components from Kubernetes
     */
    async getComponents(namespace = config.KUBERNETES_NAMESPACE) {
        try {
            const response = await this.customObjectsApi.listNamespacedCustomObject(
                'oda.tmforum.org',     // group
                'v1',             // version  
                namespace,             // namespace
                'components'           // plural
            );
            
            return response.body.items || [];
        } catch (error) {
            logger.error('Error fetching Components:', error);
            throw error;
        }
    }

    /**
     * Get specific ODA Component by name
     */
    async getComponent(name, namespace = config.KUBERNETES_NAMESPACE) {
        try {
            const response = await this.customObjectsApi.getNamespacedCustomObject(
                'oda.tmforum.org',     // group
                'v1',             // version
                namespace,             // namespace
                'components',          // plural
                name                   // name
            );
            
            return response.body;
        } catch (error) {
            if (error.response && error.response.statusCode === 404) {
                return null;
            }
            logger.error(`Error fetching Component ${name}:`, error);
            throw error;
        }
    }

    /**
     * Get ExposedAPIs from Kubernetes
     */
    async getExposedAPIs(namespace = config.KUBERNETES_NAMESPACE) {
        try {
            const response = await this.customObjectsApi.listNamespacedCustomObject(
                'oda.tmforum.org',     // group
                'v1',             // version
                namespace,             // namespace
                'exposedapis'          // plural
            );
            
            return response.body.items || [];
        } catch (error) {
            logger.error('Error fetching ExposedAPIs:', error);
            throw error;
        }
    }

    /**
     * Get specific ExposedAPI by name
     */
    async getExposedAPI(name, namespace = config.KUBERNETES_NAMESPACE) {
        try {
            const response = await this.customObjectsApi.getNamespacedCustomObject(
                'oda.tmforum.org',     // group
                'v1',             // version
                namespace,             // namespace
                'exposedapis',         // plural
                name                   // name
            );
            
            return response.body;
        } catch (error) {
            if (error.response && error.response.statusCode === 404) {
                return null;
            }
            logger.error(`Error fetching ExposedAPI ${name}:`, error);
            throw error;
        }
    }    /**
     * Convert Kubernetes Component to TMF639 Resource format
     */    convertComponentToResource(k8sComponent) {
        const metadata = k8sComponent.metadata || {};
        const spec = k8sComponent.spec || {};
        const status = k8sComponent.status || {};

        // Build base characteristics
        const characteristics = [
            {
                '@type': 'Characteristic',
                name: 'namespace',
                value: metadata.namespace
            },
            {
                '@type': 'Characteristic',
                name: 'componentType', 
                value: spec.type
            },
            {
                '@type': 'Characteristic',
                name: 'version',
                value: spec.version
            },
            {
                '@type': 'Characteristic',
                name: 'status',
                value: status.summary?.status || 'Unknown'
            }
        ];        // Add all properties from spec.componentMetadata as characteristics
        if (spec.componentMetadata && typeof spec.componentMetadata === 'object') {
            Object.entries(spec.componentMetadata).forEach(([key, value]) => {
                let characteristicValue;
                
                if (Array.isArray(value)) {
                    // Keep arrays as arrays
                    characteristicValue = [...value];
                } else if (typeof value === 'object' && value !== null) {
                    // JSON stringify other objects
                    characteristicValue = JSON.stringify(value);
                } else {
                    // Keep primitive values as-is
                    characteristicValue = value;
                }
                
                characteristics.push({
                    '@type': 'Characteristic',
                    name: key,
                    value: characteristicValue
                });
            });
        }

        return {
            id: metadata.name,
            href: `/tmf-api/resourceInventoryManagement/v5/resource/${metadata.name}`,
            '@type': 'LogicalResource',
            '@baseType': 'Resource',
            name: metadata.name,
            description: spec.description || `ODA Component: ${metadata.name}`,            category: 'ODAComponent',            resourceSpecification: {
                '@type': 'ResourceSpecificationRef',
                id: 'ODAComponent',
                name: spec.type || 'ODA Component',
                version: spec.version
            },
            resourceCharacteristic: characteristics,
            resourceStatus: this.mapComponentStatusToResourceStatus(status),
            operationalState: this.mapComponentStatusToOperationalState(status),
            administrativeState: 'unlocked',
            usageState: 'active',
            startDate: metadata.creationTimestamp,
            place: [{
                id: metadata.namespace,
                name: metadata.namespace,
                '@type': 'Namespace'
            }]
        };
    }

    /**
     * Convert Kubernetes ExposedAPI to TMF639 Resource format
     */    convertExposedAPIToResource(k8sExposedAPI) {
        const metadata = k8sExposedAPI.metadata || {};
        const spec = k8sExposedAPI.spec || {};
        const status = k8sExposedAPI.status || {};

        // Build base characteristics
        const characteristics = [
            {
                '@type': 'Characteristic',
                name: 'namespace',
                value: metadata.namespace
            },
            {
                '@type': 'Characteristic',
                name: 'apiName',
                value: spec.name
            },
            {
                '@type': 'Characteristic',
                name: 'path',
                value: spec.path
            },
            {
                '@type': 'Characteristic',
                name: 'port',
                value: spec.port?.toString()
            },
            {
                '@type': 'Characteristic',
                name: 'implementation',
                value: spec.implementation
            }
        ];

        // Add specification characteristic if spec.specification exists and is an array
        if (spec.specification && Array.isArray(spec.specification)) {
            characteristics.push({
                '@type': 'Characteristic',
                name: 'specification',
                value: [...spec.specification]
            });
        }

        // Add apiDocs characteristic
        characteristics.push({
            '@type': 'Characteristic',
            name: 'apiDocs',
            value: status.apiStatus?.developerUI
        });

        return {
            id: metadata.name,
            href: `/tmf-api/resourceInventoryManagement/v5/resource/${metadata.name}`,
            '@type': 'LogicalResource',
            '@baseType': 'Resource',            name: metadata.name,
            description: `Exposed API: ${spec.name || metadata.name}`,            category: 'API',            resourceSpecification: {
                '@type': 'ResourceSpecificationRef',
                id: 'API',
                name: 'API',
                version: spec.specification?.version
            },
            resourceCharacteristic: characteristics,
            resourceStatus: this.mapExposedAPIStatusToResourceStatus(status),
            operationalState: this.mapExposedAPIStatusToOperationalState(status),
            administrativeState: 'unlocked',
            usageState: 'active',
            startDate: metadata.creationTimestamp,
            place: [{
                id: metadata.namespace,
                name: metadata.namespace,
                '@type': 'Namespace'
            }]
        };
    }

    mapComponentStatusToResourceStatus(status) {
        const summary = status.summary || {};
        switch (summary.status) {
            case 'Complete':
                return 'available';
            case 'InProgress':
                return 'installing';
            case 'Failed':
                return 'reserved';
            default:
                return 'standby';
        }
    }

    mapComponentStatusToOperationalState(status) {
        const summary = status.summary || {};
        switch (summary.status) {
            case 'Complete':
                return 'enable';
            case 'InProgress':
                return 'enable';
            case 'Failed':
                return 'disable';
            default:
                return 'disable';
        }
    }

    mapExposedAPIStatusToResourceStatus(status) {
        if (status.implementation && status.implementation.ready) {
            return 'available';
        }
        return 'standby';
    }    mapExposedAPIStatusToOperationalState(status) {
        if (status.implementation && status.implementation.ready) {
            return 'enable';
        }
        return 'disable';
    }

    /**
     * List all resources (Components and ExposedAPIs) as TMF639 Resources
     */
    async listResources(namespace = config.KUBERNETES_NAMESPACE) {
        try {
            console.log('KubernetesResourceService: Starting listResources...');
            
            // Get Components from ODA Canvas
            const components = await this.getComponents(namespace);
            console.log(`KubernetesResourceService: Found ${components.length} Components`);

            // Get ExposedAPIs from ODA Canvas  
            const exposedApis = await this.getExposedAPIs(namespace);
            console.log(`KubernetesResourceService: Found ${exposedApis.length} ExposedAPIs`);

            // Convert Components to TMF639 Resources
            const componentResources = components.map(component => this.convertComponentToResource(component));
            
            // Convert ExposedAPIs to TMF639 Resources
            const exposedApiResources = exposedApis.map(api => this.convertExposedAPIToResource(api));

            // Combine all resources
            const allResources = [...componentResources, ...exposedApiResources];
            console.log(`KubernetesResourceService: Returning ${allResources.length} total resources`);
            
            return allResources;
        } catch (error) {
            console.error('KubernetesResourceService: Error listing resources:', error.message);
            if (error.response) {
                console.error('KubernetesResourceService: Response status:', error.response.statusCode);
                console.error('KubernetesResourceService: Response body:', JSON.stringify(error.response.body, null, 2));
            }
            throw error;
        }
    }

    /**
     * Get a specific resource by ID
     */
    async getResourceById(id, namespace = config.KUBERNETES_NAMESPACE) {
        try {
            console.log(`KubernetesResourceService: Getting resource by ID: ${id}`);
            
            // Try to find as Component first
            const component = await this.getComponent(id, namespace);
            if (component) {
                console.log(`KubernetesResourceService: Found Component: ${id}`);
                return this.convertComponentToResource(component);
            }

            // Try to find as ExposedAPI
            const exposedApi = await this.getExposedAPI(id, namespace);
            if (exposedApi) {
                console.log(`KubernetesResourceService: Found ExposedAPI: ${id}`);
                return this.convertExposedAPIToResource(exposedApi);
            }

            console.log(`KubernetesResourceService: Resource not found: ${id}`);
            return null;
        } catch (error) {
            console.error(`KubernetesResourceService: Error getting resource ${id}:`, error.message);
            throw error;
        }
    }
}

module.exports = KubernetesResourceService;
