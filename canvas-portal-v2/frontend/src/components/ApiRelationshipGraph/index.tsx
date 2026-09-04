import React, { useState } from 'react'
import { Alert, Button, Empty, Space, Spin, Tag } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'

import { useApiRelationshipGraph, type GraphNode } from '@/api/relationships'
import NodeDetailsDrawer from './NodeDetailsDrawer'
import ResourceMapView from './ResourceMapView'
import { colors } from '@/theme'

export default function ApiRelationshipGraph() {
  const query = useApiRelationshipGraph()
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  return (
    <div>
      <div
        style={{
          marginBottom: 14,
          padding: '14px 16px',
          background: '#ffffff',
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(15,23,42,0.04)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 16,
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ fontSize: 15, fontWeight: 650, color: colors.textPrimary }}>API Routing Explorer</div>
            <div style={{ fontSize: 12, color: colors.textMuted }}>
              Inspect ingress chains, component ownership, and dependencies across the cluster.
            </div>
          </div>
          <Space size={10} wrap>
            <Tag color="blue">{query.data?.nodes.length ?? 0} resources</Tag>
            <Tag color="cyan">{query.data?.links.length ?? 0} relationships</Tag>
            <Tag color="green">{query.data?.namespaces.length ?? 0} namespaces</Tag>
            <Button icon={<ReloadOutlined />} loading={query.isFetching} onClick={() => query.refetch()}>
              Refresh
            </Button>
          </Space>
        </div>
      </div>

      {query.isLoading ? (
        <div style={{ padding: 80, display: 'flex', justifyContent: 'center' }}>
          <Spin />
        </div>
      ) : query.isError ? (
        <Alert
          type="error"
          showIcon
          message="Failed to load graph"
          description={(query.error as Error)?.message}
        />
      ) : query.data ? (
        <ResourceMapView data={query.data} onSelectNode={setSelectedNode} />
      ) : (
        <Empty description="No resources yet" />
      )}

      <NodeDetailsDrawer
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onSelectNode={setSelectedNode}
      />
    </div>
  )
}
