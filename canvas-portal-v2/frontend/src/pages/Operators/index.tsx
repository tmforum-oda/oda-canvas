import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Tag, Spin, Button, Tooltip, Progress, Modal } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  ControlOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { fetchOperators, fetchOperatorPodLogs, streamOperatorPodLogs, type Operator, type OperatorPod } from '@/api/operators'
import StatusBadge from '@/components/StatusBadge'
import LogViewer from '@/components/LogViewer'
import { colors } from '@/theme'

interface OperatorCardProps {
  operator: Operator
  onViewDetails: (operator: Operator) => void
}

function OperatorCard({ operator, onViewDetails }: OperatorCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [logModal, setLogModal] = useState<{ pod: OperatorPod } | null>(null)

  const readyRatio = operator.desired > 0 ? operator.ready / operator.desired : 0
  const isHealthy = operator.status === 'running'
  const isDegraded = operator.status === 'degraded'

  const imageTag = operator.image?.split(':').pop() ?? 'latest'
  const imageName = operator.image?.split('/').slice(-1)[0]?.split(':')[0] ?? operator.name

  return (
    <>
      <Card
        style={{
          background: colors.bgCard,
          border: `1px solid ${
            isHealthy ? colors.border : isDegraded ? `${colors.statusDeprecated}50` : `${colors.statusDown}50`
          }`,
          borderRadius: 12,
          overflow: 'hidden',
          transition: 'border-color 0.2s',
        }}
        bodyStyle={{ padding: 0 }}
      >
        {/* Card header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: `1px solid ${colors.border}`,
            background: colors.surfaceInset,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 8,
                background: isHealthy
                  ? `${colors.statusLive}15`
                  : isDegraded
                  ? `${colors.statusDeprecated}15`
                  : `${colors.statusDown}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                color: isHealthy
                  ? colors.statusLive
                  : isDegraded
                  ? colors.statusDeprecated
                  : colors.statusDown,
              }}
            >
              <ControlOutlined />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <div style={{ fontWeight: 700, color: colors.textPrimary, fontSize: 14 }}>
                  {operator.name}
                </div>
                {operator.tmfId && (
                  <Tooltip title={operator.tmfName ?? operator.tmfId}>
                    <Tag
                      style={{
                        margin: 0,
                        fontSize: 10,
                        lineHeight: '16px',
                        padding: '0 6px',
                        background: colors.tmfBg,
                        color: colors.tmfText,
                        border: `1px solid ${colors.tmfText}40`,
                      }}
                    >
                      {operator.tmfId}
                    </Tag>
                  </Tooltip>
                )}
              </div>
              <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
                {operator.namespace}
              </div>
              {operator.deploymentName !== operator.name && (
                <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace', marginTop: 2 }}>
                  deploy/{operator.deploymentName}
                </div>
              )}
            </div>
          </div>
          <StatusBadge status={operator.status} />
        </div>

        {/* Card body */}
        <div style={{ padding: '16px 20px' }}>
          {/* Image */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4 }}>Image</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  fontSize: 12,
                  fontFamily: 'monospace',
                  color: colors.textSecondary,
                  background: colors.surfaceMuted,
                  padding: '2px 8px',
                  borderRadius: 4,
                  maxWidth: 220,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  display: 'block',
                }}
                title={operator.image}
              >
                {imageName}
              </span>
              {operator.containerName && (
                <Tag
                  style={{
                    fontSize: 10,
                    background: colors.hoverSurface,
                    color: colors.textSecondary,
                    border: 'none',
                    borderRadius: 4,
                    flexShrink: 0,
                    maxWidth: 150,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={operator.containerName}
                >
                  {operator.containerName}
                </Tag>
              )}
              <Tag
                style={{
                  fontSize: 10,
                  background: colors.tmfBg,
                  color: colors.tmfText,
                  border: 'none',
                  borderRadius: 4,
                  flexShrink: 0,
                }}
              >
                {imageTag}
              </Tag>
            </div>
          </div>

          {/* Desired / Ready */}
          <div style={{ marginBottom: 14 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: 11, color: colors.textMuted }}>Pods Ready</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: colors.textPrimary }}>
                {operator.ready} / {operator.desired}
              </span>
            </div>
            <Progress
              percent={Math.round(readyRatio * 100)}
              strokeColor={isHealthy ? colors.statusLive : isDegraded ? colors.statusDeprecated : colors.statusDown}
              trailColor={colors.progressTrack}
              showInfo={false}
              size="small"
            />
          </div>

          <div style={{ marginBottom: 14 }}>
            <button
              type="button"
              onClick={() => onViewDetails(operator)}
              style={{
                width: '100%',
                background: colors.surfaceSelected,
                border: `1px solid ${colors.surfaceSelectedBorder}`,
                borderRadius: 8,
                color: colors.tmfText,
                cursor: 'pointer',
                padding: '8px 12px',
                fontSize: 12,
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
              }}
            >
              <InfoCircleOutlined />
              View deployment details
            </button>
          </div>

          {/* Pods expandable */}
          <div>
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              style={{
                width: '100%',
                background: colors.surfaceSubtle,
                border: `1px solid ${colors.border}`,
                borderRadius: 6,
                color: colors.textSecondary,
                cursor: 'pointer',
                padding: '7px 12px',
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>
                {operator.pods.length} pod{operator.pods.length !== 1 ? 's' : ''}
              </span>
              <span>{expanded ? '▲' : '▼'}</span>
            </button>

            {expanded && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {operator.pods.map((pod) => (
                  <div
                    key={pod.name}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: colors.surfaceSubtle,
                      borderRadius: 6,
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
                      {pod.ready ? (
                        <CheckCircleOutlined style={{ color: colors.statusLive, fontSize: 13, flexShrink: 0 }} />
                      ) : (
                        <CloseCircleOutlined style={{ color: colors.statusDown, fontSize: 13, flexShrink: 0 }} />
                      )}
                      <span
                        style={{
                          fontSize: 11,
                          fontFamily: 'monospace',
                          color: colors.textSecondary,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        title={pod.name}
                      >
                        {pod.name}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                      {pod.restarts > 0 && (
                        <Tag
                          color="orange"
                          style={{ fontSize: 10, padding: '0 4px' }}
                        >
                          {pod.restarts}R
                        </Tag>
                      )}
                      <Tooltip title="View logs">
                        <button
                          type="button"
                          onClick={() => setLogModal({ pod })}
                          style={{
                            background: colors.surfaceSelected,
                            border: `1px solid ${colors.surfaceSelectedBorder}`,
                            borderRadius: 5,
                            color: colors.tmfText,
                            cursor: 'pointer',
                            padding: '3px 8px',
                            fontSize: 11,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <FileTextOutlined style={{ fontSize: 11 }} />
                          Logs
                        </button>
                      </Tooltip>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Log Modal */}
      <Modal
        open={!!logModal}
        onCancel={() => setLogModal(null)}
        footer={null}
        width={900}
        title={
          <span style={{ color: colors.textPrimary }}>
            Logs: {logModal?.pod.name}
            {operator.containerName ? ` / ${operator.containerName}` : ''}
          </span>
        }
        styles={{
          content: { background: colors.bgCard, padding: 0 },
          header: {
            background: colors.bgCard,
            borderBottom: `1px solid ${colors.border}`,
            padding: '12px 20px',
          },
          body: { padding: 16 },
        }}
      >
        {logModal && (
          <LogViewer
            title={`${logModal.pod.name}${operator.containerName ? ` · ${operator.containerName}` : ''}`}
            filename={`${logModal.pod.name}${operator.containerName ? `-${operator.containerName}` : ''}-logs.txt`}
            fetchLogs={(tail) =>
              fetchOperatorPodLogs(
                operator.namespace,
                operator.name,
                logModal.pod.name,
                tail,
                operator.containerName,
              )
            }
            streamLogs={(opts) =>
              streamOperatorPodLogs(
                operator.namespace,
                operator.name,
                logModal.pod.name,
                { ...opts, container: operator.containerName },
              )
            }
          />
        )}
      </Modal>
    </>
  )
}

export default function OperatorsPage() {
  const navigate = useNavigate()
  const { data: operators, isLoading, isError, refetch } = useQuery({
    queryKey: ['operators'],
    queryFn: fetchOperators,
  })

  const runningCount = operators?.filter((o) => o.status === 'running').length ?? 0
  const totalCount = operators?.length ?? 0

  return (
    <div>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
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
              fontSize: 18,
              color: '#fff',
            }}
          >
            <ControlOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              Canvas Operators
            </h1>
            <p style={{ fontSize: 12, color: colors.textMuted, margin: '2px 0 0' }}>
              {runningCount} of {totalCount} healthy
            </p>
          </div>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => refetch()}
          style={{
            background: 'transparent',
            border: `1px solid ${colors.border}`,
            color: colors.textSecondary,
          }}
        >
          Refresh
        </Button>
      </div>

      {/* Summary stats */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          { label: 'Total', value: totalCount, color: colors.primary },
          { label: 'Running', value: runningCount, color: colors.statusLive },
          { label: 'Degraded', value: operators?.filter((o) => o.status === 'degraded').length ?? 0, color: colors.statusDeprecated },
          { label: 'Down', value: operators?.filter((o) => o.status === 'down').length ?? 0, color: colors.statusDown },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: '8px 14px',
              display: 'flex',
              alignItems: 'baseline',
              gap: 8,
              flex: '0 1 auto',
              minWidth: 120,
            }}
          >
            <span style={{ fontSize: 20, fontWeight: 700, color: stat.color, lineHeight: 1 }}>{stat.value}</span>
            <span style={{ fontSize: 12, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {stat.label}
            </span>
          </div>
        ))}
      </div>

      {/* Operator cards */}
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : isError ? (
        <div
          style={{
            padding: 24,
            color: colors.statusDown,
            background: colors.bgCard,
            borderRadius: 10,
            border: `1px solid ${colors.border}`,
          }}
        >
          Failed to load operators. Please check the backend connection.
        </div>
      ) : operators && operators.length > 0 ? (
        <Row gutter={[16, 16]}>
          {operators.map((op) => (
            <Col key={`${op.namespace}/${op.name}`} xs={24} sm={12} xl={8}>
              <OperatorCard
                operator={op}
                onViewDetails={(operator) => navigate(`/operators/${operator.namespace}/${operator.name}`)}
              />
            </Col>
          ))}
        </Row>
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 60,
            background: colors.bgCard,
            borderRadius: 12,
            border: `1px solid ${colors.border}`,
          }}
        >
          <ControlOutlined style={{ fontSize: 40, color: colors.textMuted, marginBottom: 12 }} />
          <span style={{ color: colors.textMuted, fontSize: 14 }}>No operators found in the cluster.</span>
        </div>
      )}
    </div>
  )
}
