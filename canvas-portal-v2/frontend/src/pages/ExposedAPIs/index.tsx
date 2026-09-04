import React, { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  ApiOutlined,
  AppstoreOutlined,
  ClusterOutlined,
  ExperimentOutlined,
  ExpandOutlined,
  LinkOutlined,
  NodeIndexOutlined,
  ReloadOutlined,
  SafetyOutlined,
  SearchOutlined,

  ThunderboltOutlined,
} from '@ant-design/icons'
import {
  Button,
  Empty,
  Input,
  Segmented,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Tooltip,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'

import {
  fetchExposedApis,
  fetchGatewayResources,
  type ExposedAPI,
  type GatewayBinding,
  type Policy,
} from '@/api/exposedApis'
import {
  fetchDependentApis,
  type DependentAPI,
} from '@/api/dependentApis'
import ApiRelationshipGraph from '@/components/ApiRelationshipGraph'
import StatusBadge from '@/components/StatusBadge'
import { colors } from '@/theme'

type TabKey = 'exposedapis' | 'dependentapis' | 'gateway' | 'servicemesh' | 'policies'

type PolicyRow = {
  key: string
  binding: GatewayBinding
  policy: Policy
}

const TAB_TO_PATH: Record<TabKey, string> = {
  exposedapis: '/exposedapis',
  dependentapis: '/dependentapis',
  gateway: '/gateway',
  servicemesh: '/servicemesh',
  policies: '/policies',
}

const PATH_TO_TAB: Record<string, TabKey> = {
  '/exposedapis': 'exposedapis',
  '/dependentapis': 'dependentapis',
  '/gateway': 'gateway',
  '/servicemesh': 'servicemesh',
  '/ratelimiting': 'policies',
  '/policies': 'policies',
}

const PLUGIN_LABELS: Record<string, string> = {
  'jwt': 'JWT',
  'jwt-auth': 'JWT',
  'oauth2': 'OAuth 2.0',
  'oidc': 'OIDC',
  'openid-connect': 'OIDC',
  'key-auth': 'API Key',
  'basic-auth': 'Basic Auth',
  'hmac-auth': 'HMAC Auth',
  'rate-limiting': 'Rate Limiting',
  'response-ratelimiting': 'Rate Limiting',
  'limit-req': 'Rate Limiting',
  'limit-count': 'Rate Limiting',
  'limit-conn': 'Rate Limiting',
  'cors': 'CORS',
  'ip-restriction': 'IP Restrict',
  'request-transformer': 'Transform',
  'proxy-cache': 'Cache',
  'proxy-rewrite': 'Transform',
  'acl': 'ACL',
  'consumer-restriction': 'Consumer Restriction',
}

const AUTH_PLUGINS = new Set([
  'jwt',
  'jwt-auth',
  'oauth2',
  'oidc',
  'openid-connect',
  'key-auth',
  'basic-auth',
  'hmac-auth',
])

const RATE_LIMIT_PLUGINS = new Set([
  'rate-limiting',
  'response-ratelimiting',
  'limit-req',
  'limit-count',
  'limit-conn',
])

function formatApiName(name: string): string {
  return name
    .replace(/^(oda-|canvas-|component-)/i, '')
    .replace(/-api$/, '')
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function normalizePluginType(type?: string): string {
  return type?.toLowerCase() ?? ''
}

function canvasTypeColor(canvasType?: string) {
  if (canvasType === 'kong') return { bg: 'rgba(34,197,94,0.1)', text: colors.statusLive }
  if (canvasType === 'apisix') return { bg: 'rgba(251,146,60,0.12)', text: '#fb923c' }
  return { bg: colors.infoSurface, text: colors.infoText }
}

function gatewayKindColor(kind?: string) {
  if (kind === 'HTTPRoute') return { bg: 'rgba(34,197,94,0.1)', text: colors.statusLive }
  if (kind === 'ApisixRoute') return { bg: 'rgba(251,146,60,0.12)', text: '#fb923c' }
  return { bg: colors.surfaceSelected, text: colors.tmfText }
}

function pluginColor(type?: string) {
  const normalized = normalizePluginType(type)
  if (AUTH_PLUGINS.has(normalized)) return { bg: 'rgba(34,197,94,0.1)', text: colors.statusLive }
  if (RATE_LIMIT_PLUGINS.has(normalized)) return { bg: 'rgba(251,146,60,0.12)', text: '#fb923c' }
  if (normalized === 'cors') return { bg: colors.infoSurface, text: colors.infoText }
  return { bg: 'rgba(100,116,139,0.12)', text: colors.textSecondary }
}

function getPolicyLabel(type?: string): string {
  const normalized = normalizePluginType(type)
  return PLUGIN_LABELS[normalized] ?? (type || 'Unknown')
}

function asText(value: unknown): string | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return null
}

function getPolicySummary(policy: Policy): string | null {
  const cfg = policy.config ?? {}
  const parts: string[] = []

  const second = asText(cfg.second)
  const minute = asText(cfg.minute)
  const hour = asText(cfg.hour)
  const count = asText(cfg.count)
  const timeWindow = asText(cfg.time_window)
  const issuer = asText(cfg.issuer)
  const keyClaimName = asText(cfg.key_claim_name)
  const key = asText(cfg.key)
  const rejectedCode = asText(cfg.rejected_code)

  if (second) parts.push(`${second}/s`)
  if (minute) parts.push(`${minute}/min`)
  if (hour) parts.push(`${hour}/hr`)
  if (!second && !minute && !hour && count && timeWindow) parts.push(`${count}/${timeWindow}s`)
  else if (!second && !minute && !hour && count) parts.push(count)
  if (issuer) parts.push(`issuer: ${issuer}`)
  if (keyClaimName) parts.push(`claim: ${keyClaimName}`)
  if (key && !RATE_LIMIT_PLUGINS.has(normalizePluginType(policy.pluginType))) parts.push(`key: ${key}`)
  if (rejectedCode) parts.push(`HTTP ${rejectedCode}`)

  const secretRef = cfg.secret_ref
  if (secretRef && typeof secretRef === 'object') {
    const name = asText((secretRef as Record<string, unknown>).name)
    if (name) parts.push(`secret: ${name}`)
  }

  return parts.length ? parts.slice(0, 3).join(' · ') : null
}

function getAuthLabel(policies?: Policy[]): string | null {
  if (!policies?.length) return null
  for (const policy of policies) {
    if (AUTH_PLUGINS.has(normalizePluginType(policy.pluginType))) {
      return getPolicyLabel(policy.pluginType)
    }
  }
  return null
}

function getRateLimitLabel(policies?: Policy[]): string | null {
  if (!policies?.length) return null
  for (const policy of policies) {
    if (RATE_LIMIT_PLUGINS.has(normalizePluginType(policy.pluginType))) {
      return getPolicySummary(policy) ?? 'Enabled'
    }
  }
  return null
}

function getBindings(record: ExposedAPI): GatewayBinding[] {
  if (record.gatewayResources?.length) return record.gatewayResources
  if (!record.gatewayResource) return []

  return [
    {
      ...record.gatewayResource,
      canvasType: record.canvasType ?? 'istio',
      details: record.gatewayDetails,
      policies: record.policies,
      relatedExposedApi: {
        name: record.name,
        namespace: record.namespace,
        url: record.url,
        status: record.status,
      },
    },
  ]
}

function matchesSearch(value: string, query: string): boolean {
  return value.toLowerCase().includes(query.toLowerCase())
}

function TmfBadge() {
  return (
    <Tag
      style={{
        background: colors.tmfBg,
        color: colors.tmfText,
        border: 'none',
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
        padding: '1px 8px',
      }}
    >
      TMF
    </Tag>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 700,
        color: colors.textMuted,
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  )
}

function DetailList({ label, values }: { label: string; values?: string[] }) {
  if (!values?.length) return null
  return (
    <div style={{ fontSize: 11, color: colors.textSecondary }}>
      {label}: {values.join(', ')}
    </div>
  )
}

function PluginPill({ policy }: { policy: Policy }) {
  const pc = pluginColor(policy.pluginType)
  return (
    <Tag
      style={{
        background: pc.bg,
        color: pc.text,
        border: 'none',
        borderRadius: 4,
        fontSize: 10,
        margin: 0,
      }}
    >
      {getPolicyLabel(policy.pluginType)}
    </Tag>
  )
}

type ResourceTreeNode = {
  label: string
  details?: string[]
  children?: ResourceTreeNode[]
}

function uniqueStrings(values: Array<string | undefined>): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const value of values) {
    if (!value || seen.has(value)) continue
    seen.add(value)
    result.push(value)
  }
  return result
}

function resourceVersionLabel(resource: { apiVersion?: string; group?: string }): string {
  return resource.apiVersion || resource.group || 'unknown'
}

function getReferencedPluginNames(binding: GatewayBinding): string[] {
  return uniqueStrings([
    ...(binding.details?.pluginNames ?? []),
    ...((binding.policies ?? [])
      .map((policy) => policy.name)
      .filter((name): name is string => Boolean(name))),
  ])
}

function getPluginReferenceLabels(binding: GatewayBinding): string[] {
  const kongPluginNames = getReferencedPluginNames(binding)
  if (kongPluginNames.length) return kongPluginNames
  return uniqueStrings(binding.details?.pluginConfigNames ?? [])
}

function buildKongPluginNodes(binding: GatewayBinding): ResourceTreeNode[] {
  const nodes: ResourceTreeNode[] = []
  const seenNames = new Set<string>()

  ;(binding.policies ?? []).forEach((policy) => {
    if (policy.name) seenNames.add(policy.name)
    const details = [
      ...(policy.name ? [`name: ${policy.name}`] : []),
      `type: ${policy.pluginType}`,
      ...(getPolicySummary(policy) ? [`config: ${getPolicySummary(policy)}`] : []),
    ]
    nodes.push({
      label: 'KongPlugin (configuration.konghq.com/v1)',
      details,
    })
  })

  getReferencedPluginNames(binding).forEach((name) => {
    if (seenNames.has(name)) return
    nodes.push({
      label: 'KongPlugin (configuration.konghq.com/v1)',
      details: [`name: ${name}`],
    })
  })

  return nodes
}

function buildApisixPluginConfigNodes(binding: GatewayBinding): ResourceTreeNode[] {
  const configNames = binding.details?.pluginConfigNames ?? []
  const pluginNodes = (binding.policies ?? []).map((policy) => ({
    label: `${getPolicyLabel(policy.pluginType)} Plugin`,
    details: [
      ...(policy.name ? [`name: ${policy.name}`] : []),
      `type: ${policy.pluginType}`,
      ...(getPolicySummary(policy) ? [`config: ${getPolicySummary(policy)}`] : []),
    ],
  }))

  if (!configNames.length && !pluginNodes.length) return []

  return [
    {
      label: 'ApisixPluginConfig (apisix.apache.org/v2)',
      details: configNames.length ? [`name: ${configNames.join(', ')}`] : undefined,
      children: pluginNodes.length ? pluginNodes : undefined,
    },
  ]
}

function buildGenericPolicyNodes(binding: GatewayBinding): ResourceTreeNode[] {
  return (binding.policies ?? []).map((policy) => ({
    label: `${getPolicyLabel(policy.pluginType)} Policy`,
    details: [
      ...(policy.name ? [`name: ${policy.name}`] : []),
      `type: ${policy.pluginType}`,
      ...(getPolicySummary(policy) ? [`config: ${getPolicySummary(policy)}`] : []),
    ],
  }))
}

function buildGatewayBindingTreeNode(binding: GatewayBinding): ResourceTreeNode {
  const details = [
    `name: ${binding.name}`,
    ...(binding.namespace ? [`namespace: ${binding.namespace}`] : []),
    ...(binding.details?.gateways?.length ? [`gateways: ${binding.details.gateways.join(', ')}`] : []),
    ...(binding.details?.hostnames?.length ? [`hostnames: ${binding.details.hostnames.join(', ')}`] : []),
    ...(binding.details?.hosts?.length ? [`hosts: ${binding.details.hosts.join(', ')}`] : []),
    ...(binding.details?.paths?.length ? [`paths: ${binding.details.paths.join(', ')}`] : []),
    ...(binding.details?.backendRefs?.length ? [`backends: ${binding.details.backendRefs.join(', ')}`] : []),
  ]

  const children: ResourceTreeNode[] = []

  if (binding.kind === 'HTTPRoute') {
    const pluginNodes = buildKongPluginNodes(binding)
    if (pluginNodes.length) {
      children.push({
        label: 'KongPlugins',
        children: pluginNodes,
      })
    }
  } else if (binding.kind === 'ApisixRoute') {
    children.push(...buildApisixPluginConfigNodes(binding))
  } else if (binding.policies?.length) {
    children.push({
      label: 'Policies',
      children: buildGenericPolicyNodes(binding),
    })
  }

  return {
    label: `${binding.kind} (${resourceVersionLabel(binding)})`,
    details,
    children: children.length ? children : undefined,
  }
}

function buildExposedApiTree(record: ExposedAPI): ResourceTreeNode {
  const bindings = getBindings(record)

  return {
    label: `ExposedAPI (${record.apiVersion || 'oda.tmforum.org/v1beta3'})`,
    details: [
      `name: ${record.name}`,
      `namespace: ${record.namespace}`,
      ...(record.url ? [`endpoint: ${record.url}`] : []),
    ],
    children: bindings.map((binding) => buildGatewayBindingTreeNode(binding)),
  }
}

function formatTreeLines(node: ResourceTreeNode, prefix = '', isLast = true, isRoot = true): string[] {
  const connector = isRoot ? '' : (isLast ? '└── ' : '├── ')
  const branchIndent = isRoot ? '' : `${prefix}${isLast ? '    ' : '│   '}`
  const lines = [`${prefix}${connector}${node.label}`]

  for (const detail of node.details ?? []) {
    lines.push(`${branchIndent}${detail}`)
  }

  const children = node.children ?? []
  children.forEach((child, index) => {
    lines.push(...formatTreeLines(child, branchIndent, index === children.length - 1, false))
  })

  return lines
}

function ResourceTopologyTree({ record }: { record: ExposedAPI }) {
  const lines = formatTreeLines(buildExposedApiTree(record))

  return (
    <pre
      style={{
        margin: 0,
        padding: 16,
        background: colors.surfaceSubtle,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        color: colors.textSecondary,
        fontSize: 12,
        lineHeight: 1.7,
        fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {lines.join('\n')}
    </pre>
  )
}

function GatewayBindingCard({ binding }: { binding: GatewayBinding }) {
  const gc = gatewayKindColor(binding.kind)
  const cc = canvasTypeColor(binding.canvasType)
  const relatedExposedApi = binding.relatedExposedApi
  const referencedPluginNames = getReferencedPluginNames(binding)

  return (
    <div
      style={{
        minWidth: 260,
        flex: 1,
        padding: 14,
        background: colors.surfaceSubtle,
        borderRadius: 8,
        border: `1px solid ${colors.border}`,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Tag style={{ background: gc.bg, color: gc.text, border: 'none', borderRadius: 4, fontSize: 11 }}>
          {binding.kind}
        </Tag>
        <Tag style={{ background: cc.bg, color: cc.text, border: 'none', borderRadius: 4, fontSize: 11 }}>
          {binding.canvasType}
        </Tag>
        <span style={{ fontSize: 12, fontFamily: 'monospace', color: colors.textPrimary }}>
          {binding.name}
        </span>
      </div>
      <div style={{ fontSize: 11, color: colors.textMuted }}>
        namespace: <code>{binding.namespace}</code>
      </div>
      <div style={{ fontSize: 11, color: colors.textMuted }}>
        apiVersion: <code>{resourceVersionLabel(binding)}</code>
      </div>
      {relatedExposedApi ? (
        <div style={{ fontSize: 11, color: colors.textSecondary }}>
          related ExposedAPI: <code>{relatedExposedApi.namespace}/{relatedExposedApi.name}</code>
        </div>
      ) : (
        <div style={{ fontSize: 11, color: colors.textMuted }}>No related ExposedAPI found</div>
      )}
      <DetailList label="hosts" values={binding.details?.hosts} />
      <DetailList label="hostnames" values={binding.details?.hostnames} />
      <DetailList label="gateways" values={binding.details?.gateways} />
      <DetailList label="paths" values={binding.details?.paths} />
      <DetailList label="backends" values={binding.details?.backendRefs} />
      <DetailList label="plugin configs" values={binding.details?.pluginConfigNames} />
      {!binding.policies?.length && referencedPluginNames.length ? (
        <DetailList label="referenced plugins" values={referencedPluginNames} />
      ) : null}
      {binding.policies?.length ? (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {binding.policies.map((policy, index) => (
            <Tooltip
              key={`${binding.kind}-${binding.name}-${policy.pluginType}-${index}`}
              title={getPolicySummary(policy) ?? policy.name ?? 'Plugin attached'}
            >
              <span>
                <PluginPill policy={policy} />
              </span>
            </Tooltip>
          ))}
        </div>
      ) : (
        <span style={{ fontSize: 11, color: colors.textMuted }}>No plugins attached</span>
      )}
    </div>
  )
}

function ExpandedApiRow({ record }: { record: ExposedAPI }) {
  const bindings = getBindings(record)

  return (
    <div
      style={{
        padding: '18px 24px',
        background: colors.surfaceInsetStrong,
        borderTop: `1px solid ${colors.border}`,
        display: 'flex',
        gap: 24,
        flexWrap: 'wrap',
      }}
    >
      <div style={{ minWidth: 260 }}>
        <SectionLabel>Endpoint URL</SectionLabel>
        {record.url ? (
          <a
            href={record.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: colors.primary,
              fontSize: 12,
              fontFamily: 'monospace',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              wordBreak: 'break-all',
            }}
          >
            <LinkOutlined />
            {record.url}
          </a>
        ) : (
          <span style={{ color: colors.textMuted, fontSize: 12 }}>Not configured</span>
        )}
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <SectionLabel>Resource Topology</SectionLabel>
        {bindings.length ? (
          <ResourceTopologyTree record={record} />
        ) : (
          <span style={{ fontSize: 12, color: colors.textMuted }}>
            No gateway resource or plugins found for this API.
          </span>
        )}
      </div>

      {record.error && (
        <div style={{ fontSize: 12, color: colors.statusDown, fontFamily: 'monospace' }}>
          {record.error}
        </div>
      )}
    </div>
  )
}

function ExposedAPIsTable() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [apiTypeFilter, setApiTypeFilter] = useState<string>('all')
  const [namespaceFilter, setNamespaceFilter] = useState<string>('all')
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  const { data: apis, isLoading, isError, refetch } = useQuery({
    queryKey: ['exposedapis'],
    queryFn: fetchExposedApis,
  })

  const namespaceOptions = useMemo(() => {
    const seen = new Set<string>()
    for (const api of apis ?? []) {
      if (api.namespace) seen.add(api.namespace)
    }
    return [
      { value: 'all', label: 'All Namespaces' },
      ...Array.from(seen).sort().map((ns) => ({ value: ns, label: ns })),
    ]
  }, [apis])

  const filtered = (apis ?? []).filter((api) => {
    const query = search.trim()
    const bindings = getBindings(api)
    const matchSearch =
      !query ||
      matchesSearch(api.name, query) ||
      matchesSearch(api.namespace, query) ||
      matchesSearch(api.url ?? '', query) ||
      bindings.some((binding) => matchesSearch(binding.name, query))

    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'live' && api.status?.toLowerCase() === 'ready') ||
      (statusFilter === 'down' && api.status?.toLowerCase() !== 'ready')

    const matchApiType =
      apiTypeFilter === 'all' ||
      (api.apiType ?? 'openapi').toLowerCase() === apiTypeFilter

    const matchNamespace =
      namespaceFilter === 'all' || api.namespace === namespaceFilter

    return matchSearch && matchStatus && matchApiType && matchNamespace
  })

  function toggleExpand(key: string) {
    setExpandedRows((previous) =>
      previous.includes(key) ? previous.filter((rowKey) => rowKey !== key) : [...previous, key]
    )
  }

  const columns: ColumnsType<ExposedAPI> = [
    {
      title: 'API Name',
      key: 'name',
      render: (_value: unknown, record) => (
        <span style={{ fontWeight: 600, fontSize: 13, color: colors.textPrimary }}>
          {record.name || '—'}
        </span>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      sorter: (a, b) => (a.status || '').localeCompare(b.status || ''),
      render: (_value: unknown, record) => (
        <StatusBadge
          status={record.status?.toLowerCase() === 'ready' ? 'live' : 'down'}
          label={record.status?.toLowerCase() === 'ready' ? 'LIVE' : 'DOWN'}
        />
      ),
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      width: 90,
      render: (value?: string) =>
        value ? (
          <span style={{ color: colors.textSecondary, fontSize: 12 }}>v{value}</span>
        ) : (
          <Tag
            style={{
              fontSize: 11,
              background: colors.hoverSurface,
              color: colors.textMuted,
              border: 'none',
            }}
          >
            latest
          </Tag>
        ),
    },
    {
      title: 'Auth',
      key: 'auth',
      width: 120,
      render: (_value: unknown, record) => {
        const label = getAuthLabel(record.policies)
        return label ? (
          <Tag
            style={{
              background: 'rgba(34,197,94,0.1)',
              color: colors.statusLive,
              border: 'none',
              borderRadius: 4,
              fontSize: 11,
            }}
          >
            <SafetyOutlined style={{ marginRight: 4 }} />
            {label}
          </Tag>
        ) : (
          <span style={{ color: colors.textMuted, fontSize: 12 }}>—</span>
        )
      },
    },
    {
      title: 'Rate Limit',
      key: 'rateLimit',
      width: 140,
      render: (_value: unknown, record) => {
        const label = getRateLimitLabel(record.policies)
        return label ? (
          <Tag
            style={{
              background: 'rgba(251,146,60,0.12)',
              color: '#fb923c',
              border: 'none',
              borderRadius: 4,
              fontSize: 11,
            }}
          >
            <ThunderboltOutlined style={{ marginRight: 4 }} />
            {label}
          </Tag>
        ) : (
          <span style={{ color: colors.textMuted, fontSize: 12 }}>—</span>
        )
      },
    },
    {
      title: 'Plugins',
      key: 'plugins',
      width: 140,
      render: (_value: unknown, record) => {
        const count = record.policies?.length ?? 0
        if (!count) return <span style={{ color: colors.textMuted, fontSize: 12 }}>none</span>

        return (
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {record.policies!.slice(0, 3).map((policy, index) => (
              <PluginPill key={`${policy.pluginType}-${index}`} policy={policy} />
            ))}
            {count > 3 && (
              <Tag
                style={{
                  background: colors.surfaceMuted,
                  color: colors.textMuted,
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 10,
                  margin: 0,
                }}
              >
                +{count - 3}
              </Tag>
            )}
          </div>
        )
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_value: unknown, record) => {
        const rowKey = `${record.namespace}/${record.name}`
        const expanded = expandedRows.includes(rowKey)
        const isOpenApi = (record.apiType ?? 'openapi').toLowerCase() === 'openapi'

        return (
          <Space size={6}>
            <Tooltip title="Test API endpoint">
              <Button
                size="small"
                icon={<ExperimentOutlined />}
                style={{
                  background: 'rgba(34,197,94,0.1)',
                  border: '1px solid rgba(34,197,94,0.3)',
                  color: colors.statusLive,
                  borderRadius: 6,
                  height: 28,
                }}
                onClick={(event) => {
                  event.stopPropagation()
                  if (record.url) window.open(record.url, '_blank')
                }}
              />
            </Tooltip>

            {isOpenApi && record.url && (
              <Tooltip title="Open Swagger UI">
                <Button
                  size="small"
                  icon={<LinkOutlined />}
                  style={{
                    background: 'rgba(99,102,241,0.1)',
                    border: `1px solid ${colors.primary}40`,
                    color: colors.primary,
                    borderRadius: 6,
                    height: 28,
                    fontSize: 11,
                    paddingInline: 8,
                  }}
                  onClick={(event) => {
                    event.stopPropagation()
                    const docsUrl = record.url!.replace(/\/$/, '') + '/docs'
                    window.open(docsUrl, '_blank')
                  }}
                >
                  Docs
                </Button>
              </Tooltip>
            )}

            <Tooltip title={expanded ? 'Collapse details' : 'View gateway & plugin details'}>
              <Button
                size="small"
                icon={<ExpandOutlined />}
                style={{
                  background: expanded ? colors.surfaceSelected : 'transparent',
                  border: `1px solid ${expanded ? colors.primary : colors.border}`,
                  color: expanded ? colors.primary : colors.textSecondary,
                  borderRadius: 6,
                  height: 28,
                }}
                onClick={(event) => {
                  event.stopPropagation()
                  toggleExpand(rowKey)
                }}
              />
            </Tooltip>
          </Space>
        )
      },
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input
            placeholder="Search APIs by name, namespace, URL or gateway..."
            prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            value={apiTypeFilter}
            onChange={setApiTypeFilter}
            style={{ width: 150 }}
            options={[
              { value: 'all', label: 'All API Types' },
              { value: 'openapi', label: 'OpenAPI' },
              { value: 'mcp', label: 'MCP' },
              { value: 'prometheus', label: 'Prometheus' },
              { value: 'openmetrics', label: 'OpenMetrics' },
              { value: 'a2a', label: 'A2A' },
            ]}
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 160 }}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'live', label: 'Live (Ready)' },
              { value: 'down', label: 'Down (Not Ready)' },
            ]}
          />
          <Select
            value={namespaceFilter}
            onChange={setNamespaceFilter}
            showSearch
            optionFilterProp="label"
            style={{ width: 200 }}
            options={namespaceOptions}
          />
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: colors.textMuted }}>
            {filtered.length} API{filtered.length !== 1 ? 's' : ''}
          </span>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          />
        </div>
      </div>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: 10,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        {isError && (
          <div style={{ padding: 16, color: colors.statusDown }}>
            Failed to load exposed APIs. Please try again.
          </div>
        )}
        <Table<ExposedAPI>
          columns={columns}
          dataSource={filtered}
          rowKey={(record) => `${record.namespace}/${record.name}`}
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => <span style={{ color: colors.textMuted }}>{total} APIs</span>,
          }}
          size="middle"
          expandable={{
            expandedRowKeys: expandedRows,
            onExpand: (expanded, record) => {
              const rowKey = `${record.namespace}/${record.name}`
              if (expanded) setExpandedRows((previous) => [...previous, rowKey])
              else setExpandedRows((previous) => previous.filter((key) => key !== rowKey))
            },
            expandedRowRender: (record) => <ExpandedApiRow record={record} />,
            expandIcon: () => null,
            showExpandColumn: false,
          }}
          scroll={{ x: 1200 }}
        />
      </div>
    </div>
  )
}

const MESH_TYPES = new Set(['istio'])
const GATEWAY_TYPES = new Set(['kong', 'apisix'])

function GatewayResourcesTable({ mode = 'gateway' }: { mode?: 'gateway' | 'mesh' }) {
  const [search, setSearch] = useState('')
  const [canvasFilter, setCanvasFilter] = useState<string>('all')
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  const { data: resources, isLoading, isError, refetch } = useQuery({
    queryKey: ['gateway-resources'],
    queryFn: fetchGatewayResources,
  })

  const modeFiltered = (resources ?? []).filter((binding) =>
    mode === 'mesh'
      ? MESH_TYPES.has(binding.canvasType ?? '')
      : !MESH_TYPES.has(binding.canvasType ?? '')
  )

  const filtered = modeFiltered.filter((binding) => {
    const query = search.trim()
    const related = binding.relatedExposedApi
    const matchSearch =
      !query ||
      matchesSearch(binding.name, query) ||
      matchesSearch(binding.namespace ?? '', query) ||
      matchesSearch(binding.kind ?? '', query) ||
      matchesSearch(related?.name ?? '', query) ||
      matchesSearch(related?.namespace ?? '', query) ||
      (binding.details?.paths ?? []).some((path) => matchesSearch(path, query))

    const matchCanvas = canvasFilter === 'all' || binding.canvasType === canvasFilter
    return matchSearch && matchCanvas
  })

  const columns: ColumnsType<GatewayBinding> = [
    {
      title: 'Gateway Resource',
      key: 'resource',
      render: (_value: unknown, record) => {
        const gc = gatewayKindColor(record.kind)
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <Tag style={{ background: gc.bg, color: gc.text, border: 'none', borderRadius: 4, fontSize: 10 }}>
              {record.kind}
            </Tag>
            <span style={{ fontWeight: 600, color: colors.textPrimary, fontSize: 13 }}>
              {record.name}
            </span>
          </div>
        )
      },
    },
    {
      title: 'ExposedAPI',
      key: 'relatedExposedApi',
      width: 240,
      render: (_value: unknown, record) => (
        record.relatedExposedApi ? (
          <span style={{ fontWeight: 600, color: colors.textPrimary, fontSize: 12 }}>
            {formatApiName(record.relatedExposedApi.name)}
          </span>
        ) : (
          <span style={{ color: colors.textMuted, fontSize: 12 }}>Unlinked</span>
        )
      ),
    },
    {
      title: 'Routes',
      key: 'routes',
      width: 260,
      render: (_value: unknown, record) => {
        const values = [
          ...(record.details?.hostnames ?? []),
          ...(record.details?.hosts ?? []),
          ...(record.details?.paths ?? []),
        ]

        if (!values.length) return <span style={{ color: colors.textMuted, fontSize: 12 }}>—</span>

        return (
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {values.slice(0, 3).map((value) => (
              <Tag
                key={value}
                style={{
                  background: colors.surfaceMuted,
                  color: colors.textSecondary,
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 10,
                  margin: 0,
                }}
              >
                {value}
              </Tag>
            ))}
            {values.length > 3 && (
              <Tag
                style={{
                  background: colors.surfaceMuted,
                  color: colors.textMuted,
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 10,
                  margin: 0,
                }}
              >
                +{values.length - 3}
              </Tag>
            )}
          </div>
        )
      },
    },
    {
      title: 'Plugins',
      key: 'plugins',
      width: 170,
      render: (_value: unknown, record) => {
        const policies = record.policies ?? []
        const references = getPluginReferenceLabels(record)
        if (!policies.length && !references.length) return <span style={{ color: colors.textMuted, fontSize: 12 }}>none</span>

        if (!policies.length) {
          return (
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {references.slice(0, 3).map((name) => (
                <Tag
                  key={name}
                  style={{
                    background: colors.surfaceMuted,
                    color: colors.textSecondary,
                    border: 'none',
                    borderRadius: 4,
                    fontSize: 10,
                    margin: 0,
                    fontFamily: 'monospace',
                  }}
                >
                  {name}
                </Tag>
              ))}
              {references.length > 3 && (
                <Tag
                  style={{
                    background: colors.surfaceMuted,
                    color: colors.textMuted,
                    border: 'none',
                    borderRadius: 4,
                    fontSize: 10,
                    margin: 0,
                  }}
                >
                  +{references.length - 3}
                </Tag>
              )}
            </div>
          )
        }

        return (
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {policies.slice(0, 3).map((policy, index) => (
              <PluginPill key={`${policy.pluginType}-${index}`} policy={policy} />
            ))}
            {policies.length > 3 && (
              <Tag
                style={{
                  background: colors.surfaceMuted,
                  color: colors.textMuted,
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 10,
                  margin: 0,
                }}
              >
                +{policies.length - 3}
              </Tag>
            )}
          </div>
        )
      },
    },
    {
      title: 'Details',
      key: 'actions',
      width: 100,
      render: (_value: unknown, record) => {
        const rowKey = `${record.kind}/${record.namespace}/${record.name}`
        const expanded = expandedRows.includes(rowKey)
        return (
          <Button
            size="small"
            icon={<ExpandOutlined />}
            style={{
              background: expanded ? colors.surfaceSelected : 'transparent',
              border: `1px solid ${expanded ? colors.primary : colors.border}`,
              color: expanded ? colors.primary : colors.textSecondary,
              borderRadius: 6,
              height: 28,
            }}
            onClick={(event) => {
              event.stopPropagation()
              setExpandedRows((previous) =>
                previous.includes(rowKey)
                  ? previous.filter((key) => key !== rowKey)
                  : [...previous, rowKey]
              )
            }}
          />
        )
      },
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input
            placeholder={mode === 'mesh' ? 'Search mesh resources or related APIs...' : 'Search gateway resources, routes or related APIs...'}
            prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            allowClear
            style={{ width: 340 }}
          />
          {mode !== 'mesh' && (
            <Select
              value={canvasFilter}
              onChange={setCanvasFilter}
              style={{ width: 160 }}
              options={[
                { value: 'all', label: 'All Canvas Types' },
                { value: 'kong', label: 'Kong' },
                { value: 'apisix', label: 'APISIX' },
              ]}
            />
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: colors.textMuted }}>
            {filtered.length} {mode === 'mesh' ? 'mesh' : 'gateway'} resource{filtered.length !== 1 ? 's' : ''}
          </span>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          />
        </div>
      </div>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: 10,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        {isError && (
          <div style={{ padding: 16, color: colors.statusDown }}>
            Failed to load gateway resources. Please try again.
          </div>
        )}
        <Table<GatewayBinding>
          columns={columns}
          dataSource={filtered}
          rowKey={(record) => `${record.kind}/${record.namespace}/${record.name}`}
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => (
              <span style={{ color: colors.textMuted }}>{total} {mode === 'mesh' ? 'mesh' : 'gateway'} resources</span>
            ),
          }}
          expandable={{
            expandedRowKeys: expandedRows,
            onExpand: (expanded, record) => {
              const rowKey = `${record.kind}/${record.namespace}/${record.name}`
              if (expanded) setExpandedRows((previous) => [...previous, rowKey])
              else setExpandedRows((previous) => previous.filter((key) => key !== rowKey))
            },
            expandedRowRender: (record) => (
              <div
                style={{
                  padding: '18px 24px',
                  background: colors.surfaceInsetStrong,
                  borderTop: `1px solid ${colors.border}`,
                }}
              >
                <GatewayBindingCard binding={record} />
              </div>
            ),
            expandIcon: () => null,
            showExpandColumn: false,
          }}
          scroll={{ x: 1200 }}
        />
      </div>
    </div>
  )
}

function RateLimitingTable() {
  const [search, setSearch] = useState('')
  const { data: resources, isLoading, isError, refetch } = useQuery({
    queryKey: ['gateway-resources'],
    queryFn: fetchGatewayResources,
  })

  const rows = useMemo<PolicyRow[]>(() => {
    return (resources ?? []).flatMap((binding) =>
      (binding.policies ?? [])
        .filter((policy) => RATE_LIMIT_PLUGINS.has(normalizePluginType(policy.pluginType)))
        .map((policy, index) => ({
          key: `${binding.kind}/${binding.namespace}/${binding.name}/${policy.pluginType}/${index}`,
          binding,
          policy,
        }))
    )
  }, [resources])

  const filtered = rows.filter((row) => {
    const query = search.trim()
    return (
      !query ||
      matchesSearch(row.binding.name, query) ||
      matchesSearch(row.binding.namespace ?? '', query) ||
      matchesSearch(row.binding.relatedExposedApi?.name ?? '', query) ||
      matchesSearch(getPolicyLabel(row.policy.pluginType), query) ||
      matchesSearch(getPolicySummary(row.policy) ?? '', query)
    )
  })

  const columns: ColumnsType<PolicyRow> = [
    {
      title: 'API / Resource',
      key: 'resource',
      render: (_value: unknown, record) => (
        <div>
          <div style={{ fontWeight: 600, color: colors.textPrimary, fontSize: 13 }}>
            {record.binding.relatedExposedApi
              ? formatApiName(record.binding.relatedExposedApi.name)
              : record.binding.name}
          </div>
          <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
            {record.binding.relatedExposedApi
              ? `${record.binding.relatedExposedApi.namespace}/${record.binding.relatedExposedApi.name}`
              : `${record.binding.namespace}/${record.binding.name}`}
          </div>
        </div>
      ),
    },
    {
      title: 'Gateway',
      key: 'gateway',
      width: 240,
      render: (_value: unknown, record) => {
        const gc = gatewayKindColor(record.binding.kind)
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Tag style={{ background: gc.bg, color: gc.text, border: 'none', borderRadius: 4, fontSize: 10 }}>
                {record.binding.kind}
              </Tag>
              <span style={{ fontSize: 11, fontFamily: 'monospace', color: colors.textSecondary }}>
                {record.binding.name}
              </span>
            </div>
            <span style={{ fontSize: 11, color: colors.textMuted }}>{record.binding.canvasType}</span>
          </div>
        )
      },
    },
    {
      title: 'Plugin',
      key: 'plugin',
      width: 160,
      render: (_value: unknown, record) => <PluginPill policy={record.policy} />,
    },
    {
      title: 'Rule',
      key: 'rule',
      render: (_value: unknown, record) => (
        <span style={{ color: colors.textSecondary, fontSize: 12 }}>
          {getPolicySummary(record.policy) ?? 'Enabled'}
        </span>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_value: unknown, record) => (
        <StatusBadge
          status={record.policy.enabled === false ? 'down' : 'live'}
          label={record.policy.enabled === false ? 'DISABLED' : 'ACTIVE'}
        />
      ),
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Input
          placeholder="Search rate limiting by API, gateway or rule..."
          prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          allowClear
          style={{ width: 340 }}
        />
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: colors.textMuted }}>
            {filtered.length} rate-limit policy{filtered.length !== 1 ? 'ies' : ''}
          </span>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          />
        </div>
      </div>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: 10,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        {isError && (
          <div style={{ padding: 16, color: colors.statusDown }}>
            Failed to load rate limiting policies. Please try again.
          </div>
        )}
        {!isLoading && filtered.length === 0 ? (
          <div style={{ padding: 32 }}>
            <Empty
              description={
                <span style={{ color: colors.textMuted }}>
                  No rate-limiting plugins are currently attached to discovered gateway resources.
                </span>
              }
            />
          </div>
        ) : (
          <Table<PolicyRow>
            columns={columns}
            dataSource={filtered}
            rowKey={(record) => record.key}
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => (
                <span style={{ color: colors.textMuted }}>{total} rate-limit policies</span>
              ),
            }}
            scroll={{ x: 900 }}
          />
        )}
      </div>
    </div>
  )
}

function PoliciesTable() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<string>('all')

  const { data: resources, isLoading, isError, refetch } = useQuery({
    queryKey: ['gateway-resources'],
    queryFn: fetchGatewayResources,
  })

  const rows = useMemo<PolicyRow[]>(() => {
    return (resources ?? []).flatMap((binding) =>
      (binding.policies ?? [])
        .map((policy, index) => ({
          key: `${binding.kind}/${binding.namespace}/${binding.name}/${policy.pluginType}/${index}`,
          binding,
          policy,
        }))
    )
  }, [resources])

  const filtered = rows.filter((row) => {
    const query = search.trim()
    const pluginType = normalizePluginType(row.policy.pluginType)
    const matchesCategory =
      category === 'all' ||
      (category === 'auth' && AUTH_PLUGINS.has(pluginType)) ||
      (category === 'ratelimiting' && RATE_LIMIT_PLUGINS.has(pluginType)) ||
      (category === 'other' && !AUTH_PLUGINS.has(pluginType) && !RATE_LIMIT_PLUGINS.has(pluginType))

    const matchesQuery =
      !query ||
      matchesSearch(row.binding.name, query) ||
      matchesSearch(row.binding.namespace ?? '', query) ||
      matchesSearch(row.binding.relatedExposedApi?.name ?? '', query) ||
      matchesSearch(getPolicyLabel(row.policy.pluginType), query) ||
      matchesSearch(getPolicySummary(row.policy) ?? '', query)

    return matchesCategory && matchesQuery
  })

  const columns: ColumnsType<PolicyRow> = [
    {
      title: 'API / Resource',
      key: 'resource',
      render: (_value: unknown, record) => (
        <div>
          <div style={{ fontWeight: 600, color: colors.textPrimary, fontSize: 13 }}>
            {record.binding.relatedExposedApi
              ? formatApiName(record.binding.relatedExposedApi.name)
              : record.binding.name}
          </div>
          <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
            {record.binding.relatedExposedApi
              ? `${record.binding.relatedExposedApi.namespace}/${record.binding.relatedExposedApi.name}`
              : `${record.binding.namespace}/${record.binding.name}`}
          </div>
        </div>
      ),
    },
    {
      title: 'Gateway',
      key: 'gateway',
      width: 220,
      render: (_value: unknown, record) => {
        const gc = gatewayKindColor(record.binding.kind)
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Tag style={{ background: gc.bg, color: gc.text, border: 'none', borderRadius: 4, fontSize: 10 }}>
                {record.binding.kind}
              </Tag>
              <span style={{ fontSize: 11, fontFamily: 'monospace', color: colors.textSecondary }}>
                {record.binding.name}
              </span>
            </div>
            <span style={{ fontSize: 11, color: colors.textMuted }}>{record.binding.canvasType}</span>
          </div>
        )
      },
    },
    {
      title: 'Policy',
      key: 'policy',
      width: 220,
      render: (_value: unknown, record) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <PluginPill policy={record.policy} />
          {record.policy.name && (
            <span style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
              {record.policy.name}
            </span>
          )}
        </div>
      ),
    },
    {
      title: 'Details',
      key: 'details',
      render: (_value: unknown, record) => (
        <span style={{ color: colors.textSecondary, fontSize: 12 }}>
          {getPolicySummary(record.policy) ?? 'Configured'}
        </span>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_value: unknown, record) => (
        <StatusBadge
          status={record.policy.enabled === false ? 'down' : 'live'}
          label={record.policy.enabled === false ? 'DISABLED' : 'ACTIVE'}
        />
      ),
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input
            placeholder="Search policies by API, gateway or plugin..."
            prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            allowClear
            style={{ width: 340 }}
          />
          <Select
            value={category}
            onChange={setCategory}
            style={{ width: 170 }}
            options={[
              { value: 'all', label: 'All Policies' },
              { value: 'auth', label: 'Auth Policies' },
              { value: 'ratelimiting', label: 'Rate Limiting' },
              { value: 'other', label: 'Other Plugins' },
            ]}
          />
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: colors.textMuted }}>
            {filtered.length} polic{filtered.length === 1 ? 'y' : 'ies'}
          </span>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          />
        </div>
      </div>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: 10,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        {isError && (
          <div style={{ padding: 16, color: colors.statusDown }}>
            Failed to load API policies. Please try again.
          </div>
        )}
        {!isLoading && filtered.length === 0 ? (
          <div style={{ padding: 32 }}>
            <Empty
              description={
                <span style={{ color: colors.textMuted }}>
                  No policies are currently attached to discovered gateway resources.
                </span>
              }
            />
          </div>
        ) : (
          <Table<PolicyRow>
            columns={columns}
            dataSource={filtered}
            rowKey={(record) => record.key}
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => <span style={{ color: colors.textMuted }}>{total} policies</span>,
            }}
            scroll={{ x: 980 }}
          />
        )}
      </div>
    </div>
  )
}

/* ---------- Dependent APIs ---------- */
function DependentAPIsTable() {
  const [search, setSearch] = useState('')
  const [segmentFilter, setSegmentFilter] = useState<'all' | 'coreFunction' | 'managementFunction' | 'securityFunction'>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'ready' | 'unresolved'>('all')
  const [namespaceFilter, setNamespaceFilter] = useState<string>('all')

  const query = useQuery({
    queryKey: ['dependent-apis'],
    queryFn: fetchDependentApis,
    refetchInterval: 10_000,
  })

  const namespaceOptions = useMemo(() => {
    const seen = new Set<string>()
    for (const r of query.data ?? []) {
      if (r.namespace) seen.add(r.namespace)
    }
    return [
      { value: 'all', label: 'All Namespaces' },
      ...Array.from(seen).sort().map((ns) => ({ value: ns, label: ns })),
    ]
  }, [query.data])

  const rows = useMemo(() => {
    const list = query.data ?? []
    const search_lc = search.trim().toLowerCase()
    return list.filter((r) => {
      if (segmentFilter !== 'all' && r.segment !== segmentFilter) return false
      if (statusFilter === 'ready' && !r.ready) return false
      if (statusFilter === 'unresolved' && r.ready) return false
      if (namespaceFilter !== 'all' && r.namespace !== namespaceFilter) return false
      if (search_lc) {
        const hay = `${r.name} ${r.namespace} ${r.apiName ?? ''} ${r.componentName ?? ''} ${r.resolvedUrl ?? ''}`.toLowerCase()
        if (!hay.includes(search_lc)) return false
      }
      return true
    })
  }, [query.data, search, segmentFilter, statusFilter, namespaceFilter])

  const columns: ColumnsType<DependentAPI> = [
    {
      title: 'Name',
      key: 'name',
      render: (_: unknown, r) => (
        <div>
          <div style={{ fontWeight: 600, color: colors.textPrimary }}>{r.apiName || r.name}</div>
          <div style={{ fontSize: 11, color: colors.textMuted }}>{r.namespace}/{r.name}</div>
        </div>
      ),
    },
    {
      title: 'Component',
      key: 'component',
      render: (_: unknown, r) => r.componentName ? <Tag color="geekblue">{r.componentName}</Tag> : <span style={{ color: colors.textMuted }}>—</span>,
    },
    {
      title: 'Segment',
      key: 'segment',
      width: 160,
      render: (_: unknown, r) => r.segment ? <Tag>{r.segment}</Tag> : <span style={{ color: colors.textMuted }}>—</span>,
    },
    {
      title: 'Type',
      key: 'type',
      width: 110,
      render: (_: unknown, r) => <Tag>{r.apiType || 'openapi'}</Tag>,
    },
    {
      title: 'Version',
      key: 'version',
      width: 90,
      render: (_: unknown, r) => r.version ? <Tag>{r.version}</Tag> : <span style={{ color: colors.textMuted }}>—</span>,
    },
    {
      title: 'Status',
      key: 'status',
      width: 130,
      render: (_: unknown, r) => <StatusBadge status={r.ready ? 'ready' : 'not-ready'} label={r.ready ? 'Resolved' : 'Unresolved'} />,
    },
    {
      title: 'Resolved URL',
      key: 'resolved',
      render: (_: unknown, r) =>
        r.resolvedUrl ? (
          <a href={r.resolvedUrl} target="_blank" rel="noreferrer" style={{ color: colors.primary, wordBreak: 'break-all' }}>
            <LinkOutlined style={{ marginRight: 6 }} />
            {r.resolvedUrl}
          </a>
        ) : (
          <Tooltip title={r.specificationUrl ? `Spec: ${r.specificationUrl}` : undefined}>
            <span style={{ color: colors.textMuted }}>not yet resolved</span>
          </Tooltip>
        ),
    },
  ]

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 16,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input
            placeholder="Search by name, namespace, component, URL..."
            prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <Select
            value={segmentFilter}
            onChange={setSegmentFilter}
            style={{ width: 180 }}
            options={[
              { value: 'all', label: 'All Segments' },
              { value: 'coreFunction', label: 'coreFunction' },
              { value: 'managementFunction', label: 'managementFunction' },
              { value: 'securityFunction', label: 'securityFunction' },
            ]}
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 160 }}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'ready', label: 'Resolved' },
              { value: 'unresolved', label: 'Unresolved' },
            ]}
          />
          <Select
            value={namespaceFilter}
            onChange={setNamespaceFilter}
            showSearch
            optionFilterProp="label"
            style={{ width: 200 }}
            options={namespaceOptions}
          />
        </div>
        <Space>
          <span style={{ fontSize: 12, color: colors.textMuted }}>
            {rows.length} of {query.data?.length ?? 0}
          </span>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => query.refetch()}
            loading={query.isFetching}
          >
            Refresh
          </Button>
        </Space>
      </div>

      <Table<DependentAPI>
        rowKey={(r) => `${r.namespace}/${r.name}`}
        loading={query.isLoading}
        columns={columns}
        dataSource={rows}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        locale={{ emptyText: query.isError ? (query.error as Error).message : <Empty description="No Dependent APIs" /> }}
        scroll={{ x: 980 }}
      />
    </div>
  )
}

export default function ExposedAPIsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const activeKey = PATH_TO_TAB[location.pathname] ?? 'exposedapis'
  const [view, setView] = useState<'table' | 'graph'>('table')

  const tabItems = [
    {
      key: 'exposedapis',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <ApiOutlined />
          APIs
        </span>
      ),
      children: (
        <div style={{ padding: '20px 0 0' }}>
          <ExposedAPIsTable />
        </div>
      ),
    },
    {
      key: 'dependentapis',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <LinkOutlined />
          Dependent APIs
        </span>
      ),
      children: (
        <div style={{ padding: '20px 0 0' }}>
          <DependentAPIsTable />
        </div>
      ),
    },
    {
      key: 'gateway',
      label: 'API Gateway',
      children: (
        <div style={{ padding: '20px 0 0' }}>
          <GatewayResourcesTable mode="gateway" />
        </div>
      ),
    },
    {
      key: 'servicemesh',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <ClusterOutlined />
          Service Mesh
        </span>
      ),
      children: (
        <div style={{ padding: '20px 0 0' }}>
          <GatewayResourcesTable mode="mesh" />
        </div>
      ),
    },
    {
      key: 'policies',
      label: 'API Policies',
      children: (
        <div style={{ padding: '20px 0 0' }}>
          <PoliciesTable />
        </div>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: colors.primaryGradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            color: '#fff',
          }}
        >
          <ApiOutlined />
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
            API Exposure
          </h1>
          <p style={{ fontSize: 13, color: colors.textSecondary, margin: 0 }}>
            Manage exposed APIs, gateway resources, and plugin policies
          </p>
        </div>
        <Segmented
          value={view}
          onChange={(v) => setView(v as 'table' | 'graph')}
          options={[
            { label: 'Table', value: 'table', icon: <AppstoreOutlined /> },
            { label: 'Graph', value: 'graph', icon: <NodeIndexOutlined /> },
          ]}
        />
      </div>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: 12,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}
      >
        {view === 'graph' ? (
          <div style={{ padding: 20 }}>
            <ApiRelationshipGraph />
          </div>
        ) : (
          <Tabs
            activeKey={activeKey}
            onChange={(key) => navigate(TAB_TO_PATH[key as TabKey])}
            items={tabItems}
            style={{ padding: '0 20px' }}
            destroyInactiveTabPane
            tabBarStyle={{
              borderBottom: `1px solid ${colors.border}`,
              marginBottom: 0,
            }}
            tabBarGutter={8}
          />
        )}
      </div>
    </div>
  )
}
