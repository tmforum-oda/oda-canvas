import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Tabs, Card, Tag, Spin, Alert, Table, Tooltip, Button, Segmented, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ArrowLeftOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ApiOutlined,
  CodeOutlined,
  CopyOutlined,
  DownloadOutlined,
  LinkOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'
import {
  fetchComponent,
  fetchComponentRaw,
  fetchComponentStatus,
  fetchComponentPods,
  fetchComponentEvents,
  fetchComponentPodLogs,
  streamComponentPodLogs,
  fetchComponentApis,
  type ComponentPod,
  type ComponentEvent,
  type ComponentApi,
} from '@/api/components'
import StatusBadge from '@/components/StatusBadge'
import PodList from '@/components/PodList'
import LogViewer from '@/components/LogViewer'
import { colors } from '@/theme'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 0',
        borderBottom: `1px solid ${colors.border}`,
      }}
    >
      <span style={{ fontSize: 13, color: colors.textSecondary, minWidth: 160 }}>{label}</span>
      <span style={{ fontSize: 13, color: colors.textPrimary }}>{value}</span>
    </div>
  )
}

interface ComponentDetailBodyProps {
  namespace: string
  name: string
  onClose?: () => void
}

export default function ComponentDetailBody({ namespace, name, onClose }: ComponentDetailBodyProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [logPod, setLogPod] = useState<ComponentPod | null>(null)
  const [rawFormat, setRawFormat] = useState<'yaml' | 'json'>('yaml')

  const { data: rawComponent, isLoading: loadingRaw, error: rawError } = useQuery({
    queryKey: ['component-raw', namespace, name],
    queryFn: () => fetchComponentRaw(namespace, name),
    enabled: activeTab === 'raw' && !!namespace && !!name,
  })

  const { data: component, isLoading: loadingComponent } = useQuery({
    queryKey: ['component', namespace, name],
    queryFn: () => fetchComponent(namespace, name),
    enabled: !!namespace && !!name,
  })

  const { data: status, isLoading: loadingStatus } = useQuery({
    queryKey: ['component-status', namespace, name],
    queryFn: () => fetchComponentStatus(namespace, name),
    enabled: activeTab === 'status' && !!namespace && !!name,
  })

  const { data: pods, isLoading: loadingPods } = useQuery({
    queryKey: ['component-pods', namespace, name],
    queryFn: () => fetchComponentPods(namespace, name),
    enabled: (activeTab === 'pods' || activeTab === 'overview') && !!namespace && !!name,
  })

  const { data: events, isLoading: loadingEvents } = useQuery({
    queryKey: ['component-events', namespace, name],
    queryFn: () => fetchComponentEvents(namespace, name),
    enabled: activeTab === 'events' && !!namespace && !!name,
  })

  const { data: apis, isLoading: loadingApis } = useQuery({
    queryKey: ['component-apis', namespace, name],
    queryFn: () => fetchComponentApis(namespace, name),
    enabled: activeTab === 'apis' && !!namespace && !!name,
  })

  function ApiGroup({ title, apis: groupApis }: { title: string; apis: ComponentApi[] }) {
    if (!groupApis || groupApis.length === 0) return null
    return (
      <div style={{ marginBottom: 20 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: colors.textMuted,
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: 10,
          }}
        >
          {title}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {groupApis.map((api) => (
            <div
              key={api.name}
              style={{
                background: colors.surfaceSubtle,
                border: `1px solid ${colors.border}`,
                borderRadius: 10,
                padding: '14px 16px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: api.url ? 10 : 0 }}>
                {api.ready === true ? (
                  <CheckCircleOutlined style={{ color: colors.statusLive, fontSize: 14, flexShrink: 0 }} />
                ) : api.ready === false ? (
                  <CloseCircleOutlined style={{ color: colors.statusDown, fontSize: 14, flexShrink: 0 }} />
                ) : (
                  <MinusCircleOutlined style={{ color: colors.textMuted, fontSize: 14, flexShrink: 0 }} />
                )}
                <span style={{ fontWeight: 600, color: colors.textPrimary, fontSize: 13, flex: 1, minWidth: 0 }}>
                  {api.name}
                </span>
                {api.ready !== null && (
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: api.ready ? colors.statusLive : colors.statusDown,
                      background: api.ready ? `${colors.statusLive}18` : `${colors.statusDown}18`,
                      border: `1px solid ${api.ready ? colors.statusLive : colors.statusDown}40`,
                      borderRadius: 999,
                      padding: '1px 8px',
                    }}
                  >
                    {api.ready ? 'ready' : 'not ready'}
                  </span>
                )}
              </div>
              {(api.url || api.developerUI || api.specification) && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginLeft: 24 }}>
                  {api.url && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 11, color: colors.textMuted, width: 80 }}>URL</span>
                      <a
                        href={api.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: 12, color: colors.primary, fontFamily: 'monospace', wordBreak: 'break-all' }}
                      >
                        {api.url} <LinkOutlined style={{ fontSize: 10 }} />
                      </a>
                    </div>
                  )}
                  {api.developerUI && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 11, color: colors.textMuted, width: 80 }}>Developer UI</span>
                      <a
                        href={api.developerUI}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: 12, color: colors.primary, fontFamily: 'monospace', wordBreak: 'break-all' }}
                      >
                        {api.developerUI} <LinkOutlined style={{ fontSize: 10 }} />
                      </a>
                    </div>
                  )}
                  {api.specification && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 11, color: colors.textMuted, width: 80 }}>Spec</span>
                      <span style={{ fontSize: 12, color: colors.textSecondary, fontFamily: 'monospace' }}>{api.specification}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (loadingComponent) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!component) {
    return (
      <Alert
        type="error"
        message={`Component ${namespace}/${name} not found`}
        action={onClose ? <Button onClick={onClose}>Close</Button> : undefined}
      />
    )
  }

  const eventColumns: ColumnsType<ComponentEvent> = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 90,
      render: (type: string) => (
        <span
          style={{
            color: type === 'Warning' ? colors.statusDeprecated : colors.statusLive,
            fontWeight: 600,
            fontSize: 12,
          }}
        >
          {type}
        </span>
      ),
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      width: 160,
      render: (reason: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: colors.textSecondary }}>
          {reason}
        </span>
      ),
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      render: (msg: string) => (
        <span style={{ fontSize: 12, color: colors.textPrimary }}>{msg}</span>
      ),
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      width: 70,
      render: (count: number) => (
        <span style={{ color: count > 1 ? colors.statusDeprecated : colors.textMuted }}>{count}</span>
      ),
    },
    {
      title: 'Last Seen',
      dataIndex: 'lastTime',
      key: 'lastTime',
      width: 120,
      render: (t?: string) =>
        t ? (
          <Tooltip title={dayjs(t).format('YYYY-MM-DD HH:mm:ss')}>
            <span style={{ color: colors.textMuted, fontSize: 12 }}>{dayjs(t).fromNow()}</span>
          </Tooltip>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
  ]

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Card
            style={{
              flex: 1,
              minWidth: 280,
              background: colors.surfaceSubtle,
              border: `1px solid ${colors.border}`,
              borderRadius: 10,
            }}
            bodyStyle={{ padding: '16px 20px' }}
          >
            <div style={{ fontWeight: 600, color: colors.textMuted, marginBottom: 12, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Component Info
            </div>
            <InfoRow label="Name" value={component.name} />
            <InfoRow label="Namespace" value={
              <Tag style={{ background: colors.infoSurface, color: colors.infoText, border: 'none', borderRadius: 4, fontFamily: 'monospace', fontSize: 12 }}>
                {component.namespace}
              </Tag>
            } />
            <InfoRow label="Version" value={component.version ? `v${component.version}` : '—'} />
            <InfoRow label="Status" value={<StatusBadge status={component.status || 'unknown'} />} />
            <InfoRow label="Phase" value={component.phase || '—'} />
            {component.createdAt && (
              <InfoRow
                label="Created"
                value={
                  <Tooltip title={dayjs(component.createdAt).format('YYYY-MM-DD HH:mm:ss')}>
                    <span>{dayjs(component.createdAt).fromNow()}</span>
                  </Tooltip>
                }
              />
            )}
          </Card>

          {/* Labels & Annotations */}
          {(Object.keys(component.labels || {}).length > 0 || Object.keys(component.annotations || {}).length > 0) && (
            <Card
              style={{
                flex: 1,
                minWidth: 280,
                background: colors.surfaceSubtle,
                border: `1px solid ${colors.border}`,
                borderRadius: 10,
              }}
              bodyStyle={{ padding: '16px 20px' }}
            >
              {Object.keys(component.labels || {}).length > 0 && (
                <>
                  <div style={{ fontWeight: 600, color: colors.textMuted, marginBottom: 10, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Labels
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                    {Object.entries(component.labels || {}).map(([k, v]) => (
                      <Tag key={k} style={{ fontSize: 11, fontFamily: 'monospace', background: colors.hoverSurface, color: colors.textSecondary, border: 'none' }}>
                        {k}={v}
                      </Tag>
                    ))}
                  </div>
                </>
              )}
            </Card>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      children: loadingStatus ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spin /></div>
      ) : status ? (
        <div>
          {status.summaryMessage && (
            <div
              style={{
                marginBottom: 16,
                padding: '12px 16px',
                background: colors.surfaceSubtle,
                borderRadius: 8,
                border: `1px solid ${colors.border}`,
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: colors.textMuted,
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                  marginBottom: 6,
                }}
              >
                Operator Summary
              </div>
              <div style={{ fontSize: 13, color: colors.textPrimary }}>
                {status.summaryMessage}
              </div>
            </div>
          )}
          <div style={{ marginBottom: 16 }}>
            <span style={{ fontSize: 13, color: colors.textSecondary, marginRight: 8 }}>Phase:</span>
            <StatusBadge status={status.phase} />
          </div>
          {status.conditions && status.conditions.length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                Conditions
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {status.conditions.map((cond, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 12,
                      padding: '12px 16px',
                      background: colors.surfaceSubtle,
                      borderRadius: 8,
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    {cond.status === 'True' ? (
                      <CheckCircleOutlined style={{ color: colors.statusLive, fontSize: 16, marginTop: 1 }} />
                    ) : (
                      <CloseCircleOutlined style={{ color: colors.statusDown, fontSize: 16, marginTop: 1 }} />
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: colors.textPrimary }}>{cond.type}</span>
                        {cond.reason && (
                          <Tag style={{ fontSize: 11, background: colors.hoverSurface, color: colors.textSecondary, border: 'none', borderRadius: 4 }}>
                            {cond.reason}
                          </Tag>
                        )}
                      </div>
                      {cond.message && (
                        <span style={{ fontSize: 12, color: colors.textMuted }}>{cond.message}</span>
                      )}
                    </div>
                    {cond.lastTransitionTime && (
                      <span style={{ fontSize: 11, color: colors.textMuted, whiteSpace: 'nowrap' }}>
                        {dayjs(cond.lastTransitionTime).fromNow()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ color: colors.textMuted, padding: 24 }}>No status information available.</div>
      ),
    },
    {
      key: 'pods',
      label: `Pods${pods ? ` (${pods.length})` : ''}`,
      children: logPod ? (
        <div>
          <Button
            icon={<ArrowLeftOutlined />}
            type="text"
            style={{ color: colors.textSecondary, marginBottom: 16 }}
            onClick={() => setLogPod(null)}
          >
            Back to Pod List
          </Button>
          <LogViewer
            key={logPod.name}
            title={`${logPod.name} logs`}
            filename={`${logPod.name}-logs.txt`}
            fetchLogs={(tail) => fetchComponentPodLogs(namespace, logPod.name, tail)}
            streamLogs={(opts) => streamComponentPodLogs(namespace, logPod.name, opts)}
          />
        </div>
      ) : (
        <PodList
          pods={pods ?? []}
          loading={loadingPods}
          onViewLogs={(pod) => setLogPod(pod)}
        />
      ),
    },
    {
      key: 'events',
      label: `Events${events ? ` (${events.length})` : ''}`,
      children: (
        <Table<ComponentEvent>
          columns={eventColumns}
          dataSource={events ?? []}
          rowKey={(r, idx) => `${r.reason}-${idx}`}
          loading={loadingEvents}
          size="small"
          pagination={false}
          style={{ background: 'transparent' }}
        />
      ),
    },
    {
      key: 'apis',
      label: (
        <span>
          <ApiOutlined style={{ marginRight: 6 }} />
          APIs
        </span>
      ),
      children: loadingApis ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spin /></div>
      ) : apis ? (
        <div>
          {apis.coreFunction.length === 0 && apis.managementFunction.length === 0 && apis.securityFunction.length === 0 ? (
            <div style={{ color: colors.textMuted, padding: '24px 0', textAlign: 'center' }}>
              No API definitions found in this component's spec.
            </div>
          ) : (
            <>
              <ApiGroup title="Core Function" apis={apis.coreFunction} />
              <ApiGroup title="Management Function" apis={apis.managementFunction} />
              <ApiGroup title="Security Function" apis={apis.securityFunction} />
            </>
          )}
        </div>
      ) : (
        <div style={{ color: colors.textMuted, padding: '24px 0' }}>Select this tab to load API info.</div>
      ),
    },
    {
      key: 'raw',
      label: (
        <span>
          <CodeOutlined style={{ marginRight: 6 }} />
          Raw
        </span>
      ),
      children: (
        <RawDocumentView
          loading={loadingRaw}
          error={rawError as Error | null}
          data={rawComponent}
          format={rawFormat}
          onFormatChange={setRawFormat}
          filenameBase={`${namespace}-${name}`}
        />
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: colors.primaryGradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 20,
          }}
        >
          <AppstoreOutlined />
        </div>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
            {component.name}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
            <Tag style={{ background: colors.infoSurface, color: colors.infoText, border: 'none', borderRadius: 4, fontFamily: 'monospace', fontSize: 12 }}>
              {component.namespace}
            </Tag>
            <StatusBadge status={component.status || 'unknown'} size="sm" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          background: colors.bgCard,
          borderRadius: 12,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems.map(t => ({
            ...t,
            children: <div style={{ padding: '20px 4px' }}>{t.children}</div>,
          }))}
          style={{ padding: '0 20px' }}
          tabBarStyle={{
            borderBottom: `1px solid ${colors.border}`,
            marginBottom: 0,
          }}
          tabBarGutter={24}
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Raw component document viewer (YAML / JSON toggle + copy + download).
// Self-contained YAML serializer covers Kubernetes resource shapes; no extra
// dependency.
// ---------------------------------------------------------------------------

function RawDocumentView({
  loading,
  error,
  data,
  format,
  onFormatChange,
  filenameBase,
}: {
  loading: boolean
  error: Error | null
  data?: Record<string, unknown>
  format: 'yaml' | 'json'
  onFormatChange: (next: 'yaml' | 'json') => void
  filenameBase: string
}) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
        <Spin />
      </div>
    )
  }
  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        message="Failed to load raw component"
        description={(error as Error).message}
      />
    )
  }
  if (!data) {
    return <div style={{ color: colors.textMuted, padding: '24px 0' }}>Select this tab to load the raw resource.</div>
  }

  const text = format === 'yaml' ? toYaml(data) : JSON.stringify(data, null, 2)

  const onCopy = async () => {
    try {
      // navigator.clipboard is only available in secure contexts (HTTPS or
      // localhost). The portal is often served over plain HTTP, so fall back
      // to a hidden-textarea + execCommand('copy') when it's unavailable.
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        const ta = document.createElement('textarea')
        ta.value = text
        ta.style.position = 'fixed'
        ta.style.top = '-9999px'
        ta.style.opacity = '0'
        document.body.appendChild(ta)
        ta.focus()
        ta.select()
        const ok = document.execCommand('copy')
        document.body.removeChild(ta)
        if (!ok) throw new Error('execCommand copy failed')
      }
      message.success('Copied')
    } catch {
      message.error('Copy failed')
    }
  }
  const onDownload = () => {
    const blob = new Blob([text], { type: format === 'yaml' ? 'text/yaml;charset=utf-8' : 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filenameBase}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
        <Segmented
          value={format}
          onChange={(value) => onFormatChange(value as 'yaml' | 'json')}
          options={[
            { label: 'YAML', value: 'yaml' },
            { label: 'JSON', value: 'json' },
          ]}
        />
        <Button icon={<CopyOutlined />} onClick={onCopy}>Copy</Button>
        <Button icon={<DownloadOutlined />} onClick={onDownload}>Download .{format}</Button>
        <span style={{ marginLeft: 'auto', fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
          {filenameBase}.{format}
        </span>
      </div>
      <pre
        style={{
          background: colors.surfaceInsetStrong,
          color: colors.textPrimary,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          padding: '14px 16px',
          fontFamily: '"JetBrains Mono", "Fira Code", ui-monospace, monospace',
          fontSize: 12,
          lineHeight: 1.55,
          maxHeight: '60vh',
          overflow: 'auto',
          margin: 0,
          whiteSpace: 'pre',
        }}
      >
        {text}
      </pre>
    </div>
  )
}

// Minimal block-style YAML serializer for the Raw view. Handles strings,
// numbers, booleans, null, lists, and dicts — i.e. every shape that comes back
// from the Kubernetes API. Quotes scalars that look like YAML keywords or
// contain reserved characters; folds nothing (preserves multiline strings as
// quoted scalars). Not a general-purpose emitter, just enough to render the CR.
function toYaml(value: unknown, indent = 0): string {
  const pad = '  '.repeat(indent)
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'boolean' || typeof value === 'number') return String(value)
  if (typeof value === 'string') return formatYamlScalar(value)

  if (Array.isArray(value)) {
    if (value.length === 0) return '[]'
    return value
      .map((item) => {
        if (item !== null && typeof item === 'object') {
          const block = toYaml(item, indent + 1)
          // First line of the block prefixed with "- ", subsequent lines re-indented.
          const lines = block.split('\n')
          const head = lines[0].replace(/^ +/, '')
          const tail = lines.slice(1)
          return `${pad}- ${head}` + (tail.length ? '\n' + tail.join('\n') : '')
        }
        return `${pad}- ${toYaml(item, 0)}`
      })
      .join('\n')
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (entries.length === 0) return '{}'
    return entries
      .map(([key, child]) => {
        const k = /^[A-Za-z_][A-Za-z0-9_.\-/]*$/.test(key) ? key : JSON.stringify(key)
        if (child === null || child === undefined) return `${pad}${k}: null`
        if (typeof child === 'object') {
          if (Array.isArray(child) && child.length === 0) return `${pad}${k}: []`
          if (!Array.isArray(child) && Object.keys(child as Record<string, unknown>).length === 0) {
            return `${pad}${k}: {}`
          }
          return `${pad}${k}:\n${toYaml(child, indent + 1)}`
        }
        return `${pad}${k}: ${toYaml(child, 0)}`
      })
      .join('\n')
  }

  return JSON.stringify(value)
}

function formatYamlScalar(value: string): string {
  if (value === '') return '""'
  if (value.includes('\n')) return JSON.stringify(value)
  // Quote scalars that YAML would otherwise reinterpret as bool/null/number/etc.
  if (/^(true|false|null|yes|no|on|off|~|-)$/i.test(value)) return JSON.stringify(value)
  if (/^-?\d+(\.\d+)?$/.test(value)) return JSON.stringify(value)
  // Quote anything containing YAML control characters.
  if (/^[\s>&*!|%@`]/.test(value) || /[:#{}\[\],&*!|>'"%@`]/.test(value) && !/^[A-Za-z0-9_./-]+$/.test(value)) {
    return JSON.stringify(value)
  }
  return value
}
