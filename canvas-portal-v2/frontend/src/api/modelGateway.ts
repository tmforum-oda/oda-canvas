import apiClient from './client'

export interface ModelGatewayDependentModel {
  name: string
  provider: string
  version: string
  priority: number
  modality?: string
  project?: string
  endpoint?: string
  auth?: {
    method?: string
    secretRefs?: Array<{ name: string; key: string }>
    k8sServiceAccount?: string
  }
}

export interface ModelGatewayService {
  apiVersion: string
  kind: string
  name: string
  namespace: string
  endpointUrl?: string
  createdAt?: string
  resourceVersion?: string
  environmentalFunction?: {
    type?: string
    businessContext?: string
  }
  dependentAIModels: ModelGatewayDependentModel[]
  modelNames?: string
  trafficSplitStrategy?: string
  gateway?: Record<string, unknown>
  guardrails?: Record<string, unknown>
  jwtAuth?: Record<string, unknown>
  mcpServers?: Array<Record<string, unknown>>
  status?: Record<string, unknown>
  spec: Record<string, unknown>
}

export interface ModelGatewayServiceList {
  available: boolean
  items: ModelGatewayService[]
}

export interface ModelGatewayAvailability {
  available: boolean
}

export interface JsonSchemaNode {
  type?: string | string[]
  title?: string
  description?: string
  format?: string
  default?: unknown
  enum?: unknown[]
  properties?: Record<string, JsonSchemaNode>
  items?: JsonSchemaNode
  required?: string[]
  additionalProperties?: boolean | JsonSchemaNode
  minimum?: number
  maximum?: number
  minItems?: number
}

export interface ModelGatewayServiceSchema {
  apiVersion: string
  kind: string
  version: string
  scope: string
  schema: JsonSchemaNode
  specSchema: JsonSchemaNode
}

export interface ModelGatewayServicePayload {
  name: string
  namespace: string
  spec?: Record<string, unknown>
  specYaml?: string
}

export interface ModelGatewayValidationPayload extends ModelGatewayServicePayload {
  mode: 'create' | 'update'
}

export interface ModelGatewayValidationResult {
  valid: boolean
  spec: Record<string, unknown>
}

const BASE = '/api/model-gateway-services'

export async function fetchModelGatewayAvailability(): Promise<ModelGatewayAvailability> {
  const { data } = await apiClient.get<ModelGatewayAvailability>(`${BASE}/availability`)
  return data
}

export async function fetchModelGatewayServices(): Promise<ModelGatewayServiceList> {
  const { data } = await apiClient.get<ModelGatewayServiceList>(BASE)
  return data
}

export async function fetchModelGatewayServiceSchema(): Promise<ModelGatewayServiceSchema> {
  const { data } = await apiClient.get<ModelGatewayServiceSchema>(`${BASE}/schema`)
  return data
}

export async function validateModelGatewayService(
  payload: ModelGatewayValidationPayload,
): Promise<ModelGatewayValidationResult> {
  const { data } = await apiClient.post<ModelGatewayValidationResult>(`${BASE}/validate`, payload)
  return data
}

export async function createModelGatewayService(
  payload: ModelGatewayServicePayload,
): Promise<ModelGatewayService> {
  const { data } = await apiClient.post<ModelGatewayService>(BASE, payload)
  return data
}

export async function updateModelGatewayService(
  namespace: string,
  name: string,
  payload: { spec?: Record<string, unknown>; specYaml?: string },
): Promise<ModelGatewayService> {
  const { data } = await apiClient.put<ModelGatewayService>(`${BASE}/${namespace}/${name}`, payload)
  return data
}

export async function deleteModelGatewayService(namespace: string, name: string): Promise<void> {
  await apiClient.delete(`${BASE}/${namespace}/${name}`)
}

export interface ProxyTokenRequest {
  token_url: string
  client_id: string
  client_secret: string
  grant_type?: string
}

export interface ProxyChatRequest {
  gateway_url: string
  token: string
  model: string
  message: string
}

export async function proxyModelGatewayToken(payload: ProxyTokenRequest): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>(`${BASE}/proxy/token`, payload, {
    validateStatus: () => true,
  })
  return data
}

export async function proxyModelGatewayModels(
  gatewayUrl: string,
  token: string,
): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>(
    `${BASE}/proxy/models`,
    { gateway_url: gatewayUrl, token },
    { validateStatus: () => true },
  )
  return data
}

export async function proxyModelGatewayChat(payload: ProxyChatRequest): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>(`${BASE}/proxy/chat`, payload, {
    validateStatus: () => true,
  })
  return data
}
