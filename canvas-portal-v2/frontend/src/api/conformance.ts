import api from './client'

export type CanvasConformanceRunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'
export type CanvasConformanceRunMode = 'tags' | 'features'

export interface CanvasConformanceConfig {
  repo_url: string
  branch: string
  default_tags: string
  keycloak_base_url: string
  keycloak_realm: string
}

export interface CanvasConformanceResultSummary {
  total: number
  passed: number
  failed: number
  skipped: number
}

export interface CanvasConformanceRun {
  id: string
  suite: 'canvas'
  status: CanvasConformanceRunStatus
  mode: CanvasConformanceRunMode
  repo_url: string
  branch: string
  tags: string
  features: string[]
  created_by: string
  started_at?: string | null
  finished_at?: string | null
  duration_seconds?: number | null
  phase: string
  progress: number
  message: string
  exit_code?: number | null
  result: CanvasConformanceResultSummary
  log_tail: string[]
  log_path?: string | null
  cucumber_json_path?: string | null
}

export interface CanvasConformanceRunList {
  runs: CanvasConformanceRun[]
  active_run?: CanvasConformanceRun | null
}

export interface CanvasConformanceCatalog {
  repo: string
  branch: string
  path: string
  features: string[]
  use_case_tags: string[]
  feature_tags: string[]
}

export interface CanvasConformanceRunPayload {
  // repo_url/branch are server-pinned (Helm config) — callers can't choose the repo.
  mode: CanvasConformanceRunMode
  tags?: string
  features?: string[]
}

export const getCanvasConformanceConfig = (): Promise<CanvasConformanceConfig> =>
  api.get('/api/conformance/canvas/config').then((r) => r.data)

export const getCanvasConformanceCatalog = (
  refresh = false,
): Promise<CanvasConformanceCatalog> =>
  api
    .get('/api/conformance/canvas/catalog', { params: refresh ? { refresh: true } : undefined })
    .then((r) => r.data)

export const listCanvasConformanceRuns = (limit = 20): Promise<CanvasConformanceRunList> =>
  api.get('/api/conformance/canvas/runs', { params: { limit } }).then((r) => r.data)

export const startCanvasConformanceRun = (
  payload: CanvasConformanceRunPayload,
): Promise<CanvasConformanceRun> =>
  api.post('/api/conformance/canvas/runs', payload).then((r) => r.data)

export const getCanvasConformanceRun = (id: string): Promise<CanvasConformanceRun> =>
  api.get(`/api/conformance/canvas/runs/${encodeURIComponent(id)}`).then((r) => r.data)

export const getCanvasConformanceLogs = (id: string, tail = 500): Promise<string[]> =>
  api
    .get(`/api/conformance/canvas/runs/${encodeURIComponent(id)}/logs`, { params: { tail } })
    .then((r) => r.data.lines)

async function downloadFromApi(path: string, filename: string, mimeType: string): Promise<void> {
  const response = await api.get(path, { responseType: 'blob' })
  const blob = new Blob([response.data], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const downloadCanvasConformanceLog = (id: string): Promise<void> =>
  downloadFromApi(
    `/api/conformance/canvas/runs/${encodeURIComponent(id)}/logs/download`,
    `canvas-conformance-${id}.log`,
    'text/plain',
  )

export const downloadCanvasConformanceCucumberJson = (id: string): Promise<void> =>
  downloadFromApi(
    `/api/conformance/canvas/runs/${encodeURIComponent(id)}/cucumber.json/download`,
    `canvas-conformance-${id}.cucumber.json`,
    'application/json',
  )

export const downloadCanvasConformanceReportHtml = (id: string): Promise<void> =>
  downloadFromApi(
    `/api/conformance/canvas/runs/${encodeURIComponent(id)}/report.html/download`,
    `canvas-conformance-${id}.report.html`,
    'text/html',
  )

export const deleteCanvasConformanceRun = (id: string): Promise<void> =>
  api.delete(`/api/conformance/canvas/runs/${encodeURIComponent(id)}`).then(() => undefined)
