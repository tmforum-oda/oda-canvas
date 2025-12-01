// deploy_azure_infra.bicep
@description('The location for all resources.')
param location string = resourceGroup().location

@description('A prefix for all resource names to ensure uniqueness.')
param resourcePrefix string

@description('The object ID of the user or group to grant Key Vault secret access (e.g., your own user ID for setup).')
param adminUserObjectId string

@description('The Client ID of the Entra ID application registration for the backend API.')
param backendAppClientId string

@description('The Tenant ID of your Azure Entra ID.')
param entraTenantId string

// --- Variables for Resource Naming ---
var keyVaultName = '${resourcePrefix}-kv'
var logAnalyticsWorkspaceName = '${resourcePrefix}-logs'
var appInsightsName = '${resourcePrefix}-appinsights'
var aksClusterName = '${resourcePrefix}-aks'
var apimServiceName = '${resourcePrefix}-apim'
var postgresServerName = '${resourcePrefix}-pg'
var virtualNetworkName = '${resourcePrefix}-vnet'
var aksSubnetName = 'aks-subnet'
var pgSubnetName = 'pg-subnet'

// --- Networking ---
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2022-07-01' = {
  name: virtualNetworkName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: aksSubnetName
        properties: {
          addressPrefix: '10.0.1.0/24'
        }
      }
      {
        name: pgSubnetName
        properties: {
          addressPrefix: '10.0.2.0/24'
          delegations: [
            {
              name: 'Microsoft.DBforPostgreSQL/flexibleServers'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// --- Foundational Observability Resources ---
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    // MODIFICATION: Add this block to enable granular access control features.
    // 'Enableable' allows you to switch between workspace-context and resource-context access.
    // 'Enabled' forces resource-context, which is what we need for ABAC.
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// --- Azure Key Vault to store secrets ---
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: entraTenantId
    enableRbacAuthorization: true // Using RBAC is modern best practice
  }
}

// --- Azure Kubernetes Service ---
resource aksCluster 'Microsoft.ContainerService/managedClusters@2023-08-01' = {
  name: aksClusterName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    dnsPrefix: '${resourcePrefix}dns'
    agentPoolProfiles: [
      {
        name: 'agentpool'
        count: 2
        vmSize: 'Standard_DS2_v2'
        osType: 'Linux'
        mode: 'System'
        vnetSubnetID: virtualNetwork.properties.subnets[0].id
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      serviceCidr: '10.1.0.0/16'
      dnsServiceIP: '10.1.0.10'
    }
    // Enable Azure Monitor for Containers (Prometheus) - Deploys the Azure Monitor Agent (AMA)
    azureMonitorProfile: {
      metrics: {
        enabled: true
        kubeStateMetrics: {
          metricLabelsAllowlist: 'app.kubernetes.io/name,oda.tmforum.org/component'
        }
      }
    }
    oidcIssuerProfile: {
      enabled: true
    }
  }
}

// --- Azure API Management ---
resource apimService 'Microsoft.ApiManagement/service@2022-08-01' = {
  name: apimServiceName
  location: location
  sku: {
    name: 'Developer' // Use 'Basic' or 'Standard' for production
    capacity: 1
  }
  properties: {
    publisherEmail: 'admin@example.com'
    publisherName: 'ODA Canvas'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// --- Azure Database for PostgreSQL ---
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '14'
    administratorLogin: 'odaadmin'
    administratorLoginPassword: '${newGuid()}' // IMPORTANT: In production, manage this secret properly.
    network: {
      delegatedSubnetResourceId: virtualNetwork.properties.subnets[1].id
      privateDnsZoneArmResourceId: postgresPrivateDnsZone.id
    }
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
    }
  }
}

resource postgresPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${postgresServerName}.private.postgres.database.azure.com'
  location: 'global'
}

resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresPrivateDnsZone
  name: '${virtualNetworkName}-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork.id
    }
  }
}

// --- RBAC Role Assignments ---
// Grant AKS Managed Identity 'Key Vault Secrets User' role to read secrets
resource aksKvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(aksCluster.id, keyVault.id, 'kv-secrets-user')
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: aksCluster.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant APIM Managed Identity 'Key Vault Secrets User' role
resource apimKvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(apimService.id, keyVault.id, 'kv-secrets-user')
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: apimService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Admin User 'Key Vault Secrets Officer' role to set secrets
resource adminKvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, adminUserObjectId, 'kv-secrets-officer')
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c194983') // Key Vault Secrets Officer
    principalId: adminUserObjectId
    principalType: 'User'
  }
}


// --- Outputs ---
output KEY_VAULT_NAME string = keyVaultName
output AKS_CLUSTER_NAME string = aksClusterName
output APIM_SERVICE_NAME string = apimServiceName
output APP_INSIGHTS_INSTRUMENTATION_KEY string = appInsights.properties.InstrumentationKey
output PG_SERVER_FQDN string = postgresServer.properties.fullyQualifiedDomainName
output PG_ADMIN_USER string = postgresServer.properties.administratorLogin
output logAnalyticsWorkspaceName string = logAnalyticsWorkspaceName