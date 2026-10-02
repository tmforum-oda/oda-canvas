import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Row, Col, Card, Spin, Tag } from 'antd'
import {
  ClusterOutlined,
  ApiOutlined,
  ControlOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  DeploymentUnitOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons'
import { fetchComponents } from '@/api/components'
import { fetchOperators } from '@/api/operators'
import { fetchExposedApis } from '@/api/exposedApis'
import { fetchClusterOverview } from '@/api/cluster'
import { colors } from '@/theme'

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2
      style={{
        fontSize: 13,
        fontWeight: 600,
        color: colors.textMuted,
        textTransform: 'uppercase',
        letterSpacing: 1.2,
        marginBottom: 16,
        marginTop: 0,
      }}
    >
      {children}
    </h2>
  )
}

interface StatCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  color: string
  subtitle?: string
  gradient?: string
}

function StatCard({ title, value, icon, color, subtitle, gradient }: StatCardProps) {
  return (
    <Card
      style={{
        background: colors.bgCard,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        overflow: 'hidden',
        position: 'relative',
        boxShadow: '0 1px 2px rgba(15,23,42,0.04), 0 6px 16px rgba(15,23,42,0.04)',
      }}
      bodyStyle={{ padding: '20px 24px 20px 28px' }}
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: 4,
          background: color,
        }}
      />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.6, fontWeight: 600 }}>{title}</div>
          <div style={{ fontSize: 34, fontWeight: 700, color: colors.textPrimary, lineHeight: 1, letterSpacing: 0 }}>
            {value}
          </div>
          {subtitle && (
            <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 6 }}>{subtitle}</div>
          )}
        </div>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 8,
            background: gradient || `${color}20`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color,
            fontSize: 20,
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
      </div>
    </Card>
  )
}

interface InfoRowProps {
  label: string
  value: React.ReactNode
}

function InfoRow({ label, value }: InfoRowProps) {
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
      <span style={{ fontSize: 13, color: colors.textSecondary }}>{label}</span>
      <span style={{ fontSize: 13, color: colors.textPrimary, fontWeight: 500 }}>{value}</span>
    </div>
  )
}

function CapacityBar({
  used,
  total,
  label,
  format,
}: {
  used: number
  total: number
  label: string
  format: (v: number) => string
}) {
  const unknown = total <= 0
  const pct = unknown ? 0 : Math.min(100, Math.round((used / total) * 100))
  const color =
    pct > 80 ? colors.statusDown : pct > 60 ? colors.statusDeprecated : colors.statusLive
  return (
    <div style={{ marginBottom: 16 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 6,
        }}
      >
        <span style={{ fontSize: 13, color: colors.textSecondary }}>{label}</span>
        <span style={{ fontSize: 12, color: colors.textMuted }}>
          {unknown ? (
            <span>
              {format(used)} <span style={{ color: colors.textMuted }}>/ unknown</span>
            </span>
          ) : (
            <>
              {format(used)} / {format(total)}
              <span style={{ marginLeft: 8, fontWeight: 700, color }}>{pct}%</span>
            </>
          )}
        </span>
      </div>
      <div style={{ height: 8, background: colors.border, borderRadius: 999, overflow: 'hidden' }}>
        {!unknown && (
          <div
            style={{
              height: '100%',
              width: `${pct}%`,
              background: color,
              borderRadius: 999,
              transition: 'width 0.4s ease',
            }}
          />
        )}
      </div>
    </div>
  )
}

function fmtCpu(cores: number) {
  return `${cores.toFixed(1)} cores`
}
function fmtGiB(bytes: number) {
  return `${(bytes / 1024 ** 3).toFixed(1)} GiB`
}

// ─── Brand Logos ─────────────────────────────────────────────────────────────

function KongLogo({ size = 24 }: { size?: number }) {
  return (
    <img
      src="/Kong_logo.png"
      alt="Kong"
      style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
    />
  )
}

function ApisixLogo({ size = 24 }: { size?: number }) {
  return (
    <img
      src="/apisix-logo.png"
      alt="APISIX"
      style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
    />
  )
}

function IstioLogo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="64" height="64" rx="10" fill="#466BB0" />
      {/* Sail shape */}
      <path d="M32 10 L52 50 L32 44 Z" fill="white" opacity="0.9" />
      <path d="M32 10 L12 50 L32 44 Z" fill="white" opacity="0.5" />
      {/* Horizontal bar (boat hull) */}
      <rect x="14" y="50" width="36" height="4" rx="2" fill="white" />
    </svg>
  )
}

function KeycloakLogo({ size = 20 }: { size?: number }) {
  return (
    <img
      src="/keycloak-logo.png"
      alt="Keycloak"
      style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
    />
  )
}

interface ProviderInfo {
  label: string
  logo: string
}

function providerInfo(provider: string | undefined): ProviderInfo {
  switch ((provider || '').toLowerCase()) {
    case 'google':
      return { label: 'Google Kubernetes Engine', logo: '/gke-logo.png' }
    case 'amazon':
      return { label: 'Amazon EKS', logo: '/eks-logo.jpg' }
    case 'azure':
      return { label: 'Azure AKS', logo: '/aks-logo.svg' }
    default:
      return { label: 'Kubernetes', logo: '/kubernetes-logo.png' }
  }
}

// ─── API Gateway detection ────────────────────────────────────────────────────
// Checks operator deploymentName (e.g. canvas-kongistio-operator)

type ApiGatewayType = 'apisix' | 'kong' | 'istio'

interface ApiGatewayInfo {
  type: ApiGatewayType
  label: string
  logo: React.ReactNode
}

function detectApiGateway(deploymentNames: string[]): ApiGatewayInfo {
  const lower = deploymentNames.map((n) => n.toLowerCase())
  if (lower.some((n) => n.includes('apisix'))) {
    return { type: 'apisix', label: 'Apisix', logo: <ApisixLogo size={22} /> }
  }
  if (lower.some((n) => n.includes('kong'))) {
    return { type: 'kong', label: 'Kong', logo: <KongLogo size={22} /> }
  }
  return { type: 'istio', label: 'Istio', logo: <IstioLogo size={22} /> }
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function CanvasCluster() {
  const { data: components, isLoading: loadingComponents } = useQuery({
    queryKey: ['components'],
    queryFn: fetchComponents,
  })

  const { data: operators, isLoading: loadingOperators } = useQuery({
    queryKey: ['operators'],
    queryFn: fetchOperators,
  })

  const { data: exposedApis, isLoading: loadingApis } = useQuery({
    queryKey: ['exposedapis'],
    queryFn: fetchExposedApis,
  })

  const { data: clusterOverview } = useQuery({
    queryKey: ['cluster-overview'],
    queryFn: fetchClusterOverview,
    staleTime: 60_000,
  })

  const isLoading = loadingComponents || loadingOperators || loadingApis

  const totalComponents = components?.length ?? 0

  // Ready = deployment_status "Complete" (resolved to 'ready' in normalizeComponent)
  const readyComponents =
    components?.filter((c) => c.status === 'ready').length ?? 0

  // In Deployment = anything that is not complete and not failed
  const inProgressComponents =
    components?.filter((c) => c.status !== 'ready' && c.status !== 'failed').length ?? 0

  const failedComponents =
    components?.filter((c) => c.status === 'failed').length ?? 0

  const totalOperators = operators?.length ?? 0
  const runningOperators = operators?.filter((o) => o.status === 'running').length ?? 0

  const totalApis = exposedApis?.length ?? 0
  const liveApis = exposedApis?.filter((a) => a.status?.toLowerCase() === 'ready').length ?? 0

  // Namespace count from backend (components + odacompns-*)
  const componentNamespaceCount = clusterOverview?.componentNamespaceCount ?? 0

  // API gateway: detect from actual deployment names (e.g. canvas-kongistio-operator)
  const deploymentNames = operators?.map((o) => o.deploymentName) ?? []
  const apiGateway = detectApiGateway(deploymentNames)

  if (isLoading) {
    return (
      <div
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}
      >
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* Thin hero strip */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 18px',
          marginBottom: 16,
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
        }}
      >
        <div
          title={providerInfo(clusterOverview?.provider).label}
          style={{
            width: 40,
            height: 40,
            borderRadius: 8,
            background: colors.bgCard,
            border: `1px solid ${colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 5,
            flexShrink: 0,
          }}
        >
          <img
            src={providerInfo(clusterOverview?.provider).logo}
            alt={providerInfo(clusterOverview?.provider).label}
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }}
          />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary, lineHeight: 1.2 }}>
            Canvas Cluster
          </div>
          <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 1 }}>
            {providerInfo(clusterOverview?.provider).label}
          </div>
        </div>
      </div>

      {/* KPI row */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="Total Components"
            value={totalComponents}
            icon={<DatabaseOutlined />}
            color={colors.primary}
            gradient={colors.primaryGradient}
            subtitle={`${readyComponents} ready`}
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="Exposed APIs"
            value={totalApis}
            icon={<ApiOutlined />}
            color={colors.statusLive}
            subtitle={`${liveApis} live`}
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="Operators"
            value={totalOperators}
            icon={<ControlOutlined />}
            color={colors.infoText}
            subtitle={`${runningOperators} running`}
          />
        </Col>
      </Row>

      {/* 2/3 + 1/3 body */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* Component health horizontal strip */}
          <Card
            style={{
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              marginBottom: 16,
            }}
            bodyStyle={{ padding: '14px 18px' }}
          >
            <SectionTitle>Component Health</SectionTitle>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {[
                {
                  label: 'Ready',
                  value: readyComponents,
                  color: colors.statusLive,
                  bg: colors.statusLiveBg,
                  icon: <CheckCircleOutlined />,
                },
                {
                  label: 'In Deployment',
                  value: inProgressComponents,
                  color: colors.statusDeprecated,
                  bg: colors.statusDeprecatedBg,
                  icon: <SyncOutlined spin />,
                },
                {
                  label: 'Failed',
                  value: failedComponents,
                  color: colors.statusDown,
                  bg: colors.statusDownBg,
                  icon: <CloseCircleOutlined />,
                },
              ].map((s) => (
                <div
                  key={s.label}
                  style={{
                    flex: '1 1 140px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 14px',
                    background: s.bg,
                    border: `1px solid ${s.color}30`,
                    borderRadius: 8,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: `${s.color}1F`,
                      color: s.color,
                      fontSize: 16,
                      flexShrink: 0,
                    }}
                  >
                    {s.icon}
                  </div>
                  <div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: s.color, lineHeight: 1 }}>
                      {s.value}
                    </div>
                    <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 2 }}>
                      {s.label}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {clusterOverview && (
            <Card
              style={{
                background: colors.bgCard,
                border: `1px solid ${colors.border}`,
                borderRadius: 8,
                marginBottom: 16,
              }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <SectionTitle>Kubernetes Resources</SectionTitle>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
                {[
                  {
                    label: 'Nodes',
                    value: `${clusterOverview.nodes.ready}/${clusterOverview.nodes.total}`,
                    icon: <NodeIndexOutlined />,
                    color: colors.primary,
                  },
                  {
                    label: 'Deployments',
                    value: `${clusterOverview.deployments.available}/${clusterOverview.deployments.total}`,
                    icon: <DeploymentUnitOutlined />,
                    color: colors.statusLive,
                  },
                  {
                    label: 'Services',
                    value: clusterOverview.services,
                    icon: <ApiOutlined />,
                    color: colors.infoText,
                  },
                ].map((s) => (
                  <div
                    key={s.label}
                    style={{
                      flex: '1 1 130px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '10px 14px',
                      background: `${s.color}10`,
                      border: `1px solid ${s.color}28`,
                      borderRadius: 8,
                    }}
                  >
                    <div
                      style={{
                        width: 30,
                        height: 30,
                        borderRadius: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: `${s.color}1F`,
                        color: s.color,
                        fontSize: 14,
                        flexShrink: 0,
                      }}
                    >
                      {s.icon}
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: s.color, lineHeight: 1 }}>
                        {s.value}
                      </div>
                      <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 2 }}>
                        {s.label}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {clusterOverview.nodes.notReady > 0 && (
                  <Tag
                    style={{
                      color: colors.statusDown,
                      background: `${colors.statusDown}18`,
                      border: `1px solid ${colors.statusDown}40`,
                      borderRadius: 999,
                    }}
                  >
                    {clusterOverview.nodes.notReady} nodes not ready
                  </Tag>
                )}
                {clusterOverview.pods.pending > 0 && (
                  <Tag
                    style={{
                      color: colors.statusDeprecated,
                      background: `${colors.statusDeprecated}18`,
                      border: `1px solid ${colors.statusDeprecated}40`,
                      borderRadius: 999,
                    }}
                  >
                    {clusterOverview.pods.pending} pods pending
                  </Tag>
                )}
                {clusterOverview.pods.failed > 0 && (
                  <Tag
                    style={{
                      color: colors.statusDown,
                      background: `${colors.statusDown}18`,
                      border: `1px solid ${colors.statusDown}40`,
                      borderRadius: 999,
                    }}
                  >
                    {clusterOverview.pods.failed} pods failed
                  </Tag>
                )}
                {clusterOverview.version && (
                  <Tag
                    style={{
                      color: colors.textMuted,
                      background: colors.surfaceMuted,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 999,
                      fontFamily: 'monospace',
                    }}
                  >
                    {clusterOverview.provider
                      ? `${clusterOverview.provider} ${clusterOverview.version}`
                      : clusterOverview.version}
                  </Tag>
                )}
              </div>
            </Card>
          )}

          {clusterOverview && (
            <Card
              style={{
                background: colors.bgCard,
                border: `1px solid ${colors.border}`,
                borderRadius: 8,
              }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <SectionTitle>Capacity</SectionTitle>
              <CapacityBar
                label="Pods"
                used={clusterOverview.pods.total}
                total={
                  clusterOverview.pods.allocatable > 0 ? clusterOverview.pods.allocatable : 0
                }
                format={(v) => `${v}`}
              />
              <CapacityBar
                label="CPU"
                used={clusterOverview.capacity.cpuUsed}
                total={clusterOverview.capacity.cpuCores}
                format={fmtCpu}
              />
              <CapacityBar
                label="Memory"
                used={clusterOverview.capacity.memoryUsed}
                total={clusterOverview.capacity.memoryBytes}
                format={fmtGiB}
              />
            </Card>
          )}
        </Col>

        {/* Right rail: Platform Details */}
        <Col xs={24} lg={8}>
          <Card
            style={{
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              position: 'sticky',
              top: 16,
            }}
            bodyStyle={{ padding: '14px 18px' }}
          >
            <SectionTitle>Platform Details</SectionTitle>
            <InfoRow label="Canvas Version" value="ODA Canvas v1.1" />
            <InfoRow
              label="Canvas Type"
              value={
                <Tag
                  style={{
                    background: colors.tmfBg,
                    color: colors.tmfText,
                    border: 'none',
                    borderRadius: 4,
                    fontSize: 12,
                  }}
                >
                  TM Forum ODA
                </Tag>
              }
            />
            <InfoRow
              label="IDM Provider"
              value={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <KeycloakLogo size={20} />
                  <span>Keycloak</span>
                </div>
              }
            />
            <InfoRow
              label="API Gateway"
              value={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {apiGateway.logo}
                  <span>{apiGateway.label}</span>
                </div>
              }
            />
            <InfoRow
              label="Platform Status"
              value={
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    background: colors.statusLiveBg,
                    color: colors.statusLive,
                    borderRadius: 999,
                    padding: '2px 10px',
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: colors.statusLive,
                      display: 'inline-block',
                    }}
                  />
                  OPERATIONAL
                </span>
              }
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
