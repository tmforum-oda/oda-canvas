import React from 'react'
import { Table, Tag, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { InfoCircleOutlined } from '@ant-design/icons'
import type { ComponentPod } from '@/api/components'
import StatusBadge from './StatusBadge'
import { colors } from '@/theme'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

interface PodListProps {
  pods: ComponentPod[]
  loading?: boolean
  onViewLogs?: (pod: ComponentPod) => void
}

export default function PodList({ pods, loading = false, onViewLogs }: PodListProps) {
  const columns: ColumnsType<ComponentPod> = [
    {
      title: 'Pod Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <span
          style={{
            fontFamily: 'monospace',
            fontSize: 12,
            color: colors.textPrimary,
            background: colors.primarySurface,
            padding: '2px 6px',
            borderRadius: 4,
          }}
        >
          {name}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'phase',
      key: 'phase',
      width: 110,
      render: (phase: string, record: ComponentPod) => (
        <StatusBadge status={record.ready ? 'ready' : phase.toLowerCase()} size="sm" />
      ),
    },
    {
      title: 'Ready',
      key: 'ready',
      width: 70,
      render: (_: unknown, record: ComponentPod) => (
        <span style={{ color: record.ready ? colors.statusLive : colors.statusDown, fontWeight: 600 }}>
          {record.ready ? 'Yes' : 'No'}
        </span>
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
            color: restarts > 5 ? colors.statusDown : restarts > 0 ? colors.statusDeprecated : colors.textSecondary,
            fontWeight: restarts > 0 ? 600 : 400,
          }}
        >
          {restarts}
        </span>
      ),
    },
    {
      title: 'Image',
      dataIndex: 'image',
      key: 'image',
      ellipsis: true,
      render: (image: string) => (
        <Tooltip title={image}>
          <span style={{ fontSize: 12, color: colors.textSecondary, fontFamily: 'monospace' }}>
            {image.split('/').pop()}
          </span>
        </Tooltip>
      ),
    },
    {
      title: 'Node',
      dataIndex: 'node',
      key: 'node',
      ellipsis: true,
      render: (node?: string) =>
        node ? (
          <span style={{ fontSize: 12, color: colors.textMuted }}>{node}</span>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
    {
      title: 'Age',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 100,
      render: (createdAt?: string) =>
        createdAt ? (
          <Tooltip title={dayjs(createdAt).format('YYYY-MM-DD HH:mm:ss')}>
            <span style={{ color: colors.textMuted, fontSize: 12 }}>
              {dayjs(createdAt).fromNow(true)}
            </span>
          </Tooltip>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
  ]

  if (onViewLogs) {
    columns.push({
      title: 'Actions',
      key: 'actions',
      width: 90,
      render: (_: unknown, record: ComponentPod) => (
        <button
          onClick={() => onViewLogs(record)}
          style={{
            background: colors.primarySurface,
            border: `1px solid ${colors.primaryBorder}`,
            borderRadius: 6,
            color: colors.tmfText,
            cursor: 'pointer',
            padding: '4px 10px',
            fontSize: 12,
            fontWeight: 500,
          }}
        >
          Logs
        </button>
      ),
    })
  }

  return (
    <Table<ComponentPod>
      columns={columns}
      dataSource={pods}
      rowKey="name"
      loading={loading}
      size="small"
      pagination={pods.length > 10 ? { pageSize: 10, showSizeChanger: false } : false}
      expandable={{
        expandedRowRender: (record) =>
          record.containers?.length ? (
            <div style={{ padding: '8px 0' }}>
              <div style={{ fontSize: 12, color: colors.textMuted, marginBottom: 6 }}>Containers:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {record.containers.map((c) => (
                  <div
                    key={c.name}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '6px 12px',
                      background: colors.hoverSurface,
                      borderRadius: 6,
                      fontSize: 12,
                    }}
                  >
                    <StatusBadge status={c.ready ? 'ready' : c.state} size="sm" />
                    <span style={{ fontWeight: 600, color: colors.textPrimary }}>{c.name}</span>
                    <span style={{ color: colors.textMuted, fontFamily: 'monospace' }}>
                      {c.image.split('/').pop()}
                    </span>
                    {c.restarts > 0 && (
                      <Tag color="orange" style={{ fontSize: 11 }}>
                        {c.restarts} restart{c.restarts !== 1 ? 's' : ''}
                      </Tag>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : null,
        rowExpandable: (record) => !!record.containers?.length,
      }}
      style={{ background: 'transparent' }}
    />
  )
}
