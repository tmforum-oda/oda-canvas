import apiClient from './client'
import { getToken } from '@/lib/auth'
import { buildApiUrl } from '@/config'

interface RawOperatorContainer {
  name?: string | null
  image?: string | null
  ready?: boolean | null
  restarts?: number | null
  state?: string | null
}

interface RawOperatorPod {
  name?: string | null
  namespace?: string | null
  phase?: string | null
  ready?: boolean | null
  restarts?: number | null
  image?: string | null
  createdAt?: string | null
  startTime?: string | null
  node?: string | null
  podIP?: string | null
  containers?: RawOperatorContainer[] | null
}

interface RawOperator {
  name?: string | null
  deploymentName?: string | null
  containerName?: string | null
  sharedDeployment?: boolean | null
  namespace?: string | null
  status?: string | null
  desired?: number | null
  ready?: number | null
  available?: number | null
  updated?: number | null
  image?: string | null
  pods?: RawOperatorPod[] | null
  version?: string | null
  createdAt?: string | null
  selector?: Record<string, string> | null
  labels?: Record<string, string> | null
  strategy?: string | null
  tmfId?: string | null
  tmfName?: string | null
}

export interface OperatorContainer {
  name: string
  image: string
  ready: boolean
  restarts: number
  state: string
}

export interface OperatorPod {
  name: string
  namespace: string
  phase: string
  ready: boolean
  restarts: number
  image: string
  createdAt?: string
  node?: string
  podIP?: string
  containers: OperatorContainer[]
}

export interface Operator {
  name: string
  deploymentName: string
  containerName?: string
  sharedDeployment?: boolean
  namespace: string
  status: string         // "running" | "down" | "degraded"
  desired: number
  ready: number
  available: number
  updated: number
  image: string
  pods: OperatorPod[]
  version?: string
  createdAt?: string
  selector?: Record<string, string>
  labels?: Record<string, string>
  strategy?: string
  tmfId?: string
  tmfName?: string
}

function normalizeOperatorPod(raw: RawOperatorPod): OperatorPod {
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
    createdAt: raw.createdAt ?? raw.startTime ?? undefined,
    node: raw.node ?? undefined,
    podIP: raw.podIP ?? undefined,
    containers,
  }
}

function normalizeOperator(raw: RawOperator): Operator {
  return {
    name: raw.name ?? '',
    deploymentName: raw.deploymentName ?? raw.name ?? '',
    containerName: raw.containerName ?? undefined,
    sharedDeployment: raw.sharedDeployment ?? undefined,
    namespace: raw.namespace ?? '',
    status: raw.status ?? 'unknown',
    desired: raw.desired ?? 0,
    ready: raw.ready ?? 0,
    available: raw.available ?? 0,
    updated: raw.updated ?? 0,
    image: raw.image ?? '',
    pods: (raw.pods ?? []).map(normalizeOperatorPod),
    version: raw.version ?? undefined,
    createdAt: raw.createdAt ?? undefined,
    selector: raw.selector ?? undefined,
    labels: raw.labels ?? undefined,
    strategy: raw.strategy ?? undefined,
    tmfId: raw.tmfId ?? undefined,
    tmfName: raw.tmfName ?? undefined,
  }
}

export async function fetchOperators(): Promise<Operator[]> {
  const { data } = await apiClient.get<RawOperator[]>('/api/operators')
  return data.map(normalizeOperator)
}

export async function fetchOperator(namespace: string, name: string): Promise<Operator> {
  const { data } = await apiClient.get<RawOperator>(`/api/operators/${namespace}/${name}`)
  return normalizeOperator(data)
}

export async function fetchOperatorPodLogs(
  namespace: string,
  name: string,
  pod: string,
  tail = 200,
  container?: string
): Promise<string> {
  const { data } = await apiClient.get<string>(
    `/api/operators/${namespace}/${name}/pods/${pod}/logs`,
    {
      params: {
        tail,
        ...(container ? { container } : {}),
      },
      responseType: 'text',
    }
  )
  return data
}

export async function fetchPods(namespace: string): Promise<OperatorPod[]> {
  const { data } = await apiClient.get<RawOperatorPod[]>(`/api/pods/${namespace}`)
  return data.map(normalizeOperatorPod)
}

import { _streamLogsInternal, type StreamLogsOptions } from './components'

export function streamOperatorPodLogs(
  namespace: string,
  name: string,
  pod: string,
  opts: StreamLogsOptions
): AbortController {
  const params = new URLSearchParams()
  if (opts.tail !== undefined) params.set('tail', String(opts.tail))
  if (opts.container) params.set('container', opts.container)
  if (opts.previous) params.set('previous', 'true')
  const url = buildApiUrl(
    `/api/operators/${namespace}/${name}/pods/${pod}/logs/stream?${params}`
  )
  return _streamLogsInternal(url, opts)
}

export async function downloadPodLogs(namespace: string, pod: string): Promise<void> {
  const token = getToken()
  const url = buildApiUrl(`/api/pods/${namespace}/${pod}/logs`)

  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!response.ok) throw new Error(`Failed to download logs: ${response.statusText}`)

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = `${pod}-logs.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(objectUrl)
}
