import React, { useMemo } from 'react'
import { Button, Descriptions, Drawer, Empty, Space, Tabs, Tag } from 'antd'

import type { GraphNode, GraphPayload } from '@/api/relationships'
import StatusBadge from '@/components/StatusBadge'
import { colors } from '@/theme'
import { LINK_STYLES, nodeTypeLabel } from './style'

interface NodeDetailsDrawerProps {
  node: GraphNode | null
  graph?: GraphPayload
  onClose: () => void
  onSelectNode: (node: GraphNode) => void
}

interface ConnectedResource {
  node: GraphNode
  relation: keyof typeof LINK_STYLES
  direction: 'incoming' | 'outgoing'
}

export default function NodeDetailsDrawer({
  node,
  graph,
  onClose,
  onSelectNode,
}: NodeDetailsDrawerProps) {
  const related = useMemo(() => {
    if (!node || !graph) return [] as ConnectedResource[]
    const byId = new Map(graph.nodes.map((candidate) => [candidate.id, candidate]))
    const connections: ConnectedResource[] = []
    for (const link of graph.links) {
      if (link.source === node.id) {
        const target = byId.get(link.target)
        if (target) connections.push({ node: target, relation: link.relation, direction: 'outgoing' })
      }
      if (link.target === node.id) {
        const source = byId.get(link.source)
        if (source) connections.push({ node: source, relation: link.relation, direction: 'incoming' })
      }
    }
    return connections
  }, [graph, node])

  if (!node) {
    return <Drawer open={false} onClose={onClose} />
  }

  const raw = isRecord(node.raw) ? node.raw : {}
  const details = getRoutingDetails(raw)
  const metadata = getMetadata(raw)
  const incoming = related.filter((item) => item.direction === 'incoming')
  const outgoing = related.filter((item) => item.direction === 'outgoing')

  return (
    <Drawer
      title={(
        <div>
          <div style={{ fontSize: 15, fontWeight: 650 }}>{node.label}</div>
          <div style={{ fontSize: 12, fontWeight: 400, color: colors.textMuted }}>{nodeTypeLabel(node.nodeType)}</div>
        </div>
      )}
      placement="right"
      width={560}
      open
      onClose={onClose}
    >
      <Space wrap style={{ marginBottom: 16 }}>
        <Tag color="blue">{nodeTypeLabel(node.nodeType)}</Tag>
        {node.namespace && <Tag>{node.namespace}</Tag>}
        {node.ready !== undefined && (
          <StatusBadge status={node.ready ? 'ready' : 'not-ready'} size="sm" />
        )}
      </Space>
      <Tabs
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: (
              <div>
                <Descriptions bordered size="small" column={1}>
                  <Descriptions.Item label="Resource">{node.label}</Descriptions.Item>
                  <Descriptions.Item label="Type">{nodeTypeLabel(node.nodeType)}</Descriptions.Item>
                  {node.namespace && <Descriptions.Item label="Namespace">{node.namespace}</Descriptions.Item>}
                  {node.url && (
                    <Descriptions.Item label="Endpoint">
                      <a href={node.url} target="_blank" rel="noreferrer">{node.url}</a>
                    </Descriptions.Item>
                  )}
                  {metadata.map((item) => (
                    <Descriptions.Item key={item.label} label={item.label}>{item.value}</Descriptions.Item>
                  ))}
                </Descriptions>
                <SectionTitle>Connectivity</SectionTitle>
                <ConnectionSummary incoming={incoming.length} outgoing={outgoing.length} />
              </div>
            ),
          },
          {
            key: 'routing',
            label: 'Routing',
            children: (
              <div>
                {details.length > 0 && (
                  <>
                    <Descriptions bordered size="small" column={1}>
                      {details.map((item) => (
                        <Descriptions.Item key={item.label} label={item.label}>{item.value}</Descriptions.Item>
                      ))}
                    </Descriptions>
                    <SectionTitle>Relationships</SectionTitle>
                  </>
                )}
                <ResourceConnections
                  title="Incoming"
                  resources={incoming}
                  onSelectNode={onSelectNode}
                />
                <ResourceConnections
                  title="Outgoing"
                  resources={outgoing}
                  onSelectNode={onSelectNode}
                />
              </div>
            ),
          },
          {
            key: 'raw',
            label: 'Raw data',
            children: (
              <pre style={{
                background: colors.codeBg, color: colors.codeText, padding: 14,
                borderRadius: 8, maxHeight: 'calc(100vh - 190px)', overflow: 'auto',
                fontSize: 12, lineHeight: 1.5,
              }}>
                {JSON.stringify(node.raw, null, 2)}
              </pre>
            ),
          },
        ]}
      />
    </Drawer>
  )
}

function ResourceConnections({
  title,
  resources,
  onSelectNode,
}: {
  title: string
  resources: ConnectedResource[]
  onSelectNode: (node: GraphNode) => void
}) {
  return (
    <div style={{ marginBottom: 18 }}>
      <SectionTitle>{title}</SectionTitle>
      {resources.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={`No ${title.toLowerCase()} relationships`} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {resources.map((item) => (
            <div
              key={`${item.direction}:${item.relation}:${item.node.id}`}
              style={{
                padding: '9px 11px', border: `1px solid ${colors.borderLight}`,
                borderRadius: 8, background: colors.surfaceSubtle,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8,
              }}
            >
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: colors.textPrimary }}>{item.node.label}</div>
                <div style={{ fontSize: 11, color: colors.textSecondary }}>
                  {nodeTypeLabel(item.node.nodeType)} - {LINK_STYLES[item.relation].label}
                </div>
              </div>
              <Button size="small" onClick={() => onSelectNode(item.node)}>Open</Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ConnectionSummary({ incoming, outgoing }: { incoming: number; outgoing: number }) {
  return (
    <Space size={10}>
      <Tag color="geekblue">{incoming} incoming</Tag>
      <Tag color="cyan">{outgoing} outgoing</Tag>
    </Space>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ margin: '18px 0 10px', fontSize: 12, fontWeight: 700, color: colors.textSecondary }}>
      {children}
    </div>
  )
}

function getMetadata(raw: Record<string, unknown>): Array<{ label: string; value: string }> {
  const fields: Array<[string, string]> = [
    ['Status', asString(raw.status) || asString(raw.phase)],
    ['API type', asString(raw.apiType)],
    ['Version', asString(raw.version)],
    ['Implementation', asString(raw.implementation)],
    ['Port', asString(raw.port)],
    ['Functional block', asString(raw.functionalBlock)],
    ['Created', asString(raw.createdAt)],
  ]
  return fields.filter(([, value]) => !!value).map(([label, value]) => ({ label, value }))
}

function getRoutingDetails(raw: Record<string, unknown>): Array<{ label: string; value: string }> {
  const candidate = isRecord(raw.details)
    ? raw.details
    : isRecord(raw.gatewayDetails)
      ? raw.gatewayDetails
      : {}
  const fields: Array<[string, unknown]> = [
    ['Hosts', candidate.hosts ?? candidate.hostnames],
    ['Paths', candidate.paths],
    ['Gateways', candidate.gateways],
    ['Backends', candidate.backendRefs],
    ['Plugins', candidate.pluginNames ?? candidate.pluginConfigNames],
    ['Rules', candidate.rulesCount],
  ]
  return fields.flatMap(([label, value]) => {
    const rendered = displayValue(value)
    return rendered ? [{ label, value: rendered }] : []
  })
}

function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(asString).filter(Boolean).join(', ')
  if (typeof value === 'number') return String(value)
  return asString(value)
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
