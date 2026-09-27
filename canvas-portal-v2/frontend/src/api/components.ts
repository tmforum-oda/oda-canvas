import apiClient from './client'
import { buildApiUrl } from '@/config'
import { getToken } from '@/lib/auth'

interface RawComponentStatusSummary {
  phase?: string | null
  message?: string | null
}

interface RawComponentStatus {
  phase?: string | null
  summary?: RawComponentStatusSummary | string | null
}

interface RawOdaComponent {
  name?: string | null
  namespace?: string | null
  version?: string | null
  status?: RawComponentStatus | string | null
  phase?: string | null
  canvasType?: string | null
  functionalBlock?: string | null
  description?: string | null
  labels?: Record<string, string> | null
  annotations?: Record<string, string> | null
  createdAt?: string | null
}

interface RawComponentCondition {
  type?: string | null
  status?: string | null
  message?: string | null
  reason?: string | null
  lastTransitionTime?: string | null
  last_transition_time?: string | null
}

interface RawComponentStatusPayload {
  phase?: string | null
  summaryMessage?: string | null
  summary?: RawComponentStatusSummary | null
  implementation?: Record<string, unknown> | null
  apiStatus?: Record<string, unknown> | null
  children?: unknown[] | null
  conditions?: RawComponentCondition[] | null
}

interface RawPodContainer {
  name?: string | null
  image?: string | null
  ready?: boolean | null
  restarts?: number | null
  state?: string | null
}

interface RawComponentPod {
  name?: string | null
  namespace?: string | null
  phase?: string | null
  ready?: boolean | null
  restarts?: number | null
  image?: string | null
  node?: string | null
  createdAt?: string | null
  startTime?: string | null
  containers?: RawPodContainer[] | null
}

interface RawComponentPodsResponse {
  pods?: RawComponentPod[] | null
}

interface RawComponentEvent {
  type?: string | null
  reason?: string | null
  message?: string | null
  count?: number | null
  firstTime?: string | null
  firstTimestamp?: string | null
  lastTime?: string | null
  lastTimestamp?: string | null
  involvedObject?: {
    kind?: string | null
    name?: string | null
    namespace?: string | null
  } | null
}

interface RawComponentEventsResponse {
  events?: RawComponentEvent[] | null
}

export interface OdaComponent {
  name: string
  namespace: string
  version: string
  status: string
  phase: string
  canvasType?: string
  functionalBlock?: string
  description?: string
  labels?: Record<string, string>
  annotations?: Record<string, string>
  createdAt?: string
}

export interface ComponentStatus {
  phase: string
  summaryMessage?: string
  conditions: Array<{
    type: string
    status: string
    message?: string
    reason?: string
    lastTransitionTime?: string
  }>
  implementation?: Record<string, unknown>
  apiStatus?: Record<string, unknown>
  children?: unknown[]
  observedGeneration?: number
}

export interface ComponentPod {
  name: string
  namespace: string
  phase: string
  ready: boolean
  restarts: number
  image: string
  node?: string
  createdAt?: string
  containers: Array<{
    name: string
    image: string
    ready: boolean
    restarts: number
    state: string
  }>
}

export interface ComponentEvent {
  type: string
  reason: string
  message: string
  count: number
  firstTime?: string
  lastTime?: string
  involvedObject?: {
    kind: string
    name: string
    namespace: string
  }
}

function resolveComponentStatus(rawStatus: RawOdaComponent['status'], phase: string): string {
  if (typeof rawStatus === 'string' && rawStatus.trim()) {
    return rawStatus
  }

  const normalizedPhase = phase.toLowerCase()
  if (normalizedPhase === 'complete') return 'ready'
  if (['in progress', 'progressing', 'pending'].includes(normalizedPhase)) return 'pending'
  if (normalizedPhase === 'failed') return 'failed'

  return phase || 'unknown'
}

function normalizeComponent(raw: RawOdaComponent): OdaComponent {
  const nestedStatus =
    raw.status && typeof raw.status === 'object' && !Array.isArray(raw.status)
      ? raw.status
      : undefined

  const nestedSummary =
    nestedStatus?.summary && typeof nestedStatus.summary === 'object'
      ? nestedStatus.summary
      : undefined

  const phase = raw.phase ?? nestedStatus?.phase ?? nestedSummary?.phase ?? ''
  const status = resolveComponentStatus(raw.status, phase)

  return {
    name: raw.name ?? '',
    namespace: raw.namespace ?? '',
    version: raw.version ?? '',
    status,
    phase,
    canvasType: raw.canvasType ?? undefined,
    functionalBlock: raw.functionalBlock ?? undefined,
    description: raw.description ?? undefined,
    labels: raw.labels ?? {},
    annotations: raw.annotations ?? {},
    createdAt: raw.createdAt ?? undefined,
  }
}

function normalizeCondition(raw: RawComponentCondition) {
  return {
    type: raw.type ?? 'Unknown',
    status: raw.status ?? 'Unknown',
    message: raw.message ?? undefined,
    reason: raw.reason ?? undefined,
    lastTransitionTime: raw.lastTransitionTime ?? raw.last_transition_time ?? undefined,
  }
}

function normalizePod(raw: RawComponentPod): ComponentPod {
  const containers = (raw.containers ?? []).map((container) => ({
    name: container.name ?? '',
    image: container.image ?? '',
    ready: container.ready ?? false,
    restarts: container.restarts ?? 0,
    state: container.state ?? 'unknown',
  }))

  return {
    name: raw.name ?? '',
    namespace: raw.namespace ?? '',
    phase: raw.phase ?? 'Unknown',
    ready: raw.ready ?? false,
    restarts: raw.restarts ?? containers.reduce((sum, container) => sum + container.restarts, 0),
    image: raw.image ?? containers[0]?.image ?? '',
    node: raw.node ?? undefined,
    createdAt: raw.createdAt ?? raw.startTime ?? undefined,
    containers,
  }
}

function normalizeEvent(raw: RawComponentEvent): ComponentEvent {
  return {
    type: raw.type ?? 'Normal',
    reason: raw.reason ?? '',
    message: raw.message ?? '',
    count: raw.count ?? 1,
    firstTime: raw.firstTime ?? raw.firstTimestamp ?? undefined,
    lastTime: raw.lastTime ?? raw.lastTimestamp ?? undefined,
    involvedObject: raw.involvedObject
      ? {
          kind: raw.involvedObject.kind ?? '',
          name: raw.involvedObject.name ?? '',
          namespace: raw.involvedObject.namespace ?? '',
        }
      : undefined,
  }
}

export async function fetchComponents(): Promise<OdaComponent[]> {
  const { data } = await apiClient.get<RawOdaComponent[]>('/api/components')
  return data.map(normalizeComponent)
}

export async function fetchComponent(namespace: string, name: string): Promise<OdaComponent> {
  const { data } = await apiClient.get<RawOdaComponent>(`/api/components/${namespace}/${name}`)
  return normalizeComponent(data)
}

export async function fetchComponentRaw(namespace: string, name: string): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get<Record<string, unknown>>(`/api/components/${namespace}/${name}/raw`)
  return data
}

export async function fetchComponentStatus(namespace: string, name: string): Promise<ComponentStatus> {
  const { data } = await apiClient.get<RawComponentStatusPayload>(`/api/components/${namespace}/${name}/status`)
  return {
    phase: data.phase ?? data.summary?.phase ?? 'Unknown',
    summaryMessage: data.summaryMessage ?? data.summary?.message ?? undefined,
    conditions: (data.conditions ?? []).map(normalizeCondition),
    implementation: data.implementation ?? undefined,
    apiStatus: data.apiStatus ?? undefined,
    children: data.children ?? undefined,
  }
}

export async function fetchComponentPods(namespace: string, name: string): Promise<ComponentPod[]> {
  const { data } = await apiClient.get<RawComponentPodsResponse | RawComponentPod[]>(
    `/api/components/${namespace}/${name}/pods`
  )
  const pods = Array.isArray(data) ? data : data.pods ?? []
  return pods.map(normalizePod)
}

export async function fetchComponentEvents(namespace: string, name: string): Promise<ComponentEvent[]> {
  const { data } = await apiClient.get<RawComponentEventsResponse | RawComponentEvent[]>(
    `/api/components/${namespace}/${name}/events`
  )
  const events = Array.isArray(data) ? data : data.events ?? []
  return events.map(normalizeEvent)
}

export interface ComponentApi {
  name: string
  specification?: string
  implementation?: string
  path?: string
  url?: string
  developerUI?: string
  ready: boolean | null
  port?: number | null
}

export interface ComponentApis {
  name: string
  namespace: string
  coreFunction: ComponentApi[]
  managementFunction: ComponentApi[]
  securityFunction: ComponentApi[]
}

export async function fetchComponentApis(namespace: string, name: string): Promise<ComponentApis> {
  const { data } = await apiClient.get<ComponentApis>(`/api/components/${namespace}/${name}/apis`)
  return data
}

export async function fetchComponentPodLogs(
  namespace: string,
  podName: string,
  tail = 200
): Promise<string> {
  const { data } = await apiClient.get<string>(
    `/api/pods/${namespace}/${podName}/logs`,
    { params: { tail }, responseType: 'text' }
  )
  return data
}

export interface StreamLogsOptions {
  tail?: number
  container?: string
  previous?: boolean
  onChunk: (text: string) => void
  onError?: (err: Error) => void
  onClose?: () => void
}

export function streamComponentPodLogs(
  namespace: string,
  podName: string,
  opts: StreamLogsOptions
): AbortController {
  const params = new URLSearchParams()
  if (opts.tail !== undefined) params.set('tail', String(opts.tail))
  if (opts.container) params.set('container', opts.container)
  if (opts.previous) params.set('previous', 'true')
  const url = buildApiUrl(`/api/pods/${namespace}/${podName}/logs/stream?${params}`)
  return streamLogs(url, opts)
}

function streamLogs(url: string, opts: StreamLogsOptions): AbortController {
  const controller = new AbortController()
  const token = getToken()

  ;(async () => {
    try {
      const resp = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
      if (!resp.ok) {
        throw new Error(`Stream failed: ${resp.status} ${resp.statusText}`)
      }
      if (!resp.body) {
        throw new Error('No response body for stream')
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        if (text) opts.onChunk(text)
      }
      const tail = decoder.decode()
      if (tail) opts.onChunk(tail)
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        opts.onError?.(err as Error)
      }
    } finally {
      opts.onClose?.()
    }
  })()

  return controller
}

export { streamLogs as _streamLogsInternal }
