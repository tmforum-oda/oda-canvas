import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Table, Tag, Tooltip, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ArrowLeftOutlined,
  ControlOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { fetchOperator, fetchOperatorPodLogs, streamOperatorPodLogs, type OperatorPod } from '@/api/operators'
import StatusBadge from '@/components/StatusBadge'
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
        gap: 16,
        alignItems: 'flex-start',
        padding: '10px 0',
        borderBottom: `1px solid ${colors.border}`,
      }}
    >
      <span style={{ fontSize: 13, color: colors.textSecondary, minWidth: 140 }}>{label}</span>
      <span style={{ fontSize: 13, color: colors.textPrimary, textAlign: 'right' }}>{value}</span>
    </div>
  )
}

export default function OperatorDetail() {
  const { namespace = '', name = '' } = useParams<{ namespace: string; name: string }>()
  const navigate = useNavigate()
  const [selectedPod, setSelectedPod] = useState<OperatorPod | null>(null)

  const { data: operator, isLoading } = useQuery({
    queryKey: ['operator', namespace, name],
    queryFn: () => fetchOperator(namespace, name),
    enabled: !!namespace && !!name,
  })

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!operator) {
    return (
      <Alert
        type="error"
        message={`Operator ${namespace}/${name} not found`}
        action={<Button onClick={() => navigate('/operators')}>Back to Operators</Button>}
      />
    )
  }

  const imageName = operator.image?.split('/').slice(-1)[0]?.split(':')[0] ?? operator.name
  const imageTag = operator.image?.split(':').pop() ?? 'latest'
  const restartCount = operator.pods.reduce((sum, pod) => sum + pod.restarts, 0)
  const unhealthyCount = operator.pods.filter((pod) => !pod.ready).length

  const podColumns: ColumnsType<OperatorPod> = [
    {
      title: 'Pod Name',
      dataIndex: 'name',
      key: 'name',
      render: (podName: string, record: OperatorPod) => (
        <button
          type="button"
          onClick={() => setSelectedPod(record)}
          style={{
            background: 'transparent',
            border: 'none',
            padding: 0,
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontSize: 12,
            color: colors.primary,
            textAlign: 'left',
          }}
        >
          {podName}
        </button>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 120,
      render: (_: unknown, record: OperatorPod) => (
        <StatusBadge status={record.ready ? 'ready' : record.phase.toLowerCase()} size="sm" />
      ),
    },
    {
      title: 'Restarts',
      dataIndex: 'restarts',
      key: 'restarts',
      width: 90,
      render: (restarts: number) => (
        <span
          style={{
            color: restarts > 0 ? colors.statusDeprecated : colors.textSecondary,
            fontWeight: restarts > 0 ? 600 : 400,
          }}
        >
          {restarts}
        </span>
      ),
    },
    {
      title: 'Node',
      dataIndex: 'node',
      key: 'node',
      render: (node?: string) =>
        node ? (
          <span style={{ fontSize: 12, color: colors.textSecondary }}>{node}</span>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
    {
      title: 'Age',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
      render: (createdAt?: string) =>
        createdAt ? (
          <Tooltip title={dayjs(createdAt).format('YYYY-MM-DD HH:mm:ss')}>
            <span style={{ color: colors.textMuted, fontSize: 12 }}>{dayjs(createdAt).fromNow()}</span>
          </Tooltip>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 110,
      render: (_: unknown, record: OperatorPod) => (
        <button
          type="button"
          onClick={() => setSelectedPod(record)}
          style={{
            background: colors.surfaceSelected,
            border: `1px solid ${colors.surfaceSelectedBorder}`,
            borderRadius: 6,
            color: colors.tmfText,
            cursor: 'pointer',
            padding: '4px 10px',
            fontSize: 12,
            fontWeight: 600,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <FileTextOutlined />
          Logs
        </button>
      ),
    },
  ]

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="text"
        style={{ color: colors.textSecondary, marginBottom: 16, paddingLeft: 0 }}
        onClick={() => navigate('/operators')}
      >
        Back to Canvas Operators
      </Button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
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
          <ControlOutlined />
        </div>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              {operator.name}
            </h1>
            {operator.tmfId && (
              <Tag
                style={{
                  margin: 0,
                  background: colors.tmfBg,
                  color: colors.tmfText,
                  border: `1px solid ${colors.tmfText}40`,
                  fontFamily: 'monospace',
                  fontSize: 12,
                }}
                title={operator.tmfName ?? operator.tmfId}
              >
                {operator.tmfId}
              </Tag>
            )}
          </div>
          {operator.tmfName && (
            <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 2 }}>
              {operator.tmfName}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
            <Tag
              style={{
                background: colors.infoSurface,
                color: colors.infoText,
                border: 'none',
                borderRadius: 4,
                fontFamily: 'monospace',
                fontSize: 12,
              }}
            >
              {operator.namespace}
            </Tag>
            <StatusBadge status={operator.status} size="sm" />
            {operator.containerName && (
              <Tag
                style={{
                  background: colors.hoverSurface,
                  color: colors.textSecondary,
                  border: 'none',
                  borderRadius: 4,
                  fontFamily: 'monospace',
                  fontSize: 12,
                }}
              >
                {operator.containerName}
              </Tag>
            )}
            {operator.sharedDeployment && (
              <Tag
                style={{
                  background: `${colors.statusDeprecated}18`,
                  color: colors.statusDeprecated,
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 12,
                }}
              >
                Shared deployment
              </Tag>
            )}
            <span style={{ fontSize: 12, color: colors.textMuted }}>
              Deployment details, pods, and live log access
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Desired', value: operator.desired, color: colors.primary },
          { label: 'Ready', value: operator.ready, color: colors.statusLive },
          { label: 'Available', value: operator.available, color: colors.textPrimary },
          { label: 'Pods', value: operator.pods.length, color: colors.textSecondary },
          { label: 'Restarts', value: restartCount, color: restartCount > 0 ? colors.statusDeprecated : colors.textSecondary },
          { label: 'Unhealthy Pods', value: unhealthyCount, color: unhealthyCount > 0 ? colors.statusDown : colors.statusLive },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 10,
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flex: '1 1 140px',
            }}
          >
            <span style={{ fontSize: 24, fontWeight: 700, color: stat.color }}>{stat.value}</span>
            <span style={{ fontSize: 13, color: colors.textSecondary }}>{stat.label}</span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
        <Card
          style={{
            flex: 1,
            minWidth: 300,
            background: colors.surfaceSubtle,
            border: `1px solid ${colors.border}`,
            borderRadius: 10,
          }}
          bodyStyle={{ padding: '16px 20px' }}
        >
          <div style={{ fontWeight: 600, color: colors.textMuted, marginBottom: 12, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
            Deployment Overview
          </div>
          <InfoRow label="Deployment" value={operator.deploymentName} />
          <InfoRow label="Operator Container" value={operator.containerName || '—'} />
          <InfoRow label="Namespace" value={operator.namespace} />
          <InfoRow label="Strategy" value={operator.strategy || 'RollingUpdate'} />
          <InfoRow label="Image" value={
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{imageName}</span>
              <Tag style={{ background: colors.tmfBg, color: colors.tmfText, border: 'none' }}>{imageTag}</Tag>
            </span>
          } />
          <InfoRow label="Created" value={
            operator.createdAt ? (
              <Tooltip title={dayjs(operator.createdAt).format('YYYY-MM-DD HH:mm:ss')}>
                <span>{dayjs(operator.createdAt).fromNow()}</span>
              </Tooltip>
            ) : '—'
          } />
          <InfoRow label="Selector" value={
            operator.selector && Object.keys(operator.selector).length > 0 ? (
              <span style={{ display: 'inline-flex', flexWrap: 'wrap', gap: 6, justifyContent: 'flex-end' }}>
                {Object.entries(operator.selector).map(([key, value]) => (
                  <Tag
                    key={key}
                    style={{
                      fontSize: 11,
                      fontFamily: 'monospace',
                      background: colors.hoverSurface,
                      color: colors.textSecondary,
                      border: 'none',
                    }}
                  >
                    {key}={value}
                  </Tag>
                ))}
              </span>
            ) : '—'
          } />
        </Card>

        <Card
          style={{
            flex: 1,
            minWidth: 300,
            background: colors.surfaceSubtle,
            border: `1px solid ${colors.border}`,
            borderRadius: 10,
          }}
          bodyStyle={{ padding: '16px 20px' }}
        >
          <div style={{ fontWeight: 600, color: colors.textMuted, marginBottom: 12, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
            Runtime Health
          </div>
          <InfoRow label="Replica Health" value={`${operator.ready} / ${operator.desired} ready`} />
          <InfoRow label="Available Pods" value={operator.available} />
          <InfoRow label="Updated Pods" value={operator.updated} />
          <InfoRow label="Pod Restarts" value={restartCount} />
          <InfoRow label="Pod Count" value={operator.pods.length} />
          <InfoRow label="Primary Image" value={operator.image ? <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{operator.image}</span> : '—'} />
        </Card>
      </div>

      <Card
        style={{
          background: colors.bgCard,
          borderRadius: 12,
          border: `1px solid ${colors.border}`,
        }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: colors.textPrimary }}>Pods and Logs</div>
            <div style={{ fontSize: 13, color: colors.textSecondary }}>
              Select any operator pod to inspect its current logs or download them.
            </div>
          </div>
          {selectedPod && (
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => setSelectedPod(null)}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            >
              Back to pod list
            </Button>
          )}
        </div>

        {selectedPod ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              <Tag
                style={{
                  background: colors.infoSurface,
                  color: colors.infoText,
                  border: 'none',
                  borderRadius: 4,
                  fontFamily: 'monospace',
                  fontSize: 12,
                }}
              >
                {selectedPod.name}
              </Tag>
              <StatusBadge status={selectedPod.ready ? 'ready' : selectedPod.phase} size="sm" />
              {selectedPod.node && <span style={{ fontSize: 12, color: colors.textMuted }}>Node: {selectedPod.node}</span>}
              {selectedPod.podIP && <span style={{ fontSize: 12, color: colors.textMuted }}>Pod IP: {selectedPod.podIP}</span>}
            </div>
            <LogViewer
              key={selectedPod.name}
              title={`${selectedPod.name} current logs${operator.containerName ? ` · ${operator.containerName}` : ''}`}
              filename={`${selectedPod.name}${operator.containerName ? `-${operator.containerName}` : ''}-logs.txt`}
              fetchLogs={(tail) =>
                fetchOperatorPodLogs(
                  operator.namespace,
                  operator.name,
                  selectedPod.name,
                  tail,
                  operator.containerName,
                )
              }
              streamLogs={(opts) =>
                streamOperatorPodLogs(
                  operator.namespace,
                  operator.name,
                  selectedPod.name,
                  { ...opts, container: operator.containerName },
                )
              }
            />
          </div>
        ) : (
          <Table<OperatorPod>
            columns={podColumns}
            dataSource={operator.pods}
            rowKey="name"
            pagination={operator.pods.length > 10 ? { pageSize: 10, showSizeChanger: false } : false}
            expandable={{
              expandedRowRender: (record) => (
                <div style={{ padding: '8px 0' }}>
                  {record.podIP && (
                    <div style={{ marginBottom: 10, fontSize: 12, color: colors.textMuted }}>
                      Pod IP: <span style={{ color: colors.textSecondary, fontFamily: 'monospace' }}>{record.podIP}</span>
                    </div>
                  )}
                  {record.containers.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {record.containers.map((container) => (
                        <div
                          key={container.name}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 12,
                            padding: '8px 12px',
                            background: colors.surfaceSubtle,
                            borderRadius: 8,
                            border: `1px solid ${colors.border}`,
                            flexWrap: 'wrap',
                          }}
                        >
                          <StatusBadge status={container.ready ? 'ready' : container.state} size="sm" />
                          <span style={{ fontWeight: 600, color: colors.textPrimary }}>{container.name}</span>
                          {operator.containerName === container.name && (
                            <Tag
                              style={{
                                background: `${colors.primary}18`,
                                color: colors.primary,
                                border: 'none',
                                fontSize: 11,
                              }}
                            >
                              current operator
                            </Tag>
                          )}
                          <span style={{ color: colors.textMuted, fontFamily: 'monospace', fontSize: 12 }}>
                            {container.image}
                          </span>
                          {container.restarts > 0 && (
                            <Tag color="orange" style={{ fontSize: 11 }}>
                              {container.restarts} restart{container.restarts !== 1 ? 's' : ''}
                            </Tag>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: colors.textMuted, fontSize: 12 }}>No container metadata available.</div>
                  )}
                </div>
              ),
              rowExpandable: (record) => record.containers.length > 0 || !!record.podIP,
            }}
            onRow={(record) => ({
              onClick: () => setSelectedPod(record),
              style: { cursor: 'pointer' },
            })}
            size="small"
            style={{ background: 'transparent' }}
          />
        )}
      </Card>
    </div>
  )
}
