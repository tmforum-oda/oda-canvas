import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Input, Select, Button, Drawer, Grid } from 'antd'
import { SearchOutlined, AppstoreOutlined, ReloadOutlined, DeploymentUnitOutlined, SyncOutlined, CloseOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { fetchComponents, type OdaComponent } from '@/api/components'
import { fetchOperators } from '@/api/operators'
import ComponentTopology from '@/components/ComponentTopology'
import ComponentDetailBody from './ComponentDetailBody'
import StatusBadge from '@/components/StatusBadge'
import { colors } from '@/theme'

const ALPHABET = ['#', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')]

export default function ComponentsPage() {
  const navigate = useNavigate()
  const { namespace: paramNs, name: paramName } = useParams<{ namespace?: string; name?: string }>()
  const screens = Grid.useBreakpoint()
  const selected = paramNs && paramName ? { namespace: paramNs, name: paramName } : null

  // When a catalog tile has more than one installed instance, the click opens
  // the drawer in "picker" mode listing every instance instead of guessing one.
  const [picker, setPicker] = useState<{ label: string; instances: OdaComponent[] } | null>(null)

  function openComponent(namespace: string, name: string) {
    setPicker(null)
    navigate(`/components/${namespace}/${name}`)
  }

  function openInstancePicker(instances: OdaComponent[], label: string) {
    navigate('/components')
    setPicker({ label, instances })
  }

  function backToInstanceList() {
    // Keep the picker so the drawer falls back to the instance list.
    navigate('/components')
  }

  function closeDrawer() {
    setPicker(null)
    navigate('/components')
  }
  const [search, setSearch] = useState('')
  const [nsFilter, setNsFilter] = useState<string>('all')
  const [letterFilter, setLetterFilter] = useState<string>('')

  const { data: components, isLoading, isError, refetch } = useQuery({
    queryKey: ['components'],
    queryFn: fetchComponents,
  })

  // Operators are surfaced read-only on the catalog map (installed/not). The
  // component code below is intentionally unaffected by this query.
  const { data: operators } = useQuery({
    queryKey: ['operators'],
    queryFn: fetchOperators,
  })

  const namespaces = Array.from(new Set(components?.map((c) => c.namespace) ?? []))

  const filtered = (components ?? []).filter((c) => {
    const matchSearch =
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.namespace.toLowerCase().includes(search.toLowerCase())

    const matchNs = nsFilter === 'all' || c.namespace === nsFilter
    return matchSearch && matchNs
  })

  const topologyComponents = [...filtered].sort(
    (a, b) => a.namespace.localeCompare(b.namespace) || a.name.localeCompare(b.name)
  )

  return (
    <div>
      {/* Header */}
      <div
        className="portal-shell-card"
        style={{
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          padding: '22px 24px',
          marginBottom: 18,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 8,
                background: colors.primaryGradient,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                color: '#fff',
                flexShrink: 0,
              }}
            >
              <AppstoreOutlined />
            </div>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 760, color: colors.textPrimary, margin: 0 }}>
                Component Inventory
              </h1>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Button
              icon={<DeploymentUnitOutlined />}
              onClick={() => navigate('/components/deploy')}
              style={{
                background: colors.infoSurface,
                border: `1px solid ${colors.primary}40`,
                color: colors.primary,
              }}
            >
              Deploy
            </Button>
            <Button
              icon={<SyncOutlined />}
              onClick={() => navigate('/components/lifecycle')}
              style={{
                background: colors.infoSurface,
                border: `1px solid ${colors.primary}40`,
                color: colors.primary,
              }}
            >
              Lifecycle Mgmt
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20, flexWrap: 'wrap' }}>
          <Input
            placeholder="Search components..."
            prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 300 }}
          />
          <Select
            value={nsFilter}
            onChange={setNsFilter}
            style={{ width: 220 }}
            options={[
              { value: 'all', label: 'All Namespaces' },
              ...namespaces.map((ns) => ({ value: ns, label: ns })),
            ]}
          />
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              height: 32,
              padding: '0 10px',
              borderRadius: 8,
              background: colors.surfaceSubtle,
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            {filtered.length} matched
          </span>
        </div>
      </div>

      {/* A–Z filter strip */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 4,
          marginBottom: 20,
          padding: '8px 12px',
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {ALPHABET.map((letter) => {
          const active = letterFilter === letter
          return (
            <button
              key={letter}
              type="button"
              onClick={() => setLetterFilter(active ? '' : letter)}
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                border: `1px solid ${active ? colors.primary : colors.border}`,
                background: active ? colors.primary : 'transparent',
                color: active ? '#fff' : colors.textSecondary,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 0,
                transition: 'background 0.15s ease, color 0.15s ease, border-color 0.15s ease',
              }}
            >
              {letter}
            </button>
          )
        })}
        {letterFilter && (
          <button
            type="button"
            onClick={() => setLetterFilter('')}
            style={{
              marginLeft: 8,
              padding: '4px 10px',
              borderRadius: 999,
              border: `1px solid ${colors.border}`,
              background: 'transparent',
              color: colors.textMuted,
              fontSize: 11,
              cursor: 'pointer',
            }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Map header pill */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
          padding: '0 4px',
        }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: colors.textMuted,
            textTransform: 'uppercase',
            letterSpacing: 1,
          }}
        >
          Components Map
        </div>
        {!isLoading && !isError && (
          <span style={{ fontSize: 11, color: colors.textMuted }}>
            {filtered.length} component{filtered.length === 1 ? '' : 's'} matched
          </span>
        )}
      </div>

      {isError && (
        <div
          style={{
            padding: 16,
            color: colors.statusDown,
            background: colors.statusDownBg,
            border: `1px solid ${colors.statusDown}40`,
            borderRadius: 8,
          }}
        >
          Failed to load components. Please try again.
        </div>
      )}

      {isLoading && (
        <div style={{ padding: 40, textAlign: 'center', color: colors.textMuted }}>
          Loading components…
        </div>
      )}

      {!isLoading && !isError && (
        <ComponentTopology
          components={topologyComponents}
          operators={operators ?? []}
          letterFilter={letterFilter}
          onSelect={(component) => openComponent(component.namespace, component.name)}
          onSelectMany={(instances, label) => openInstancePicker(instances, label)}
        />
      )}

      <Drawer
        open={!!selected || !!picker}
        onClose={closeDrawer}
        placement="right"
        width={screens.lg ? '64%' : '100%'}
        destroyOnClose
        closeIcon={<CloseOutlined />}
        styles={{
          header: {
            background: colors.bgCard,
            borderBottom: `1px solid ${colors.border}`,
            padding: '14px 22px',
          },
          body: {
            background: colors.bgBase,
            padding: '22px 24px 32px',
          },
        }}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.6 }}>
              Component
            </span>
            <span style={{ color: colors.border }}>·</span>
            <span style={{ fontSize: 13, color: colors.textPrimary, fontWeight: 600 }}>
              {selected ? `${selected.namespace}/${selected.name}` : picker ? picker.label : ''}
            </span>
          </div>
        }
      >
        {selected ? (
          <>
            {picker && (
              <button
                type="button"
                onClick={backToInstanceList}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 16,
                  padding: '4px 10px',
                  borderRadius: 6,
                  border: `1px solid ${colors.border}`,
                  background: 'transparent',
                  color: colors.primary,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ‹ Back to {picker.instances.length} instances
              </button>
            )}
            <ComponentDetailBody
              namespace={selected.namespace}
              name={selected.name}
              onClose={closeDrawer}
            />
          </>
        ) : picker ? (
          <InstancePicker
            label={picker.label}
            instances={picker.instances}
            onPick={(instance) => openComponent(instance.namespace, instance.name)}
          />
        ) : null}
      </Drawer>
    </div>
  )
}

function InstancePicker({
  label,
  instances,
  onPick,
}: {
  label: string
  instances: OdaComponent[]
  onPick: (instance: OdaComponent) => void
}) {
  return (
    <div>
      <div style={{ fontSize: 13, color: colors.textSecondary, marginBottom: 16 }}>
        <strong style={{ color: colors.textPrimary }}>{instances.length}</strong> installed instances of{' '}
        <strong style={{ color: colors.textPrimary }}>{label}</strong>. Select one to view its details.
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {instances.map((instance) => (
          <button
            key={`${instance.namespace}/${instance.name}`}
            type="button"
            onClick={() => onPick(instance)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              width: '100%',
              padding: '14px 16px',
              borderRadius: 8,
              border: `1px solid ${colors.border}`,
              background: colors.bgCard,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = colors.primary
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(15,23,42,0.08)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = colors.border
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: colors.textPrimary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {instance.name}
              </div>
              <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 4 }}>
                <span style={{ fontFamily: 'monospace' }}>{instance.namespace}</span>
                {instance.version ? ` · v${instance.version}` : ''}
                {instance.createdAt ? ` · created ${new Date(instance.createdAt).toLocaleString()}` : ''}
              </div>
            </div>
            <div style={{ flexShrink: 0 }}>
              <StatusBadge status={instance.phase || instance.status || 'unknown'} dot size="sm" />
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
