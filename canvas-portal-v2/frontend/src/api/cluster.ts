import api from './client'

export interface ClusterOverview {
  nodes: { total: number; ready: number; notReady: number }
  pods: { total: number; running: number; pending: number; failed: number; allocatable: number }
  deployments: { total: number; available: number }
  services: number
  capacity: {
    cpuCores: number
    cpuUsed: number
    memoryBytes: number
    memoryUsed: number
  }
  version: string
  provider: string
  componentNamespaces: string[]
  componentNamespaceCount: number
  /**
   * Namespaces where the portal's backend SA actually has install/upgrade
   * RoleBindings (sourced from rbac.canvasInstallAccess.targetNamespaces).
   * The install/upgrade UI must constrain its namespace picker to this list.
   */
  installNamespaces: string[]
}

export const fetchClusterOverview = (): Promise<ClusterOverview> =>
  api.get('/api/cluster/overview').then((r) => r.data)
