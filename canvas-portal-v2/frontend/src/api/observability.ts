import apiClient from './client'

export type ObservabilityToolStatus = 'healthy' | 'unhealthy' | 'not_found' | 'declared'
export type ObservabilityToolSource = 'cluster' | 'chart'

export interface ObservabilityTool {
  id: 'langfuse' | 'grafana' | 'prometheus' | string
  name: string
  description: string
  available: boolean
  status: ObservabilityToolStatus
  source?: ObservabilityToolSource
  healthMessage?: string
  namespace?: string
  serviceName?: string
  publicUrl?: string
  internalUrl?: string
}

export interface ObservabilitySummary {
  tools: ObservabilityTool[]
}

export async function fetchObservabilitySummary(): Promise<ObservabilitySummary> {
  const { data } = await apiClient.get<ObservabilitySummary>('/api/observability')
  return data
}
