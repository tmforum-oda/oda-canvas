import React from 'react'
import { Modal, Table, Tag, Spin, Alert } from 'antd'
import { HistoryOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { getHelmHistory, type HelmRevision } from '@/api/helm'
import { colors } from '@/theme'

interface Props {
  open: boolean
  onClose: () => void
  releaseName: string
  namespace: string
}

const STATUS_COLORS: Record<string, string> = {
  deployed: colors.statusLive,
  superseded: colors.statusDeprecated,
  failed: colors.statusDown,
  uninstalling: colors.statusDeprecated,
  pending: colors.textMuted,
  'pending-install': colors.textMuted,
  'pending-upgrade': colors.textMuted,
  'pending-rollback': colors.textMuted,
}

function statusColor(status: string): string {
  return STATUS_COLORS[status?.toLowerCase()] ?? colors.textMuted
}

export default function HelmHistoryModal({ open, onClose, releaseName, namespace }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['helm-history', releaseName, namespace],
    queryFn: () => getHelmHistory(releaseName, namespace),
    enabled: open && !!releaseName && !!namespace,
    staleTime: 30_000,
  })

  const columns = [
    {
      title: 'Revision',
      dataIndex: 'revision',
      width: 80,
      render: (v: number) => (
        <span style={{ fontWeight: 700, color: colors.primary, fontFamily: 'monospace' }}>{v}</span>
      ),
    },
    {
      title: 'Updated',
      dataIndex: 'updated',
      render: (v: string) => {
        if (!v) return '—'
        try {
          return new Date(v).toLocaleString()
        } catch {
          return v
        }
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 120,
      render: (v: string) => (
        <Tag
          style={{
            color: statusColor(v),
            background: `${statusColor(v)}20`,
            border: `1px solid ${statusColor(v)}50`,
            borderRadius: 999,
            fontFamily: 'monospace',
            fontSize: 11,
          }}
        >
          {v}
        </Tag>
      ),
    },
    {
      title: 'Chart',
      dataIndex: 'chart',
      render: (v: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: colors.textSecondary }}>{v}</span>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string) => (
        <span style={{ fontSize: 12, color: colors.textMuted }}>{v || '—'}</span>
      ),
    },
  ]

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <HistoryOutlined style={{ color: colors.primary }} />
          <div>
            <span style={{ color: colors.textPrimary }}>Release History</span>
            <span
              style={{
                marginLeft: 10,
                fontSize: 12,
                fontFamily: 'monospace',
                color: colors.textMuted,
                background: colors.primarySurface,
                border: `1px solid ${colors.primaryBorder}`,
                borderRadius: 4,
                padding: '2px 8px',
              }}
            >
              {releaseName} / {namespace}
            </span>
          </div>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={820}
    >
      {isLoading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      )}

      {error && (
        <Alert
          type="error"
          message={(error as Error).message ?? 'Failed to load history'}
          style={{ marginBottom: 12 }}
        />
      )}

      {data && (
        <Table<HelmRevision>
          dataSource={[...data].reverse()}
          columns={columns}
          rowKey="revision"
          size="small"
          pagination={false}
          style={{ marginTop: 8 }}
        />
      )}
    </Modal>
  )
}
