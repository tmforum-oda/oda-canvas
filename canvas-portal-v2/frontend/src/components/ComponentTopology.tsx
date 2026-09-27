import React, { useMemo } from 'react'
import { Tooltip } from 'antd'
import { RightOutlined } from '@ant-design/icons'
import type { OdaComponent } from '@/api/components'
import type { Operator } from '@/api/operators'
import {
  TMF_COMPONENT_CATALOG,
  TMF_OPERATOR_CATALOG,
  type TmfCatalogComponent,
  type TmfCatalogDomain,
  type TmfOperatorCatalogEntry,
} from '@/data/tmfComponentCatalog'
import { colors } from '@/theme'

interface ComponentTopologyProps {
  components: OdaComponent[]
  operators?: Operator[]
  onSelect: (component: OdaComponent) => void
  onSelectMany: (instances: OdaComponent[], label: string) => void
  letterFilter?: string
}

interface CatalogTile extends TmfCatalogComponent {
  domainKey: string
  domainTitle: string
  instances: OdaComponent[]
}

function normalizeText(value?: string): string {
  return (value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '')
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)))
}

function getComponentCandidates(component: OdaComponent): string[] {
  const name = component.name ?? ''
  const description = component.description ?? ''
  const labelValues = Object.values(component.labels ?? {})
  const annotationValues = Object.values(component.annotations ?? {})
  const candidates = [
    normalizeText(name),
    normalizeText(description),
    ...labelValues.map((value) => normalizeText(value)),
    ...annotationValues.map((value) => normalizeText(value)),
  ]

  const parts = name.split(/[^A-Za-z0-9]+/).filter(Boolean)
  if (parts.length > 1) {
    candidates.push(normalizeText(parts.slice(1).join('')))
    candidates.push(normalizeText(parts.slice(1).join('-')))
  }

  return uniqueStrings(candidates)
}

function getCatalogAliases(component: TmfCatalogComponent): string[] {
  return uniqueStrings([
    normalizeText(component.name),
    normalizeText(component.code),
    ...(component.aliases ?? []).map((alias) => normalizeText(alias)),
  ])
}

function getMatchScore(candidate: string, alias: string): number {
  if (!candidate || !alias) return 0
  if (candidate === alias) return 4000 + alias.length
  // Candidate contains the alias (catalog alias is shorter than the component name)
  if (candidate.endsWith(alias) || candidate.startsWith(alias)) return 3000 + alias.length
  if (candidate.includes(alias) && alias.length >= 8) return 2000 + alias.length
  // Reverse: alias contains the candidate (component is named with a shorter
  // form, e.g. "productrecommendation" vs alias "productrecommendationmanagement")
  if (candidate.length >= 10 && (alias.startsWith(candidate) || alias.endsWith(candidate))) {
    return 2500 + candidate.length
  }
  if (candidate.length >= 12 && alias.includes(candidate)) {
    return 1500 + candidate.length
  }
  return 0
}

function buildCatalogTiles(): CatalogTile[] {
  return TMF_COMPONENT_CATALOG.flatMap((domain) =>
    domain.components.map((component) => ({
      ...component,
      domainKey: domain.key,
      domainTitle: domain.title,
      instances: [],
    }))
  )
}

function matchCatalogTile(component: OdaComponent, tiles: CatalogTile[]): CatalogTile | null {
  const candidates = getComponentCandidates(component)
  let bestMatch: CatalogTile | null = null
  let bestScore = 0

  for (const tile of tiles) {
    for (const alias of getCatalogAliases(tile)) {
      for (const candidate of candidates) {
        const score = getMatchScore(candidate, alias)
        if (score > bestScore) {
          bestScore = score
          bestMatch = tile
        }
      }
    }
  }

  return bestMatch
}

function sortInstances(instances: OdaComponent[]): OdaComponent[] {
  return [...instances].sort((left, right) => {
    const leftCreated = left.createdAt ?? ''
    const rightCreated = right.createdAt ?? ''
    if (leftCreated !== rightCreated) return rightCreated.localeCompare(leftCreated)
    return left.name.localeCompare(right.name)
  })
}

function getPrimaryInstance(instances: OdaComponent[]): OdaComponent | undefined {
  return sortInstances(instances)[0]
}

// TM Forum-style domain colours used to fill the small hexagon badge on each
// tile. Each domain has its own solid colour so the row stays scannable at a
// glance, mirroring the public catalog at tmforum.org/oda/directory.
interface DomainPaint {
  hexFill: string
  hexBorder: string
  badgeBg: string
  badgeText: string
}

function getDomainPaint(domainKey: string): DomainPaint {
  switch (domainKey) {
    case 'party-management':
      return {
        hexFill: '#E4002B',
        hexBorder: '#B00021',
        badgeBg: '#FEE2E2',
        badgeText: '#7F1D1D',
      }
    case 'core-commerce-management':
      return {
        hexFill: '#F2A900',
        hexBorder: '#C68800',
        badgeBg: '#FEF3C7',
        badgeText: '#92400E',
      }
    case 'production':
      return {
        hexFill: '#005EB8',
        hexBorder: '#003C71',
        badgeBg: '#DBEAFE',
        badgeText: '#1E3A8A',
      }
    default:
      return {
        hexFill: '#6B7280',
        hexBorder: '#4B5563',
        badgeBg: '#F3F4F6',
        badgeText: '#374151',
      }
  }
}

const HEX_CLIP = 'polygon(25% 2%, 75% 2%, 100% 50%, 75% 98%, 25% 98%, 0 50%)'

function HexBadge({ paint, label }: { paint: DomainPaint; label: string }) {
  return (
    <div
      style={{
        position: 'relative',
        width: 46,
        height: 46,
        flexShrink: 0,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          clipPath: HEX_CLIP,
          background: paint.hexFill,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            color: '#fff',
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: 0.5,
          }}
        >
          {label}
        </span>
      </div>
    </div>
  )
}

function ComponentRow({
  tile,
  paint,
  onSelect,
  onSelectMany,
}: {
  tile: CatalogTile
  paint: DomainPaint
  onSelect: (component: OdaComponent) => void
  onSelectMany: (instances: OdaComponent[], label: string) => void
}) {
  const installed = tile.instances.length > 0
  const multiple = tile.instances.length > 1
  const primary = getPrimaryInstance(tile.instances)

  const installedBg = 'linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%)'
  const installedBorder = '#86EFAC'
  const idleBg = '#FFFFFF'
  const baseShadow = '0 1px 2px rgba(15,23,42,0.04)'
  const hoverShadow = '0 4px 12px rgba(15,23,42,0.08)'

  const tooltip = (
    <div style={{ minWidth: 220 }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: colors.textPrimary }}>{tile.name}</div>
      <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 4 }}>
        {tile.domainTitle}
      </div>
      {tile.code && (
        <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
          {tile.code}
        </div>
      )}
      <div style={{ marginTop: 8, fontSize: 12, color: installed ? colors.statusLive : colors.textMuted }}>
        {installed
          ? `${tile.instances.length} installed instance${tile.instances.length > 1 ? 's' : ''}`
          : 'Not installed'}
      </div>
      {installed && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: `1px solid ${colors.border}`, fontSize: 11, color: colors.primary, fontWeight: 600 }}>
          {multiple ? 'Click to choose an instance' : 'Click to view component details'}
        </div>
      )}
    </div>
  )

  return (
    <Tooltip
      title={tooltip}
      color="#FFFFFF"
      overlayStyle={{ maxWidth: 320 }}
      mouseEnterDelay={0.25}
    >
      <button
        type="button"
        aria-label={
          multiple
            ? `Choose an instance of ${tile.name}`
            : primary
              ? `Open ${primary.name}`
              : `TMF component ${tile.name}`
        }
        aria-disabled={!primary}
        onClick={() => {
          if (multiple) onSelectMany(sortInstances(tile.instances), tile.name)
          else if (primary) onSelect(primary)
        }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          width: '100%',
          padding: '12px 14px',
          borderRadius: 8,
          border: `1px solid ${installed ? installedBorder : colors.border}`,
          background: installed ? installedBg : idleBg,
          boxShadow: baseShadow,
          cursor: primary ? 'pointer' : 'default',
          textAlign: 'left',
          transition: 'transform 0.18s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.18s ease, border-color 0.15s ease',
          fontFamily: 'inherit',
        }}
        onMouseEnter={(e) => {
          if (!primary) return
          const n = e.currentTarget
          n.style.transform = 'translateY(-2px)'
          n.style.boxShadow = hoverShadow
          n.style.borderColor = colors.primary
        }}
        onMouseLeave={(e) => {
          const n = e.currentTarget
          n.style.transform = 'translateY(0)'
          n.style.boxShadow = baseShadow
          n.style.borderColor = installed ? installedBorder : colors.border
        }}
      >
        <HexBadge paint={paint} label="TMF" />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: colors.textPrimary,
              lineHeight: 1.3,
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {tile.name}
          </div>
          {tile.code && (
            <div style={{ marginTop: 4 }}>
              <span
                style={{
                  display: 'inline-block',
                  padding: '1px 6px',
                  borderRadius: 4,
                  background: paint.badgeBg,
                  color: paint.badgeText,
                  fontSize: 10,
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  letterSpacing: 0.3,
                }}
              >
                {tile.code}
              </span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {installed && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '2px 8px',
                borderRadius: 999,
                background: '#DCFCE7',
                border: `1px solid ${installedBorder}`,
                color: '#166534',
                fontSize: 10,
                fontWeight: 700,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: '#16A34A',
                  display: 'inline-block',
                }}
              />
              {tile.instances.length > 1 ? `x${tile.instances.length}` : 'Installed'}
            </span>
          )}
          <RightOutlined style={{ fontSize: 11, color: colors.textMuted }} />
        </div>
      </button>
    </Tooltip>
  )
}

function DomainCard({
  domain,
  tiles,
  onSelect,
  onSelectMany,
}: {
  domain: TmfCatalogDomain
  tiles: CatalogTile[]
  onSelect: (component: OdaComponent) => void
  onSelectMany: (instances: OdaComponent[], label: string) => void
}) {
  const paint = getDomainPaint(domain.key)
  const installedCount = tiles.filter((tile) => tile.instances.length > 0).length

  if (tiles.length === 0) return null

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: '20px 22px 22px',
        marginBottom: 20,
        boxShadow: '0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          marginBottom: 18,
          position: 'relative',
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: 16,
            fontWeight: 700,
            color: colors.textPrimary,
            letterSpacing: 0.3,
          }}
        >
          {domain.title}
        </h3>
        <span
          style={{
            position: 'absolute',
            right: 0,
            fontSize: 11,
            color: colors.textMuted,
            fontWeight: 600,
          }}
        >
          {installedCount}/{tiles.length} installed
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 12,
        }}
      >
        {tiles.map((tile) => (
          <ComponentRow
            key={`${tile.domainKey}-${tile.code || tile.name}`}
            tile={tile}
            paint={paint}
            onSelect={onSelect}
            onSelectMany={onSelectMany}
          />
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Operators row (catalog-only — read-only, does not affect component logic)
// ---------------------------------------------------------------------------

interface OperatorCatalogTile extends TmfOperatorCatalogEntry {
  installedCount: number
}

function buildOperatorTiles(operators: Operator[]): OperatorCatalogTile[] {
  // Lookup by canonical operator name (matches OPERATOR_SIGNATURES keys that
  // the backend uses when it assigns `operator.name`). Also try matching on
  // the backend-provided `tmfId` for entries whose code is set, so we still
  // light up when a cluster operator carries an `oda.tmforum.org/operatorId`
  // label without a known signature mapping.
  const cluster = operators ?? []
  const nameSet = new Set(cluster.map((operator) => operator.name))
  const tmfIdCounts = new Map<string, number>()
  for (const operator of cluster) {
    if (!operator.tmfId) continue
    tmfIdCounts.set(operator.tmfId, (tmfIdCounts.get(operator.tmfId) ?? 0) + 1)
  }

  return TMF_OPERATOR_CATALOG.map((entry) => {
    const sigMatches = (entry.signatureKeys ?? []).filter((key) => nameSet.has(key)).length
    const idMatches = entry.code ? tmfIdCounts.get(entry.code) ?? 0 : 0
    return { ...entry, installedCount: Math.max(sigMatches, idMatches) }
  })
}

// Distinct hexagon palette for operators — violet, separate from the four
// component domain colours so the row is visually flagged as a different
// catalog axis (operators vs functional-block components).
const OPERATOR_PAINT: DomainPaint = {
  hexFill: '#7C3AED',
  hexBorder: '#5B21B6',
  badgeBg: '#EDE9FE',
  badgeText: '#5B21B6',
}

function OperatorTile({ tile }: { tile: OperatorCatalogTile }) {
  const installed = tile.installedCount > 0
  const installedBg = 'linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%)'
  const installedBorder = '#86EFAC'
  const tooltipBody = (
    <div style={{ minWidth: 220 }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: colors.textPrimary }}>{tile.name}</div>
      <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 4 }}>
        Canvas Operator
      </div>
      {tile.code && (
        <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' }}>
          {tile.code}
        </div>
      )}
      <div style={{ marginTop: 8, fontSize: 12, color: installed ? colors.statusLive : colors.textMuted }}>
        {installed
          ? `${tile.installedCount} running deployment${tile.installedCount > 1 ? 's' : ''}`
          : 'Not installed'}
      </div>
    </div>
  )

  return (
    <Tooltip title={tooltipBody} color="#FFFFFF" overlayStyle={{ maxWidth: 320 }} mouseEnterDelay={0.25}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 14px',
          borderRadius: 8,
          border: `1px solid ${installed ? installedBorder : colors.border}`,
          background: installed ? installedBg : '#FFFFFF',
          boxShadow: '0 1px 2px rgba(15,23,42,0.04)',
        }}
      >
        <HexBadge paint={OPERATOR_PAINT} label="OPS" />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: colors.textPrimary,
              lineHeight: 1.3,
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {tile.name}
          </div>
          {tile.code && (
            <div style={{ marginTop: 4 }}>
              <span
                style={{
                  display: 'inline-block',
                  padding: '1px 6px',
                  borderRadius: 4,
                  background: OPERATOR_PAINT.badgeBg,
                  color: OPERATOR_PAINT.badgeText,
                  fontSize: 10,
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  letterSpacing: 0.3,
                }}
              >
                {tile.code}
              </span>
            </div>
          )}
        </div>

        {installed && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '2px 8px',
              borderRadius: 999,
              background: '#DCFCE7',
              border: `1px solid ${installedBorder}`,
              color: '#166534',
              fontSize: 10,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#16A34A', display: 'inline-block' }} />
            {tile.installedCount > 1 ? `x${tile.installedCount}` : 'Installed'}
          </span>
        )}
      </div>
    </Tooltip>
  )
}

function OperatorCatalogCard({ tiles }: { tiles: OperatorCatalogTile[] }) {
  if (tiles.length === 0) return null
  const installedCount = tiles.filter((tile) => tile.installedCount > 0).length

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: '20px 22px 22px',
        marginBottom: 20,
        boxShadow: '0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          marginBottom: 18,
          position: 'relative',
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: 16,
            fontWeight: 700,
            color: colors.textPrimary,
            letterSpacing: 0.3,
          }}
        >
          Canvas Operators
        </h3>
        <span
          style={{
            position: 'absolute',
            right: 0,
            fontSize: 11,
            color: colors.textMuted,
            fontWeight: 600,
          }}
        >
          {installedCount}/{tiles.length} installed
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 12,
        }}
      >
        {tiles.map((tile) => (
          <OperatorTile key={tile.code ?? tile.name} tile={tile} />
        ))}
      </div>
    </div>
  )
}

export default function ComponentTopology({ components, operators, onSelect, onSelectMany, letterFilter }: ComponentTopologyProps) {
  const { domains, unmatched } = useMemo(() => {
    const tiles = buildCatalogTiles()
    const unmatchedComponents: OdaComponent[] = []

    for (const component of components) {
      const match = matchCatalogTile(component, tiles)
      if (match) {
        match.instances.push(component)
      } else {
        unmatchedComponents.push(component)
      }
    }

    return {
      domains: TMF_COMPONENT_CATALOG.map((domain) => ({
        ...domain,
        tiles: tiles.filter((tile) => tile.domainKey === domain.key),
      })),
      unmatched: unmatchedComponents,
    }
  }, [components])

  const matchesLetter = (name: string) => {
    if (!letterFilter) return true
    if (letterFilter === '#') return /^[^a-zA-Z]/.test(name.trim())
    return name.trim().toUpperCase().startsWith(letterFilter.toUpperCase())
  }

  const filteredDomains = letterFilter
    ? domains.map((d) => ({ ...d, tiles: d.tiles.filter((t) => matchesLetter(t.name)) }))
    : domains

  const filteredUnmatched = letterFilter
    ? unmatched.filter((c) => matchesLetter(c.name))
    : unmatched

  const operatorTiles = useMemo(() => buildOperatorTiles(operators ?? []), [operators])

  return (
    <div>
      {filteredDomains.map((domain) => (
        <DomainCard
          key={domain.key}
          domain={domain}
          tiles={domain.tiles}
          onSelect={onSelect}
          onSelectMany={onSelectMany}
        />
      ))}

      {!letterFilter && <OperatorCatalogCard tiles={operatorTiles} />}

      {filteredUnmatched.length > 0 && (
        <OutsideCatalogCard
          components={sortInstances(filteredUnmatched)}
          onSelect={onSelect}
          onSelectMany={onSelectMany}
        />
      )}

    </div>
  )
}

// ---------------------------------------------------------------------------
// Outside TMF Catalog — same look as a DomainCard, no TMF code chip
// ---------------------------------------------------------------------------

const OUTSIDE_TMF_PAINT: DomainPaint = {
  hexFill: '#475569',
  hexBorder: '#1F2937',
  badgeBg: '#E2E8F0',
  badgeText: '#1E293B',
}

function OutsideCatalogCard({
  components,
  onSelect,
  onSelectMany,
}: {
  components: OdaComponent[]
  onSelect: (component: OdaComponent) => void
  onSelectMany: (instances: OdaComponent[], label: string) => void
}) {
  // Each unmatched component renders as its own tile (always 1 instance) so
  // it picks up the same hex badge, "Installed" pill, and click behaviour as
  // a regular TMF tile. The only intentional difference is the missing
  // `code`, which ComponentRow already hides conditionally.
  const tiles: CatalogTile[] = components.map((component) => ({
    name: component.name,
    domainKey: 'outside-tmf',
    domainTitle: 'Outside TMF Catalog',
    instances: [component],
  }))

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: '20px 22px 22px',
        marginBottom: 20,
        boxShadow: '0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.04)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          marginBottom: 18,
          position: 'relative',
        }}
      >
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: colors.textPrimary, letterSpacing: 0.3 }}>
          Outside TMF Catalog
        </h3>
        <span style={{ position: 'absolute', right: 0, fontSize: 11, color: colors.textMuted, fontWeight: 600 }}>
          {components.length} installed
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 12,
        }}
      >
        {tiles.map((tile) => (
          <ComponentRow
            key={`${tile.instances[0].namespace}/${tile.instances[0].name}`}
            tile={tile}
            paint={OUTSIDE_TMF_PAINT}
            onSelect={onSelect}
            onSelectMany={onSelectMany}
          />
        ))}
      </div>
    </div>
  )
}
