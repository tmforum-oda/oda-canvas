import apiClient from './client'

export interface GatewayResource {
  kind: string    // "VirtualService" | "HTTPRoute" | "ApisixRoute"
  name: string
  namespace?: string
  group?: string
  apiVersion?: string
}

/** Extra details surfaced from the gateway object itself (paths, hosts, etc.) */
export interface GatewayDetails {
  hosts?: string[]
  gateways?: string[]
  hostnames?: string[]
  paths?: string[]
  backendRefs?: string[]
  pluginNames?: string[]
  pluginConfigNames?: string[]
  rulesCount?: number
}

/** A plugin/policy attached to this ExposedAPI via the gateway */
export interface Policy {
  pluginType: string          // e.g. "rate-limiting", "jwt", "oauth2", "key-auth", "cors"
  name?: string               // K8s resource name of the plugin
  namespace?: string
  enabled?: boolean
  config?: Record<string, unknown>
}

export interface RelatedExposedApi {
  name: string
  namespace: string
  url?: string
  status?: string
}

export interface GatewayBinding extends GatewayResource {
  canvasType: string
  details?: GatewayDetails
  relatedExposedApi?: RelatedExposedApi
  policies?: Policy[]
}

export interface ExposedAPI {
  apiVersion?: string
  name: string
  namespace: string
  url?: string
  status: string              // "ready" | "notReady"
  apiType?: string            // "openapi" | "mcp" | "prometheus" | "openmetrics" | "a2a"
  canvasType?: string
  implementation?: string
  port?: string
  version?: string
  createdAt?: string
  gatewayResource?: GatewayResource
  gatewayDetails?: GatewayDetails
  gatewayResources?: GatewayBinding[]
  policies?: Policy[]
  error?: string
}

export interface GatewayInventoryResponse {
  canvasType?: string
  availableCanvasTypes?: string[]
  resources: GatewayBinding[]
}

export async function fetchExposedApis(): Promise<ExposedAPI[]> {
  const { data } = await apiClient.get<ExposedAPI[]>('/api/exposedapis')
  return data
}

export async function fetchExposedApi(namespace: string, name: string): Promise<ExposedAPI> {
  const { data } = await apiClient.get<ExposedAPI>(`/api/exposedapis/${namespace}/${name}`)
  return data
}

export async function fetchGatewayResources(): Promise<GatewayBinding[]> {
  const { data } = await apiClient.get<GatewayInventoryResponse>('/api/gateway/resources')
  return data.resources ?? []
}
