import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Col, Row, Spin, Tag, Tooltip } from 'antd'
import {
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  ExportOutlined,
  MonitorOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import {
  fetchObservabilitySummary,
  type ObservabilityTool,
} from '@/api/observability'
import { colors } from '@/theme'

const TOOL_LOGOS: Record<string, string> = {
  langfuse: '/langfuse-logo.svg',
  prometheus: '/prometheus.png',
  grafana: '/grafana-logo.svg',
}

function ToolLogo({ tool }: { tool: ObservabilityTool }) {
  const src = TOOL_LOGOS[tool.id]
  if (src) {
    return (
      <img
        src={src}
        alt={tool.name}
        style={{ width: 28, height: 28, objectFit: 'contain' }}
      />
    )
  }
  if (tool.id === 'grafana') return <DashboardOutlined style={{ fontSize: 22 }} />
  if (tool.id === 'prometheus') return <DatabaseOutlined style={{ fontSize: 22 }} />
  return <ApiOutlined style={{ fontSize: 22 }} />
}

function badgeStyle(tool: ObservabilityTool): { color: string; background: string; label: string; icon: React.ReactNode } {
  if (tool.source === 'chart') {
    return {
      color: colors.primary,
      background: colors.primarySurface,
      label: 'Declared in chart',
      icon: <CheckCircleOutlined />,
    }
  }
  if (tool.status === 'healthy') {
    return {
      color: colors.statusLive,
      background: colors.statusLiveBg,
      label: 'Found in cluster',
      icon: <CheckCircleOutlined />,
    }
  }
  if (tool.status === 'unhealthy') {
    return {
      color: colors.statusDown,
      background: colors.statusDownBg,
      label: 'Found in cluster (degraded)',
      icon: <CloseCircleOutlined />,
    }
  }
  return {
    color: colors.textMuted,
    background: colors.surfaceMuted,
    label: 'Not configured',
    icon: <MonitorOutlined />,
  }
}

function ToolCard({ tool }: { tool: ObservabilityTool }) {
  const canOpen = Boolean(tool.publicUrl)
  const badge = badgeStyle(tool)
  const subtitle = tool.source === 'chart'
    ? 'Provider declared in Helm values'
    : tool.namespace && tool.serviceName
      ? `${tool.namespace}/${tool.serviceName}`
      : 'Service not discovered'

  return (
    <Card
      style={{
        background: colors.bgCard,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
      }}
      bodyStyle={{ padding: 16 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 8,
              background: colors.surfaceMuted,
              border: `1px solid ${colors.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.textSecondary,
              flexShrink: 0,
            }}
          >
            <ToolLogo tool={tool} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: colors.textPrimary, fontWeight: 700, fontSize: 15 }}>{tool.name}</div>
            <div style={{ color: colors.textMuted, fontSize: 11 }}>{subtitle}</div>
          </div>
        </div>

        <Tooltip title={tool.healthMessage || badge.label}>
          <Tag
            icon={badge.icon}
            style={{
              background: badge.background,
              color: badge.color,
              border: `1px solid ${colors.border}`,
              borderRadius: 6,
              height: 26,
              display: 'inline-flex',
              alignItems: 'center',
              margin: 0,
              flexShrink: 0,
            }}
          >
            {badge.label}
          </Tag>
        </Tooltip>
      </div>

      <div style={{ display: 'grid', gap: 8, marginBottom: 14 }}>
        {tool.source !== 'chart' && (
          <div>
            <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 3 }}>Internal URL</div>
            <div
              title={tool.internalUrl || 'Unavailable'}
              style={{
                color: tool.internalUrl ? colors.textSecondary : colors.textMuted,
                fontFamily: 'monospace',
                fontSize: 12,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {tool.internalUrl || 'Unavailable'}
            </div>
          </div>
        )}
        <div>
          <div style={{ color: colors.textMuted, fontSize: 11, marginBottom: 3 }}>
            {tool.source === 'chart' ? 'Configured URL' : 'Public URL'}
          </div>
          <div
            title={tool.publicUrl || 'Not exposed'}
            style={{
              color: tool.publicUrl ? colors.textSecondary : colors.textMuted,
              fontFamily: 'monospace',
              fontSize: 12,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {tool.publicUrl || 'Not exposed'}
          </div>
        </div>
      </div>

      <Button
        type="primary"
        icon={<ExportOutlined />}
        href={tool.publicUrl}
        target="_blank"
        rel="noreferrer"
        disabled={!canOpen}
        style={{
          width: '100%',
          background: canOpen ? colors.primaryGradient : colors.surfaceMuted,
          border: 'none',
          borderRadius: 8,
          fontWeight: 600,
        }}
      >
        Open {tool.name}
      </Button>
    </Card>
  )
}

export default function ObservabilityPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['observability-summary'],
    queryFn: fetchObservabilitySummary,
    staleTime: 30_000,
    retry: 1,
  })

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: colors.primaryGradient,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 18,
            }}
          >
            <MonitorOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              Observability
            </h1>
            <p style={{ fontSize: 12, color: colors.textMuted, margin: '2px 0 0' }}>
              Telemetry tools
            </p>
          </div>
        </div>

        <Button
          icon={<ReloadOutlined spin={isFetching} />}
          onClick={() => refetch()}
          style={{
            background: 'transparent',
            border: `1px solid ${colors.border}`,
            color: colors.textSecondary,
            borderRadius: 8,
          }}
        >
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : isError ? (
        <Alert
          type="error"
          showIcon
          message="Failed to load observability status"
          description="Check backend connectivity and Kubernetes permissions for observability services."
        />
      ) : (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {(data?.tools || []).map((tool) => (
            <Col xs={24} lg={8} key={tool.id}>
              <ToolCard tool={tool} />
            </Col>
          ))}
        </Row>
      )}
    </div>
  )
}
