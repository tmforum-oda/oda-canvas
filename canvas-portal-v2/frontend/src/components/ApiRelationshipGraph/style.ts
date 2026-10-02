// Visual palette for the API relationship graph.
// Adapted from Knowledge-graph/html_templates/html-d3-template.html and the
// portal's theme to give each node/edge type a consistent visual identity.

export type NodeType =
  | 'component'
  | 'exposedApi'
  | 'dependentApi'
  | 'virtualService'
  | 'httpRoute'
  | 'apisixRoute'
  | 'kongIngress'
  | 'kongPlugin'
  | 'apisixPluginConfig'
  | 'gateway' // generic fallback

export type RelationType =
  | 'backedBy'     // ExposedAPI -> Component (traffic terminates at the component)
  | 'declares'     // Component -> DependentAPI (declarative; upward in new layout)
  | 'routesTo'     // Gateway resource -> ExposedAPI (traffic flow: gateway forwards to the API)
  | 'fronts'       // Ingress route (HTTPRoute/Apisix/Kong) -> VirtualService (via istio-ingress)
  | 'resolvesTo'   // DependentAPI -> ExposedAPI (cross-component dependency resolution)
  | 'policy'       // gateway resource -> plugin/policy

export interface NodeStyle {
  fill: string
  stroke: string
  tint: string       // pastel background used by ResourceMapView cards + drawio export
  shape: 'rect' | 'circle' | 'diamond'
  size: number       // radius for circles, half-side for rect/diamond
  textColor: string
}

export interface LinkStyle {
  stroke: string
  width: number
  dashed: boolean
  label: string
}

export const NODE_STYLES: Record<NodeType, NodeStyle> = {
  component: {
    fill: '#1d4ed8',
    stroke: '#1e3a8a',
    tint: '#eff6ff',
    shape: 'rect',
    size: 30,
    textColor: '#ffffff',
  },
  exposedApi: {
    fill: '#059669',
    stroke: '#047857',
    tint: '#ecfdf5',
    shape: 'circle',
    size: 18,
    textColor: '#ffffff',
  },
  dependentApi: {
    fill: '#7c3aed',
    stroke: '#5b21b6',
    tint: '#f5f3ff',
    shape: 'circle',
    size: 14,
    textColor: '#ffffff',
  },
  virtualService: {
    fill: '#0ea5e9',
    stroke: '#0369a1',
    tint: '#f0f9ff',
    shape: 'diamond',
    size: 16,
    textColor: '#ffffff',
  },
  httpRoute: {
    fill: '#16a34a',
    stroke: '#15803d',
    tint: '#f0fdf4',
    shape: 'diamond',
    size: 16,
    textColor: '#ffffff',
  },
  apisixRoute: {
    fill: '#f97316',
    stroke: '#c2410c',
    tint: '#fff7ed',
    shape: 'diamond',
    size: 16,
    textColor: '#ffffff',
  },
  kongIngress: {
    fill: '#dc2626',
    stroke: '#991b1b',
    tint: '#fef2f2',
    shape: 'diamond',
    size: 16,
    textColor: '#ffffff',
  },
  kongPlugin: {
    fill: '#b91c1c',
    stroke: '#7f1d1d',
    tint: '#fef2f2',
    shape: 'diamond',
    size: 12,
    textColor: '#ffffff',
  },
  apisixPluginConfig: {
    fill: '#ea580c',
    stroke: '#9a3412',
    tint: '#fff7ed',
    shape: 'diamond',
    size: 12,
    textColor: '#ffffff',
  },
  gateway: {
    fill: '#6b7280',
    stroke: '#374151',
    tint: '#f9fafb',
    shape: 'diamond',
    size: 16,
    textColor: '#ffffff',
  },
}

export const LINK_STYLES: Record<RelationType, LinkStyle> = {
  routesTo:    { stroke: '#047857', width: 2.0, dashed: false, label: 'routes to' },
  fronts:      { stroke: '#0ea5e9', width: 2.6, dashed: false, label: 'fronts (via istio-ingress)' },
  backedBy:    { stroke: '#1e3a8a', width: 2.2, dashed: false, label: 'backed by' },
  declares:    { stroke: '#5b21b6', width: 1.4, dashed: true,  label: 'declares' },
  resolvesTo:  { stroke: '#7c3aed', width: 2.0, dashed: true,  label: 'resolves to' },
  policy:      { stroke: '#b91c1c', width: 1.2, dashed: true,  label: 'policy' },
}

// Status overlays (a red ring around unhealthy nodes)
export function statusRingColor(ready?: boolean): string | null {
  if (ready === undefined) return null
  return ready ? null : '#dc2626'
}

// Human-readable label for a node type (used by legend + side panel)
export function nodeTypeLabel(t: NodeType): string {
  switch (t) {
    case 'component': return 'Component'
    case 'exposedApi': return 'ExposedAPI'
    case 'dependentApi': return 'DependentAPI'
    case 'virtualService': return 'VirtualService (Istio)'
    case 'httpRoute': return 'HTTPRoute (Gateway API)'
    case 'apisixRoute': return 'ApisixRoute'
    case 'kongIngress': return 'KongIngress'
    case 'kongPlugin': return 'KongPlugin'
    case 'apisixPluginConfig': return 'ApisixPluginConfig'
    case 'gateway': return 'Gateway resource'
  }
}
