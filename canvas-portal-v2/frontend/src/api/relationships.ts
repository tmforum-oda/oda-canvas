// Client-side join: turn the four existing REST endpoints
// (components, exposedapis, dependentapis, gateway/resources)
// into a graph of {nodes, links}. No backend changes required.

import { useQuery } from '@tanstack/react-query'

import { fetchComponents, type OdaComponent } from './components'
import { fetchExposedApis, fetchGatewayResources, type ExposedAPI, type GatewayBinding, type GatewayDetails, type Policy } from './exposedApis'
import { fetchDependentApis, type DependentAPI } from './dependentApis'

import type { NodeType, RelationType } from '@/components/ApiRelationshipGraph/style'

export interface GraphNode {
  id: string
  nodeType: NodeType
  label: string
  sublabel?: string
  namespace?: string
  ready?: boolean
  url?: string
  raw: unknown
}

export interface GraphLink {
  source: string
  target: string
  relation: RelationType
}

export interface GraphPayload {
  nodes: GraphNode[]
  links: GraphLink[]
  namespaces: string[]
  canvasTypes: string[]
}

// --- node-id helpers (must be stable across renders) ---
const componentId       = (ns: string, name: string) => `component:${ns}/${name}`
const exposedApiId      = (ns: string, name: string) => `exposedApi:${ns}/${name}`
const dependentApiId    = (ns: string, name: string) => `dependentApi:${ns}/${name}`
const gatewayResourceId = (kind: string, ns: string, name: string) =>
  `${gatewayKindToType(kind)}:${ns}/${name}`
const policyId = (kind: string, ns: string, name: string, idx: number) =>
  `${policyKindToType(kind)}:${ns}/${name}#${idx}`

function gatewayKindToType(kind: string): NodeType {
  const k = (kind || '').toLowerCase()
  if (k === 'virtualservice') return 'virtualService'
  if (k === 'httproute') return 'httpRoute'
  if (k === 'apisixroute') return 'apisixRoute'
  if (k === 'kongingress' || k === 'ingress') return 'kongIngress'
  return 'gateway'
}

function policyKindToType(kind?: string): NodeType {
  const k = (kind || '').toLowerCase()
  if (k.includes('kong')) return 'kongPlugin'
  if (k.includes('apisix')) return 'apisixPluginConfig'
  return 'kongPlugin'
}

// Heuristic: does this ingress route's backendRefs target the istio-ingress
// gateway? The backendRefs are strings like "istio-ingress/istio-ingress:80"
// or "namespace/serviceName:port".
function ingressRefsTargetIstio(details?: GatewayDetails): boolean {
  const refs = details?.backendRefs ?? []
  return refs.some((r) => {
    if (typeof r !== 'string') return false
    const s = r.toLowerCase()
    return s.includes('istio-ingress') || s.includes('istiogateway')
  })
}

// Is this gateway resource an "ingress" route (north/south entry), as opposed
// to in-cluster service mesh (VirtualService)?
function isIngressKind(kind: string): boolean {
  const k = (kind || '').toLowerCase()
  return k === 'httproute' || k === 'apisixroute' || k === 'kongingress' || k === 'ingress'
}

function isMeshKind(kind: string): boolean {
  return (kind || '').toLowerCase() === 'virtualservice'
}

// Best-effort: find the owning Component for a given namespaced ExposedAPI.
// Strategy: prefer the explicit `oda.tmforum.org/componentName` label if the
// API client carried it through; otherwise fall back to a longest-prefix
// match against known Component names in the same namespace.
function findOwnerComponent(
  apiName: string,
  apiNamespace: string,
  components: OdaComponent[],
): OdaComponent | undefined {
  const sameNs = components.filter((c) => c.namespace === apiNamespace)
  return sameNs
    .filter((c) => apiName.startsWith(`${c.name}-`) || apiName === c.name)
    .sort((a, b) => b.name.length - a.name.length)[0]
}

export async function buildRelationshipGraph(): Promise<GraphPayload> {
  const [components, exposed, dependent, gateways] = await Promise.all([
    fetchComponents(),
    fetchExposedApis(),
    fetchDependentApis(),
    fetchGatewayResources(),
  ])

  const nodes = new Map<string, GraphNode>()
  const links: GraphLink[] = []
  const linkKeys = new Set<string>()
  const canvasTypeSet = new Set<string>()
  const namespaceSet = new Set<string>()
  const linkKey = (link: GraphLink) =>
    JSON.stringify([link.source, link.relation, link.target])
  const addLink = (link: GraphLink) => {
    const key = linkKey(link)
    if (linkKeys.has(key)) return
    linkKeys.add(key)
    links.push(link)
  }
  const removeLink = (link: GraphLink) => {
    const key = linkKey(link)
    if (!linkKeys.delete(key)) return
    const index = links.findIndex((existing) => linkKey(existing) === key)
    if (index >= 0) links.splice(index, 1)
  }

  // --- Components ---
  for (const c of components) {
    namespaceSet.add(c.namespace)
    nodes.set(componentId(c.namespace, c.name), {
      id: componentId(c.namespace, c.name),
      nodeType: 'component',
      label: c.name,
      sublabel: c.namespace,
      namespace: c.namespace,
      ready: (c.phase || '').toLowerCase().includes('complete'),
      raw: c,
    })
  }

  // --- ExposedAPIs + their gateway bindings + policies ---
  const exposedByUrl = new Map<string, ExposedAPI>()
  // Cache per-ExposedAPI ingress / mesh bindings so we can wire HTTPRoute -> VS
  // ("fronts") edges after the first pass.
  const ingressBindingsByApi = new Map<string, { gwId: string; details?: GatewayDetails }[]>()
  const meshBindingsByApi    = new Map<string, { gwId: string; details?: GatewayDetails }[]>()
  for (const ex of exposed) {
    if (!ex.name || !ex.namespace) continue
    namespaceSet.add(ex.namespace)
    if (ex.canvasType) canvasTypeSet.add(ex.canvasType)
    nodes.set(exposedApiId(ex.namespace, ex.name), {
      id: exposedApiId(ex.namespace, ex.name),
      nodeType: 'exposedApi',
      label: ex.name,
      sublabel: ex.apiType,
      namespace: ex.namespace,
      ready: ex.status === 'ready',
      url: ex.url,
      raw: ex,
    })
    if (ex.url) exposedByUrl.set(ex.url, ex)

    // ExposedAPI -> backedBy -> Component  (downward in new layout; the
    // API terminates at the backing component / pod).
    const owner = findOwnerComponent(ex.name, ex.namespace, components)
    if (owner) {
      addLink({
        source: exposedApiId(ex.namespace, ex.name),
        target: componentId(owner.namespace, owner.name),
        relation: 'backedBy',
      })
    }

    // ExposedAPI -> routedVia -> gateway resource (one per binding)
    for (const b of ex.gatewayResources ?? []) {
      if (!b.name || !b.namespace) continue
      const gwId = gatewayResourceId(b.kind, b.namespace, b.name)
      if (!nodes.has(gwId)) {
        if (b.canvasType) canvasTypeSet.add(b.canvasType)
        nodes.set(gwId, {
          id: gwId,
          nodeType: gatewayKindToType(b.kind),
          label: b.name,
          sublabel: b.kind,
          namespace: b.namespace,
          ready: true,
          raw: b,
        })
      }
      // Traffic flow direction: gateway routes traffic TO the ExposedAPI,
      // not the other way round. So gateway is the source.
      addLink({
        source: gwId,
        target: exposedApiId(ex.namespace, ex.name),
        relation: 'routesTo',
      })
      // remember which gateway resources are ingress vs mesh for this ExposedAPI
      // so we can wire HTTPRoute -> VirtualService chain edges below.
      const apiKey = exposedApiId(ex.namespace, ex.name)
      if (isIngressKind(b.kind)) {
        const list = ingressBindingsByApi.get(apiKey) ?? []
        list.push({ gwId, details: b.details })
        ingressBindingsByApi.set(apiKey, list)
      } else if (isMeshKind(b.kind)) {
        const list = meshBindingsByApi.get(apiKey) ?? []
        list.push({ gwId, details: b.details })
        meshBindingsByApi.set(apiKey, list)
      }
      // gateway -> policy edges
      ;(b.policies ?? []).forEach((p: Policy, i: number) => {
        if (!p) return
        const polNs = p.namespace ?? b.namespace ?? 'unknown'
        const polNm = p.name ?? `${b.name}-policy-${i}`
        const polId = policyId(b.kind, polNs, polNm, i)
        if (!nodes.has(polId)) {
          nodes.set(polId, {
            id: polId,
            nodeType: policyKindToType(b.kind),
            label: polNm,
            sublabel: p.pluginType,
            namespace: polNs,
            ready: p.enabled !== false,
            raw: p,
          })
        }
        addLink({ source: gwId, target: polId, relation: 'policy' })
      })
    }
  }

  // --- standalone gateway resources (some inventory may not have been linked
  //     via an ExposedAPI — still surface them for completeness) ---
  for (const b of gateways) {
    if (!b.name || !b.namespace) continue
    const gwId = gatewayResourceId(b.kind, b.namespace, b.name)
    if (!nodes.has(gwId)) {
      if (b.canvasType) canvasTypeSet.add(b.canvasType)
      nodes.set(gwId, {
        id: gwId,
        nodeType: gatewayKindToType(b.kind),
        label: b.name,
        sublabel: b.kind,
        namespace: b.namespace,
        ready: true,
        raw: b,
      })
    }
    if (b.relatedExposedApi?.name && b.relatedExposedApi.namespace) {
      // gateway -> routesTo -> ExposedAPI (traffic flow direction)
      addLink({
        source: gwId,
        target: exposedApiId(b.relatedExposedApi.namespace, b.relatedExposedApi.name),
        relation: 'routesTo',
      })
    }
  }

  // --- Ingress -> VirtualService "fronts" chain ---
  // If an ExposedAPI has both an ingress route (HTTPRoute/Apisix/Kong)
  // whose backendRefs target istio-ingress AND a sibling VirtualService,
  // draw a 'fronts' edge from the ingress to the VS. This matches the
  // actual traffic path: HTTPRoute -> istio-ingress -> VirtualService.
  for (const [apiKey, ingressList] of ingressBindingsByApi.entries()) {
    const meshList = meshBindingsByApi.get(apiKey)
    if (!meshList || meshList.length === 0) continue
    for (const ingress of ingressList) {
      if (!ingressRefsTargetIstio(ingress.details)) continue
      // A recognized ingress-to-mesh route is a chain, not a parallel direct
      // path to the ExposedAPI. Remove the shortcut added during binding load.
      removeLink({ source: ingress.gwId, target: apiKey, relation: 'routesTo' })
      for (const mesh of meshList) {
        addLink({ source: ingress.gwId, target: mesh.gwId, relation: 'fronts' })
      }
    }
  }

  // --- DependentAPIs + resolves-to edges ---
  for (const da of dependent) {
    if (!da.name || !da.namespace) continue
    namespaceSet.add(da.namespace)
    nodes.set(dependentApiId(da.namespace, da.name), {
      id: dependentApiId(da.namespace, da.name),
      nodeType: 'dependentApi',
      label: da.name,
      sublabel: da.apiType,
      namespace: da.namespace,
      ready: da.ready,
      url: da.resolvedUrl,
      raw: da,
    })
    // Component -> declares -> DependentAPI
    if (da.componentName) {
      const ownerNs = da.namespace // assume same ns
      const ownerId = componentId(ownerNs, da.componentName)
      // create a synthetic component node if it's not already known
      if (!nodes.has(ownerId)) {
        nodes.set(ownerId, {
          id: ownerId,
          nodeType: 'component',
          label: da.componentName,
          sublabel: ownerNs,
          namespace: ownerNs,
          raw: { name: da.componentName, namespace: ownerNs },
        })
      }
      addLink({ source: ownerId, target: dependentApiId(da.namespace, da.name), relation: 'declares' })
    }
    // DependentAPI -> resolvesTo -> ExposedAPI (cross-component)
    if (da.ready && da.resolvedUrl) {
      const target = exposedByUrl.get(da.resolvedUrl)
      if (target?.name && target.namespace) {
        addLink({
          source: dependentApiId(da.namespace, da.name),
          target: exposedApiId(target.namespace, target.name),
          relation: 'resolvesTo',
        })
      }
    }
  }

  return {
    nodes: Array.from(nodes.values()),
    links,
    namespaces: Array.from(namespaceSet).sort(),
    canvasTypes: Array.from(canvasTypeSet).sort(),
  }
}

export function useApiRelationshipGraph() {
  return useQuery({
    queryKey: ['api-relationship-graph'],
    queryFn: buildRelationshipGraph,
    refetchInterval: 15_000,
  })
}
