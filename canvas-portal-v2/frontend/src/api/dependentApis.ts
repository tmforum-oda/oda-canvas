import apiClient from './client'

export interface DependentAPI {
  apiVersion?: string
  name: string
  namespace: string
  apiName?: string            // logical API name (e.g. "downstreamproductcatalog")
  apiType?: string            // "openapi" | ...
  segment?: string            // "coreFunction" | "managementFunction" | "securityFunction"
  componentName?: string      // owning Component (from oda.tmforum.org/componentName label)
  specificationUrl?: string   // Swagger / spec URL declared by the component
  version?: string            // e.g. "v4"
  ready: boolean              // operator-resolved
  resolvedUrl?: string        // URL the operator wired up to satisfy this dependency
  svcInvID?: string           // service inventory id, if resolved
  createdAt?: string
}

export async function fetchDependentApis(): Promise<DependentAPI[]> {
  const { data } = await apiClient.get<DependentAPI[]>('/api/dependentapis')
  return data
}

export async function fetchDependentApi(namespace: string, name: string): Promise<DependentAPI> {
  const { data } = await apiClient.get<DependentAPI>(`/api/dependentapis/${namespace}/${name}`)
  return data
}
