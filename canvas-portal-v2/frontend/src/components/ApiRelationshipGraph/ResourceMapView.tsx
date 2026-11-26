import React, { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import dagre from '@dagrejs/dagre'
import {
  CompressOutlined,
  DownloadOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  MinusOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { Button, Dropdown, Empty, Select, Space, Tag } from 'antd'

import type { GraphLink, GraphNode, GraphPayload } from '@/api/relationships'
import { colors } from '@/theme'
import { edgePath, nodeDimensions, type PositionedEdge } from './dagre-layout'
import { LINK_STYLES, NODE_STYLES, nodeTypeLabel, type RelationType } from './style'

interface ResourceMapViewProps {
  data: GraphPayload
  onSelectNode: (node: GraphNode) => void
}

interface MapNode extends GraphNode {
  x: number
  y: number
  width: number
  height: number
}

interface MapGroup {
  id: string
  label: string
  namespace: string
  x: number
  y: number
  width: number
  height: number
}

interface MapResult {
  nodes: MapNode[]
  edges: PositionedEdge[]
  groups: MapGroup[]
  bounds: { width: number; height: number }
}

const MAP_HEIGHT = 680
const MAP_PADDING = 54
const MIN_ZOOM = 0.035
const MAX_ZOOM = 2.6

export default function ResourceMapView({ data, onSelectNode }: ResourceMapViewProps) {
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)
  const canvasRef = useRef<SVGGElement | null>(null)
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const [namespace, setNamespace] = useState<string>()
  const [selectedComponentIds, setSelectedComponentIds] = useState<string[]>([])
  const [viewportWidth, setViewportWidth] = useState(1160)
  const [viewportHeight, setViewportHeight] = useState(MAP_HEIGHT)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const components = useMemo(() => {
    return data.nodes
      .filter((node) => node.nodeType === 'component' && (!namespace || node.namespace === namespace))
      .sort((a, b) => a.label.localeCompare(b.label))
  }, [data.nodes, namespace])

  const componentIdsKey = components.map((node) => node.id).join('|')
  useEffect(() => {
    const validIds = new Set(components.map((component) => component.id))
    setSelectedComponentIds((current) => {
      const valid = current.filter((id) => validIds.has(id))
      if (valid.length > 0) {
        return valid.length === current.length ? current : valid
      }
      return components[0] ? [components[0].id] : []
    })
  }, [componentIdsKey])

  const visibleGraph = useMemo(
    () => buildComponentNeighbourhood(data, selectedComponentIds),
    [data, selectedComponentIds],
  )
  const layout = useMemo(
    () => computeMapLayout(visibleGraph.nodes, visibleGraph.links),
    [visibleGraph],
  )
  const selectedSet = useMemo(() => new Set(selectedComponentIds), [selectedComponentIds])
  const layoutKey = useMemo(
    () => `${selectedComponentIds.join('|')}::${layout.nodes.map((node) => node.id).join('|')}`,
    [layout.nodes, selectedComponentIds],
  )

  useEffect(() => {
    if (!wrapperRef.current) return
    const observer = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect
      if (rect) {
        setViewportWidth(Math.max(820, Math.floor(rect.width)))
        setViewportHeight(Math.max(MAP_HEIGHT, Math.floor(rect.height)))
      }
    })
    observer.observe(wrapperRef.current)
    return () => observer.disconnect()
  }, [layout.nodes.length > 0])

  // Exit fullscreen on Escape — standard browser pattern.
  useEffect(() => {
    if (!isFullscreen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsFullscreen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isFullscreen])

  // Attach d3-zoom whenever the SVG is mounted. Has to depend on
  // `layout.nodes.length > 0` because the SVG is conditionally rendered
  // (empty state hides it), so refs are null on the first render and a
  // single-shot `useEffect(…, [])` would never see them.
  const hasNodes = layout.nodes.length > 0
  useEffect(() => {
    if (!hasNodes) return
    const svgEl = svgRef.current
    const canvas = canvasRef.current
    if (!svgEl || !canvas) return
    const svg = d3.select(svgEl)
    const graphCanvas = d3.select(canvas)
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([MIN_ZOOM, MAX_ZOOM])
      .filter((event) => {
        // Allow left-mouse-drag pan + wheel zoom; ignore right-click (so
        // browser context menu still works) and ignore drags that start
        // on a button so the toolbar still works inside the wrapper.
        if (event.type === 'mousedown' && event.button !== 0) return false
        const target = event.target as Element | null
        if (target?.closest('button')) return false
        return !event.ctrlKey && !event.metaKey
      })
      .on('zoom', (event) => graphCanvas.attr('transform', event.transform.toString()))
    zoomRef.current = zoom
    svg.call(zoom as never)
    // Set initial transform so subsequent fit-to-screen has something to compose with.
    svg.call((selection) => zoom.transform(selection as never, d3.zoomIdentity))
    return () => {
      svg.interrupt()
      svg.on('.zoom', null)
      zoomRef.current = null
    }
  }, [hasNodes])

  useEffect(() => {
    fitToScreen()
  }, [layoutKey, layout.bounds.width, layout.bounds.height, viewportWidth, viewportHeight, isFullscreen])

  function zoomBy(factor: number) {
    const svgEl = svgRef.current
    const zoom = zoomRef.current
    if (!svgEl || !zoom) return
    d3.select(svgEl).transition().duration(180).call((selection) => zoom.scaleBy(selection as never, factor))
  }

  function fitToScreen() {
    const svgEl = svgRef.current
    const zoom = zoomRef.current
    if (!svgEl || !zoom || layout.nodes.length === 0) return
    const scale = Math.min(
      (viewportWidth - MAP_PADDING * 2) / layout.bounds.width,
      (viewportHeight - MAP_PADDING * 2) / layout.bounds.height,
      1.15,
    )
    const safeScale = Math.max(MIN_ZOOM, scale)
    const translateX = (viewportWidth - layout.bounds.width * safeScale) / 2
    const translateY = (viewportHeight - layout.bounds.height * safeScale) / 2
    const transform = d3.zoomIdentity.translate(translateX, translateY).scale(safeScale)
    d3.select(svgEl).transition().duration(320).call((selection) => zoom.transform(selection as never, transform))
  }

  function downloadSvg() {
    const svgEl = svgRef.current
    if (!svgEl) return
    const clone = svgEl.cloneNode(true) as SVGSVGElement
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
    // Bake a sensible width/height so the file opens at a useful size in Inkscape/Figma.
    clone.setAttribute('width', String(layout.bounds.width))
    clone.setAttribute('height', String(layout.bounds.height))
    clone.setAttribute('viewBox', `0 0 ${layout.bounds.width} ${layout.bounds.height}`)
    const source = '<?xml version="1.0" standalone="no"?>\n' + new XMLSerializer().serializeToString(clone)
    downloadBlob(source, `resource-map-${timestamp()}.svg`, 'image/svg+xml;charset=utf-8')
  }

  function downloadDrawio() {
    if (layout.nodes.length === 0) return
    const idMap = new Map<string, string>()
    layout.nodes.forEach((node, i) => idMap.set(node.id, `n${i + 2}`))

    const cells: string[] = []
    cells.push('        <mxCell id="0"/>')
    cells.push('        <mxCell id="1" parent="0"/>')

    for (const node of layout.nodes) {
      const id = idMap.get(node.id)!
      const style = NODE_STYLES[node.nodeType]
      const typeLabel = nodeTypeLabel(node.nodeType).toUpperCase()
      const nsLine = node.namespace
        ? `<br/><font color="#94a3b8" style="font-size:10px">${escapeXmlText(node.namespace)}</font>`
        : ''
      const html = `<font color="${style.fill}" style="font-size:10px"><b>${escapeXmlText(typeLabel)}</b></font><br/><b>${escapeXmlText(node.label)}</b>${nsLine}`
      const drawioStyle = `rounded=1;whiteSpace=wrap;html=1;fillColor=${style.tint};strokeColor=${style.fill};fontSize=11;strokeWidth=1.4;align=left;verticalAlign=middle;spacingLeft=14;spacingRight=10;`
      const x = Math.round(node.x - node.width / 2)
      const y = Math.round(node.y - node.height / 2)
      cells.push(
        `        <mxCell id="${id}" value="${escapeXmlAttr(html)}" style="${drawioStyle}" vertex="1" parent="1"><mxGeometry x="${x}" y="${y}" width="${node.width}" height="${node.height}" as="geometry"/></mxCell>`,
      )
    }

    let edgeCounter = 0
    for (const edge of layout.edges) {
      const src = idMap.get(edge.source)
      const tgt = idMap.get(edge.target)
      if (!src || !tgt) continue
      const style = LINK_STYLES[edge.relation]
      const dashed = style.dashed ? 'dashed=1;dashPattern=7 5;' : ''
      const drawioStyle = `edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=classic;endFill=1;strokeColor=${style.stroke};strokeWidth=${style.width};${dashed}fontSize=10;fontColor=${style.stroke};`
      const edgeId = `e${++edgeCounter}`
      cells.push(
        `        <mxCell id="${edgeId}" value="${escapeXmlAttr(style.label)}" style="${drawioStyle}" edge="1" parent="1" source="${src}" target="${tgt}"><mxGeometry relative="1" as="geometry"/></mxCell>`,
      )
    }

    const w = Math.max(827, Math.round(layout.bounds.width))
    const h = Math.max(1169, Math.round(layout.bounds.height))
    const xml = `<mxfile host="canvas-portal" type="device">
  <diagram name="Resource Map" id="resource-map">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${w}" pageHeight="${h}" math="0" shadow="0">
      <root>
${cells.join('\n')}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`
    downloadBlob(xml, `resource-map-${timestamp()}.drawio`, 'application/xml;charset=utf-8')
  }

  const containerStyle: React.CSSProperties = isFullscreen
    ? {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1000,
        background: '#ffffff',
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        overflow: 'hidden',
      }
    : {}

  const wrapperStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    height: isFullscreen ? '100%' : MAP_HEIGHT,
    flex: isFullscreen ? 1 : undefined,
    border: `1px solid ${colors.border}`,
    borderRadius: 14,
    overflow: 'hidden',
    background: colors.surfaceSubtle,
    boxShadow: 'inset 0 1px 2px rgba(15,23,42,0.03)',
  }

  return (
    <div style={containerStyle}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        gap: 14, flexWrap: 'wrap', marginBottom: isFullscreen ? 0 : 14,
      }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 650, color: colors.textPrimary }}>Component relationship map</div>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>
            Select one or multiple components to display their complete API entry paths and dependencies.
          </div>
        </div>
        <Space wrap size={10}>
          <Select
            allowClear
            placeholder="All namespaces"
            value={namespace}
            onChange={setNamespace}
            style={{ width: 180 }}
            options={data.namespaces.map((ns) => ({ label: ns, value: ns }))}
          />
          <Select
            mode="multiple"
            showSearch
            value={selectedComponentIds}
            onChange={setSelectedComponentIds}
            optionFilterProp="label"
            placeholder="Select components"
            maxTagCount="responsive"
            options={components.map((node) => ({
              value: node.id,
              label: node.namespace ? `${node.label} (${node.namespace})` : node.label,
            }))}
            style={{ minWidth: 340, maxWidth: 480 }}
          />
          <Button
            disabled={components.length === 0}
            onClick={() => setSelectedComponentIds(components.map((node) => node.id))}
          >
            Select all
          </Button>
        </Space>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 10, marginBottom: isFullscreen ? 0 : 10,
      }}>
        <Space size={8} wrap>
          <Tag color="blue">{selectedComponentIds.length} selected components</Tag>
          <Tag color="cyan">{layout.nodes.length} related resources</Tag>
          <Tag color="geekblue">{layout.edges.length} relationships</Tag>
        </Space>
        <Space size={8} wrap>
          <Dropdown
            disabled={layout.nodes.length === 0}
            menu={{
              items: [
                { key: 'svg', label: 'Download SVG (image)', onClick: downloadSvg },
                { key: 'drawio', label: 'Download .drawio (XML for diagrams.net)', onClick: downloadDrawio },
              ],
            }}
          >
            <Button icon={<DownloadOutlined />}>Export</Button>
          </Dropdown>
          <Button
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={() => setIsFullscreen((v) => !v)}
          >
            {isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          </Button>
          <Space.Compact>
            <Button aria-label="Zoom out" icon={<MinusOutlined />} onClick={() => zoomBy(0.82)} />
            <Button icon={<CompressOutlined />} onClick={fitToScreen}>Fit</Button>
            <Button aria-label="Zoom in" icon={<PlusOutlined />} onClick={() => zoomBy(1.22)} />
          </Space.Compact>
        </Space>
      </div>

      <div ref={wrapperRef} style={wrapperStyle}>
        {layout.nodes.length === 0 ? (
          <div style={emptySurface}>
            <Empty description="Select at least one component to view its related resources" />
          </div>
        ) : (
          <svg
            ref={svgRef}
            viewBox={`0 0 ${viewportWidth} ${viewportHeight}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ display: 'block', width: '100%', height: '100%', cursor: 'grab' }}
          >
            <defs>
              <pattern id="resource-map-grid" width="28" height="28" patternUnits="userSpaceOnUse">
                <circle cx="1.5" cy="1.5" r="1.2" fill="#e2e8f0" />
              </pattern>
              {Object.entries(LINK_STYLES).map(([relation, style]) => {
                // Slightly larger markers on dep-api edges so the architectural
                // dependency direction reads as well as the traffic edges.
                const isDepApi = relation === 'declares' || relation === 'resolvesTo'
                const size = isDepApi ? 10 : 8
                return (
                  <marker
                    key={relation}
                    id={`resource-map-arrow-${relation}`}
                    viewBox="0 -5 10 10"
                    refX="9"
                    refY="0"
                    markerWidth={size}
                    markerHeight={size}
                    orient="auto"
                  >
                    <path d="M0,-5L10,0L0,5" fill={style.stroke} />
                  </marker>
                )
              })}
            </defs>
            <rect width={viewportWidth} height={viewportHeight} fill="#ffffff" />
            <rect width={viewportWidth} height={viewportHeight} fill="url(#resource-map-grid)" />
            <g ref={canvasRef}>
              {layout.groups.map((group) => (
                <MapGroupBox key={group.id} group={group} />
              ))}
              {layout.edges.map((edge) => (
                <MapEdge key={edge.id} edge={edge} />
              ))}
              {layout.nodes.map((node) => (
                <MapResourceCard
                  key={node.id}
                  node={node}
                  selected={selectedSet.has(node.id)}
                  onSelect={() => onSelectNode(node)}
                />
              ))}
            </g>
          </svg>
        )}
      </div>
    </div>
  )
}

function MapGroupBox({ group }: { group: MapGroup }) {
  return (
    <g pointerEvents="none">
      <rect
        x={group.x}
        y={group.y}
        width={group.width}
        height={group.height}
        rx={16}
        ry={16}
        fill="#f8fafc"
        fillOpacity={0.55}
        stroke="#94a3b8"
        strokeOpacity={0.55}
        strokeWidth={1.2}
        strokeDasharray="6 5"
      />
      <text
        x={group.x + 14}
        y={group.y + 18}
        fontSize="10"
        fontWeight="700"
        fill="#475569"
        letterSpacing="0.55"
      >
        {`COMPONENT · ${group.label}${group.namespace ? ` · ${group.namespace}` : ''}`.toUpperCase()}
      </text>
    </g>
  )
}

function MapEdge({ edge }: { edge: PositionedEdge }) {
  const style = LINK_STYLES[edge.relation]
  const midpoint = edge.points[Math.floor(edge.points.length / 2)]
  const pathString = edgePath(edge.points, 10)

  // Two visual buckets, mirroring Explore Topology:
  //   - "flowing" traffic edges (routesTo, fronts) → dashed line with the
  //     dash pattern animated, so direction is unmistakable at a glance.
  //   - everything else: solid for backedBy/policy, longer dashed for
  //     declares/resolvesTo (logical dep-api edges, no traffic flow).
  const isFlowing = edge.relation === 'routesTo' || edge.relation === 'fronts'
  const dashArray = isFlowing ? '6 4' : style.dashed ? '8 4' : undefined
  // Suppress labels on the animated traffic edges — the colour + flow
  // direction already communicates the relation, and the labels are dense.
  const showLabel = !isFlowing

  return (
    <g>
      <path
        d={pathString}
        fill="none"
        stroke={style.stroke}
        strokeWidth={style.width}
        strokeDasharray={dashArray}
        strokeLinecap={isFlowing || style.dashed ? 'round' : undefined}
        markerEnd={`url(#resource-map-arrow-${edge.relation})`}
        opacity={0.85}
      >
        {isFlowing && (
          <animate
            attributeName="stroke-dashoffset"
            from="0"
            to="-20"
            dur="0.9s"
            repeatCount="indefinite"
          />
        )}
      </path>
      {midpoint && showLabel && (
        <text
          x={midpoint.x}
          y={midpoint.y - 7}
          textAnchor="middle"
          fontSize="10"
          fontWeight="600"
          fill={style.stroke}
          stroke="#ffffff"
          strokeWidth="4"
          paintOrder="stroke"
        >
          {style.label}
        </text>
      )}
    </g>
  )
}

function MapResourceCard({
  node,
  selected,
  onSelect,
}: {
  node: MapNode
  selected: boolean
  onSelect: () => void
}) {
  const style = NODE_STYLES[node.nodeType]
  const statusText = node.ready === undefined ? undefined : node.ready ? 'READY' : 'NOT READY'
  const statusFill = node.ready ? '#dcfce7' : '#fee2e2'
  const statusColor = node.ready ? '#15803d' : '#b91c1c'

  // Components are visually emphasised: bigger card, larger type label and
  // primary name, wider bar.
  const isComponent = node.nodeType === 'component'
  const barWidth = isComponent ? 9 : 7
  const typeFontSize = isComponent ? 11 : 9
  const typeY = isComponent ? 22 : 17
  const nameFontSize = isComponent ? 16 : 12
  const nameY = isComponent ? 50 : 36
  const namespaceFontSize = isComponent ? 12 : 10
  const namespaceY = isComponent ? node.height - 18 : node.height - 13
  const pillWidth = isComponent ? 68 : 58
  const pillHeight = isComponent ? 20 : 17
  const pillFontSize = isComponent ? 10 : 8.5
  const pillY = isComponent ? 12 : 10
  const pillTextY = isComponent ? 25 : 21.5

  return (
    <g
      transform={`translate(${node.x - node.width / 2},${node.y - node.height / 2})`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') onSelect()
      }}
      style={{ cursor: 'pointer' }}
      aria-label={`${nodeTypeLabel(node.nodeType)} ${node.label}`}
    >
      <rect
        width={node.width}
        height={node.height}
        rx={isComponent ? 13 : 11}
        fill={style.tint}
        stroke={selected ? colors.primary : style.fill}
        strokeWidth={selected ? (isComponent ? 2.8 : 2.4) : isComponent ? 1.8 : 1.4}
        opacity={selected ? 1 : 0.95}
      />
      <rect x="0" y="10" width={barWidth} height={node.height - 20} rx={barWidth / 2} fill={style.fill} />
      <text
        x={isComponent ? 18 : 14}
        y={typeY}
        fontSize={typeFontSize}
        fontWeight="700"
        letterSpacing="0.55"
        fill={style.fill}
      >
        {selected ? 'SELECTED / ' : ''}
        {nodeTypeLabel(node.nodeType).toUpperCase()}
      </text>
      <text
        x={isComponent ? 18 : 14}
        y={nameY}
        fontSize={nameFontSize}
        fontWeight={isComponent ? 700 : 650}
        fill={colors.textPrimary}
      >
        {truncate(node.label, isComponent ? 32 : 25)}
      </text>
      {node.namespace && (
        <text
          x={isComponent ? 18 : 14}
          y={namespaceY}
          fontSize={namespaceFontSize}
          fill={colors.textMuted}
        >
          {truncate(node.namespace, isComponent ? 30 : 24)}
        </text>
      )}
      {statusText && (
        <>
          <rect
            x={node.width - pillWidth - 9}
            y={pillY}
            width={pillWidth}
            height={pillHeight}
            rx={pillHeight / 2}
            fill={statusFill}
          />
          <text
            x={node.width - pillWidth / 2 - 9}
            y={pillTextY}
            textAnchor="middle"
            fontSize={pillFontSize}
            fontWeight="700"
            fill={statusColor}
          >
            {statusText}
          </text>
        </>
      )}
    </g>
  )
}

function buildComponentNeighbourhood(data: GraphPayload, componentIds: string[]): { nodes: GraphNode[]; links: GraphLink[] } {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]))
  const selected = new Set(componentIds)
  const nodeIds = new Set<string>()
  const links = new Map<string, GraphLink>()
  const addNode = (id: string) => {
    if (nodeById.has(id)) nodeIds.add(id)
  }
  const addLink = (link: GraphLink) => {
    addNode(link.source)
    addNode(link.target)
    links.set(`${link.source}|${link.relation}|${link.target}`, link)
  }
  const incoming = (target: string, relation: RelationType) =>
    data.links.filter((link) => link.target === target && link.relation === relation)
  const outgoing = (source: string, relation: RelationType) =>
    data.links.filter((link) => link.source === source && link.relation === relation)

  for (const componentId of selected) {
    addNode(componentId)

    for (const apiLink of incoming(componentId, 'backedBy')) {
      addLink(apiLink)
      const apiId = apiLink.source

      for (const routeLink of incoming(apiId, 'routesTo')) {
        addLink(routeLink)
        const routeNode = nodeById.get(routeLink.source)
        if (routeNode?.nodeType === 'virtualService') {
          for (const ingressLink of incoming(routeNode.id, 'fronts')) {
            addLink(ingressLink)
            for (const policyLink of outgoing(ingressLink.source, 'policy')) addLink(policyLink)
          }
        }
        for (const policyLink of outgoing(routeLink.source, 'policy')) addLink(policyLink)
      }
    }

    for (const dependencyLink of outgoing(componentId, 'declares')) {
      addLink(dependencyLink)
      // Redirect each resolvesTo edge so it terminates at the provider Component
      // (skipping the intermediate ExposedAPI), per the architectural-overview
      // rendering: caller-component → dependentApi → provider-component.
      for (const resolutionLink of outgoing(dependencyLink.target, 'resolvesTo')) {
        const providerLinks = data.links.filter(
          (link) => link.source === resolutionLink.target && link.relation === 'backedBy',
        )
        if (providerLinks.length === 0) {
          addLink(resolutionLink)
          continue
        }
        for (const providerLink of providerLinks) {
          addLink({
            ...resolutionLink,
            target: providerLink.target,
          })
          addNode(providerLink.target)
        }
      }
    }
  }

  return {
    nodes: Array.from(nodeIds).map((id) => nodeById.get(id)!).filter(Boolean),
    links: Array.from(links.values()),
  }
}

function computeMapLayout(nodes: GraphNode[], links: GraphLink[]): MapResult {
  if (nodes.length === 0) return { nodes: [], edges: [], groups: [], bounds: { width: 0, height: 0 } }

  // -------------------------------------------------------------------------
  // Manual rank-and-row layout. We tried dagre with align/tight-tree/nodesep
  // tweaks and it still collapsed same-rank fan-in nodes (e.g. 3 HTTPRoutes
  // all fronting 3 VSes that all back one Component) onto identical y. This
  // layout walks the graph from each Component backwards through its
  // backedBy → routesTo → fronts chains, assigns one row per chain, and
  // places every node at a fixed (rank-x, row-y). Output is 100% predictable
  // and trivially debuggable.
  // -------------------------------------------------------------------------

  const RANK_X: Record<string, number> = {
    httpRoute:          MAP_PADDING + 80,
    apisixRoute:        MAP_PADDING + 80,
    kongIngress:        MAP_PADDING + 80,
    gateway:            MAP_PADDING + 80,
    kongPlugin:         MAP_PADDING + 80,
    apisixPluginConfig: MAP_PADDING + 80,
    virtualService:     MAP_PADDING + 460,
    exposedApi:         MAP_PADDING + 840,
    component:          MAP_PADDING + 1220,
    dependentApi:       MAP_PADDING + 1600,
  }
  const ROW_HEIGHT = 130
  const COMPONENT_GAP = 60        // extra vertical space between component blocks
  const TOP_PADDING = MAP_PADDING

  const nodeById = new Map(nodes.map((n) => [n.id, n]))
  const out = new Map<string, MapNode>()
  const place = (n: GraphNode, x: number, y: number) => {
    if (out.has(n.id)) return
    const dims = nodeDimensions(n.nodeType)
    out.set(n.id, { ...n, ...dims, x, y })
  }

  // index links for quick traversal
  const incomingByRelation = new Map<string, GraphLink[]>()
  const outgoingByRelation = new Map<string, GraphLink[]>()
  const idx = (key: string) => `${key}`
  for (const l of links) {
    const inKey  = idx(`${l.target}|${l.relation}|in`)
    const outKey = idx(`${l.source}|${l.relation}|out`)
    if (!incomingByRelation.has(inKey)) incomingByRelation.set(inKey, [])
    if (!outgoingByRelation.has(outKey)) outgoingByRelation.set(outKey, [])
    incomingByRelation.get(inKey)!.push(l)
    outgoingByRelation.get(outKey)!.push(l)
  }
  const incomingTo = (id: string, rel: RelationType) =>
    incomingByRelation.get(`${id}|${rel}|in`) ?? []
  const outgoingFrom = (id: string, rel: RelationType) =>
    outgoingByRelation.get(`${id}|${rel}|out`) ?? []

  // pick the components in stable order. Anything not reachable from a component
  // will be parked at the bottom in a "misc" lane afterwards.
  const components = nodes
    .filter((n) => n.nodeType === 'component')
    .sort((a, b) => `${a.namespace ?? ''}${a.label}`.localeCompare(`${b.namespace ?? ''}${b.label}`))

  // Per-component group membership (Component + its traffic chain, excluding
  // DependentAPIs). Used after placement to compute a bounding box for each
  // group so the renderer can draw a backdrop around it.
  const groupMembership = new Map<string, string[]>()
  const trackInGroup = (componentId: string, nodeId: string) => {
    if (!groupMembership.has(componentId)) groupMembership.set(componentId, [])
    groupMembership.get(componentId)!.push(nodeId)
  }

  let cursorY = TOP_PADDING
  for (const component of components) {
    // collect chains terminating at this component: every ExposedAPI that's
    // backedBy this component → (optional) its routesTo VS / gateway → (optional)
    // its fronting ingress route
    const apis = incomingTo(component.id, 'backedBy')
      .map((l) => nodeById.get(l.source))
      .filter((n): n is GraphNode => !!n)
      .sort((a, b) => a.label.localeCompare(b.label))

    const startY = cursorY
    const rowCount = Math.max(apis.length, 1)
    const centerY = startY + ((rowCount - 1) * ROW_HEIGHT) / 2

    // place each chain on its own row
    apis.forEach((api, rowIdx) => {
      const rowY = startY + rowIdx * ROW_HEIGHT

      // ExposedAPI
      place(api, RANK_X[api.nodeType], rowY)
      trackInGroup(component.id, api.id)

      // upstream routing chain
      for (const routeLink of incomingTo(api.id, 'routesTo')) {
        const route = nodeById.get(routeLink.source)
        if (!route) continue
        place(route, RANK_X[route.nodeType], rowY)
        trackInGroup(component.id, route.id)
        // ingress that fronts this route
        for (const frontLink of incomingTo(route.id, 'fronts')) {
          const ingress = nodeById.get(frontLink.source)
          if (!ingress) continue
          place(ingress, RANK_X[ingress.nodeType], rowY)
          trackInGroup(component.id, ingress.id)
          // any policies attached to the ingress
          outgoingFrom(ingress.id, 'policy').forEach((polLink, polIdx) => {
            const policy = nodeById.get(polLink.target)
            if (!policy) return
            // stack policies slightly offset to the side of the ingress
            place(policy, RANK_X[ingress.nodeType] - 200, rowY + (polIdx + 1) * 36)
            trackInGroup(component.id, policy.id)
          })
        }
        // any policies directly on this route
        outgoingFrom(route.id, 'policy').forEach((polLink, polIdx) => {
          const policy = nodeById.get(polLink.target)
          if (!policy) return
          place(policy, RANK_X[route.nodeType] - 200, rowY + (polIdx + 1) * 36)
          trackInGroup(component.id, policy.id)
        })
      }
    })

    // Component goes in the centre of its chain rows
    place(component, RANK_X.component, centerY)
    trackInGroup(component.id, component.id)

    // declared DependentAPIs and their resolution targets — deliberately NOT
    // tracked in the group, so the box wraps only the Component + its traffic
    // chain and DependentAPIs sit visually outside.
    outgoingFrom(component.id, 'declares').forEach((depLink, depIdx) => {
      const dep = nodeById.get(depLink.target)
      if (!dep) return
      const depY = centerY + depIdx * ROW_HEIGHT
      place(dep, RANK_X.dependentApi, depY)
      // resolvesTo now terminates at the provider Component (see neighbourhood
      // builder). If it isn't already placed (e.g. provider component is not in
      // the current selection), park it to the right of the DependentAPI.
      outgoingFrom(dep.id, 'resolvesTo').forEach((resLink, resIdx) => {
        const resolved = nodeById.get(resLink.target)
        if (!resolved || out.has(resolved.id)) return
        place(resolved, RANK_X[resolved.nodeType] + 1400, depY + resIdx * 80)
      })
    })

    cursorY = startY + Math.max(rowCount, 1) * ROW_HEIGHT + COMPONENT_GAP
  }

  // park any unplaced nodes in a misc lane at the bottom
  for (const n of nodes) {
    if (out.has(n.id)) continue
    place(n, MAP_PADDING + 80, cursorY)
    cursorY += ROW_HEIGHT
  }

  const placedNodes = Array.from(out.values())
  // Build edges from placed positions.
  //
  // Forward edges (source left of target): source.right → vertical bend →
  // target.left. Standard left-to-right traffic.
  //
  // Backward edges (e.g. resolvesTo, where a DependentAPI on the far right
  // points back to a Component on its left): naive routes either overlap the
  // backedBy edges entering the target from its left, OR overlap the
  // sibling declares edge that lives on the source's own row. We dodge both
  // by exiting the source from its TOP or BOTTOM (whichever faces the
  // target), running vertically through empty space, then horizontally into
  // the target's RIGHT side.
  const positionedEdges: PositionedEdge[] = links.map((l) => {
    const s = out.get(l.source)
    const t = out.get(l.target)
    const id = `${l.source}|${l.relation}|${l.target}`
    if (!s || !t) {
      return { ...l, id, points: [] }
    }

    if (s.x > t.x) {
      const targetAbove = t.y <= s.y
      const sExitY = targetAbove ? s.y - s.height / 2 : s.y + s.height / 2
      const tRight = t.x + t.width / 2
      return {
        ...l,
        id,
        points: [
          { x: s.x, y: sExitY },
          { x: s.x, y: t.y },
          { x: tRight, y: t.y },
        ],
      }
    }

    const sx = s.x + s.width / 2
    const sy = s.y
    const tx = t.x - t.width / 2
    const ty = t.y
    const midX = sx + (tx - sx) / 2
    return {
      ...l,
      id,
      points: sy === ty
        ? [{ x: sx, y: sy }, { x: tx, y: ty }]
        : [{ x: sx, y: sy }, { x: midX, y: sy }, { x: midX, y: ty }, { x: tx, y: ty }],
    }
  })

  // Build group bounding boxes from the membership map. Each group wraps a
  // Component and its traffic chain (HTTPRoutes, VSes, ExposedAPIs, policies)
  // but deliberately excludes its DependentAPIs.
  const GROUP_PAD_X = 22
  const GROUP_PAD_TOP = 28
  const GROUP_PAD_BOTTOM = 18
  const groups: MapGroup[] = []
  for (const component of components) {
    const memberIds = groupMembership.get(component.id) ?? []
    const memberNodes = memberIds
      .map((id) => out.get(id))
      .filter((n): n is MapNode => !!n)
    if (memberNodes.length === 0) continue
    const xs = memberNodes.flatMap((n) => [n.x - n.width / 2, n.x + n.width / 2])
    const ys = memberNodes.flatMap((n) => [n.y - n.height / 2, n.y + n.height / 2])
    const gMinX = Math.min(...xs) - GROUP_PAD_X
    const gMaxX = Math.max(...xs) + GROUP_PAD_X
    const gMinY = Math.min(...ys) - GROUP_PAD_TOP
    const gMaxY = Math.max(...ys) + GROUP_PAD_BOTTOM
    groups.push({
      id: component.id,
      label: component.label,
      namespace: component.namespace ?? '',
      x: gMinX,
      y: gMinY,
      width: gMaxX - gMinX,
      height: gMaxY - gMinY,
    })
  }

  const allX = placedNodes.flatMap((n) => [n.x - n.width / 2, n.x + n.width / 2])
  const allY = placedNodes.flatMap((n) => [n.y - n.height / 2, n.y + n.height / 2])
  // Include group rectangles in the bounds so the SVG fits everything.
  const allGroupX = groups.flatMap((g) => [g.x, g.x + g.width])
  const allGroupY = groups.flatMap((g) => [g.y, g.y + g.height])
  const minX = Math.min(0, ...allX, ...allGroupX)
  const minY = Math.min(0, ...allY, ...allGroupY)
  const maxX = Math.max(0, ...allX, ...allGroupX)
  const maxY = Math.max(0, ...allY, ...allGroupY)

  return {
    nodes: placedNodes,
    edges: positionedEdges,
    groups,
    bounds: {
      width: maxX - minX + MAP_PADDING,
      height: maxY - minY + MAP_PADDING,
    },
  }
}

function truncate(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max - 3)}...` : value
}

function escapeXmlText(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function escapeXmlAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function timestamp(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
}

const emptySurface: React.CSSProperties = {
  height: '100%',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
}
