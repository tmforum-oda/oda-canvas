// Compute deterministic node positions via @dagrejs/dagre so the graph reads
// as a clean top-to-bottom DAG with minimum edge crossings. Replaces the old
// d3-force simulation — same data always produces the same layout (no
// reshuffles on refresh). d3 still handles rendering, zoom, drag, hover.

import dagre from '@dagrejs/dagre'

import type { NodeType, RelationType } from './style'

const NODE_DIMS: Record<NodeType, { width: number; height: number }> = {
  component:          { width: 290, height: 108 },
  exposedApi:         { width: 222, height: 66 },
  dependentApi:       { width: 222, height: 66 },
  virtualService:     { width: 208, height: 62 },
  httpRoute:          { width: 208, height: 62 },
  apisixRoute:        { width: 208, height: 62 },
  kongIngress:        { width: 208, height: 62 },
  gateway:            { width: 208, height: 62 },
  kongPlugin:         { width: 190, height: 56 },
  apisixPluginConfig: { width: 190, height: 56 },
}

export function nodeDimensions(t: NodeType): { width: number; height: number } {
  return NODE_DIMS[t] ?? { width: 180, height: 60 }
}

export type LayoutDensity = 'compact' | 'comfortable' | 'spacious'

const LAYOUT_SPACING: Record<LayoutDensity, {
  nodesep: number
  ranksep: number
  edgesep: number
  margin: number
}> = {
  compact: { nodesep: 54, ranksep: 92, edgesep: 28, margin: 28 },
  comfortable: { nodesep: 104, ranksep: 138, edgesep: 42, margin: 44 },
  spacious: { nodesep: 154, ranksep: 178, edgesep: 58, margin: 58 },
}

export interface DagreInputNode {
  id: string
  nodeType: NodeType
}

export interface DagreInputEdge {
  id: string
  source: string
  target: string
  relation: RelationType
}

export interface PositionedNode extends DagreInputNode {
  x: number   // centre
  y: number   // centre
  width: number
  height: number
}

export interface PositionedEdge extends DagreInputEdge {
  points: Array<{ x: number; y: number }>   // polyline waypoints (includes endpoints)
}

export interface LayoutResult {
  nodes: PositionedNode[]
  edges: PositionedEdge[]
  bounds: { width: number; height: number }
}

export function computeLayout(
  nodes: DagreInputNode[],
  edges: DagreInputEdge[],
  density: LayoutDensity = 'comfortable',
): LayoutResult {
  const spacing = LAYOUT_SPACING[density]
  const g = new dagre.graphlib.Graph({ multigraph: true, compound: false })
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({
    rankdir: 'TB',
    nodesep: spacing.nodesep,
    ranksep: spacing.ranksep,
    edgesep: spacing.edgesep,
    marginx: spacing.margin,
    marginy: spacing.margin,
    align: 'UL',
    // 'longest-path' lays things out faster; 'tight-tree' / 'network-simplex' look better but are slower.
    ranker: 'network-simplex',
  })

  for (const n of nodes) {
    const dims = nodeDimensions(n.nodeType)
    g.setNode(n.id, { width: dims.width, height: dims.height })
  }
  for (const e of edges) {
    g.setEdge(e.source, e.target, { weight: 1 }, e.id)
  }

  dagre.layout(g)

  const positionedNodes: PositionedNode[] = nodes.map((n) => {
    const node = g.node(n.id)
    const dims = nodeDimensions(n.nodeType)
    return {
      ...n,
      x: node?.x ?? 0,
      y: node?.y ?? 0,
      width: dims.width,
      height: dims.height,
    }
  })

  const positionedEdges: PositionedEdge[] = edges.map((e) => {
    const ed = g.edge({ v: e.source, w: e.target, name: e.id })
    return {
      ...e,
      points: (ed?.points ?? []).map((p: { x: number; y: number }) => ({ x: p.x, y: p.y })),
    }
  })

  const gRect = g.graph()
  return {
    nodes: positionedNodes,
    edges: positionedEdges,
    bounds: { width: gRect.width ?? 1000, height: gRect.height ?? 800 },
  }
}

/** Build a polyline path string for an edge, optionally rounded corners. */
export function edgePath(points: Array<{ x: number; y: number }>, cornerRadius = 8): string {
  if (points.length === 0) return ''
  if (points.length === 1) return `M${points[0].x},${points[0].y}`
  if (points.length === 2 || cornerRadius <= 0) {
    return 'M' + points.map((p) => `${p.x},${p.y}`).join('L')
  }
  const segs: string[] = [`M${points[0].x},${points[0].y}`]
  for (let i = 1; i < points.length - 1; i++) {
    const a = points[i - 1]
    const b = points[i]
    const c = points[i + 1]
    const ab = Math.hypot(b.x - a.x, b.y - a.y)
    const bc = Math.hypot(c.x - b.x, c.y - b.y)
    const r = Math.min(cornerRadius, ab / 2, bc / 2)
    const ux1 = (b.x - a.x) / ab
    const uy1 = (b.y - a.y) / ab
    const ux2 = (c.x - b.x) / bc
    const uy2 = (c.y - b.y) / bc
    const p1 = { x: b.x - ux1 * r, y: b.y - uy1 * r }
    const p2 = { x: b.x + ux2 * r, y: b.y + uy2 * r }
    segs.push(`L${p1.x},${p1.y}`)
    segs.push(`Q${b.x},${b.y} ${p2.x},${p2.y}`)
  }
  const last = points[points.length - 1]
  segs.push(`L${last.x},${last.y}`)
  return segs.join(' ')
}
