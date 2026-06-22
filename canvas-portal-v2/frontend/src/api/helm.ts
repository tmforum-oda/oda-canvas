import api from './client'

export interface HelmRelease {
  name: string
  namespace: string
  chart: string
  app_version?: string
  status: string
  updated?: string
}

export interface HelmInstallPayload {
  release_name: string
  chart: string
  namespace: string
  repo_name?: string
  version?: string
  repo_url?: string
  create_namespace?: boolean
  values?: Record<string, unknown>
  values_yaml?: string  // Raw YAML string from the values editor; takes precedence over values dict
  timeout_minutes?: number  // Helm --timeout in minutes (default 5). Server clamps to [1, 60].
}

export interface HelmChartValuesParams {
  chart?: string
  repo_url?: string
  version?: string
}

export interface HelmUninstallPayload {
  release_name: string
  namespace: string
}

export interface HelmRepository {
  name: string
  url: string
  status: string
  error?: string | null
  chart_count: number
  last_synced_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface HelmRepositoryPayload {
  name: string
  url: string
}

export interface HelmRepositoryChartVersion {
  version: string
  app_version?: string | null
}

export interface HelmRepositoryChart {
  name: string
  full_name: string
  repo_name: string
  repo_url: string
  description: string
  latest_version: string
  latest_app_version?: string | null
  versions: HelmRepositoryChartVersion[]
}

/** List all helm releases, optionally filtered by namespace. */
export const listHelmReleases = (namespace?: string): Promise<HelmRelease[]> =>
  api
    .get('/api/helm/releases', { params: namespace ? { namespace } : {} })
    .then((r) => r.data)

export const listHelmRepositories = (): Promise<HelmRepository[]> =>
  api.get('/api/helm/repos').then((r) => r.data)

export const addHelmRepository = (
  payload: HelmRepositoryPayload,
): Promise<HelmRepository> =>
  api.post('/api/helm/repos', payload).then((r) => r.data)

export const syncHelmRepository = (repoName: string): Promise<HelmRepository> =>
  api.post(`/api/helm/repos/${encodeURIComponent(repoName)}/sync`).then((r) => r.data)

export const deleteHelmRepository = (repoName: string): Promise<{ success: boolean; name: string }> =>
  api.delete(`/api/helm/repos/${encodeURIComponent(repoName)}`).then((r) => r.data)

export const listHelmRepositoryCharts = (
  repoName: string,
): Promise<HelmRepositoryChart[]> =>
  api.get('/api/helm/repo-charts', { params: { repo_name: repoName } }).then((r) => r.data)

/**
 * Fetch the default values.yaml for a chart (helm show values).
 * Returns the raw YAML string so it can be displayed in the editor.
 */
export const getChartValues = (
  params: HelmChartValuesParams,
): Promise<string> =>
  api
    .get('/api/helm/values', {
      params: {
        ...(params.chart ? { chart: params.chart } : {}),
        ...(params.repo_url ? { repo_url: params.repo_url } : {}),
        ...(params.version ? { version: params.version } : {}),
      },
    })
    .then((r) => r.data.values as string)

/**
 * Fetch the user-supplied values that an existing release was last upgraded
 * with. Equivalent to `helm get values <release> -n <ns> -o yaml`.
 */
export const getReleaseValues = (release_name: string, namespace: string): Promise<string> =>
  api
    .get('/api/helm/releases/values', { params: { release: release_name, namespace } })
    .then((r) => r.data.values as string)

/** Install (or upgrade) a helm chart. */
export const installHelmChart = (payload: HelmInstallPayload): Promise<{ success: boolean; release_name: string; namespace: string; message: string }> =>
  api.post('/api/helm/install', payload).then((r) => r.data)

/** Uninstall a helm release. */
export const uninstallHelmChart = (payload: HelmUninstallPayload): Promise<{ success: boolean; release_name: string; message: string }> =>
  api.delete('/api/helm/uninstall', { data: payload }).then((r) => r.data)

export interface HelmRevision {
  revision: number
  updated: string
  status: string
  chart: string
  app_version?: string
  description: string
}

/** Fetch the revision history for a Helm release. */
export const getHelmHistory = (release: string, namespace: string): Promise<HelmRevision[]> =>
  api.get('/api/helm/history', { params: { release, namespace } }).then((r) => r.data)
