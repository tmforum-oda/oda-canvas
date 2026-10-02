import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Tag } from 'antd'
import {
  AppstoreOutlined,
  DeleteOutlined,
  HistoryOutlined,
  ReloadOutlined,
  SyncOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { fetchComponents } from '@/api/components'
import HelmInstallModal, { type HelmInstallStep1Values } from '@/components/HelmInstallModal'
import {
  HelmBulkUninstallModal,
  HelmUpgradePickerModal,
} from '@/components/HelmReleaseManagementModals'
import HelmHistoryModal from '@/components/HelmHistoryModal'
import { colors } from '@/theme'

export default function ComponentsLifecyclePage() {
  const navigate = useNavigate()
  const [upgradePickerOpen, setUpgradePickerOpen] = useState(false)
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)
  const [uninstallModalOpen, setUninstallModalOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyRelease, setHistoryRelease] = useState<{ name: string; namespace: string } | null>(null)
  const [upgradeInitialValues, setUpgradeInitialValues] = useState<
    Partial<HelmInstallStep1Values> | undefined
  >(undefined)

  const { data: components, refetch } = useQuery({
    queryKey: ['components'],
    queryFn: fetchComponents,
  })

  const namespaces = Array.from(
    new Set((components ?? []).map((component) => component.namespace).filter(Boolean)),
  ).sort()
  const releaseNamespaces = Array.from(new Set(['components', ...namespaces].filter(Boolean))).sort()
  const defaultReleaseNamespace = releaseNamespaces.includes('components')
    ? 'components'
    : releaseNamespaces[0] ?? 'components'

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          marginBottom: 24,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: colors.primaryGradient,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              color: '#fff',
            }}
          >
            <SyncOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              Component Lifecycle Mgmt
            </h1>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Button
            icon={<AppstoreOutlined />}
            onClick={() => navigate('/components')}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          >
            Inventory
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => navigate('/components/deploy')}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
            }}
          >
            Deploy
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

      <div
        style={{
          display: 'flex',
          gap: 12,
          flexWrap: 'wrap',
          alignItems: 'center',
          padding: '14px 18px',
          marginBottom: 20,
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: colors.textMuted,
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            marginRight: 4,
          }}
        >
          Release actions
        </div>
        <Button
          icon={<UploadOutlined />}
          onClick={() => setUpgradePickerOpen(true)}
          style={{
            background: colors.infoSurface,
            border: `1px solid ${colors.primary}40`,
            color: colors.primary,
          }}
        >
          Upgrade
        </Button>
        <Button
          icon={<DeleteOutlined />}
          onClick={() => setUninstallModalOpen(true)}
          style={{
            background: 'rgba(239,68,68,0.12)',
            border: `1px solid ${colors.statusDown}40`,
            color: colors.statusDown,
          }}
        >
          Uninstall
        </Button>
        <Button
          icon={<HistoryOutlined />}
          onClick={() => setUpgradePickerOpen(true)}
          style={{
            background: 'rgba(99,102,241,0.08)',
            border: `1px solid ${colors.primary}30`,
            color: colors.textSecondary,
          }}
        >
          History
        </Button>
      </div>

      <Card
        style={{
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        bodyStyle={{ padding: '18px 20px' }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: colors.textMuted,
            textTransform: 'uppercase',
            letterSpacing: 1,
            marginBottom: 12,
          }}
        >
          Namespace Scope
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {releaseNamespaces.map((namespace) => (
            <Tag
              key={namespace}
              style={{
                background:
                  namespace === defaultReleaseNamespace ? colors.primarySurface : colors.surfaceMuted,
                color: namespace === defaultReleaseNamespace ? colors.primary : colors.textSecondary,
                border: `1px solid ${namespace === defaultReleaseNamespace ? `${colors.primary}40` : colors.border}`,
                borderRadius: 999,
                padding: '4px 10px',
                fontFamily: 'monospace',
              }}
            >
              {namespace}
            </Tag>
          ))}
        </div>
      </Card>

      <HelmUpgradePickerModal
        open={upgradePickerOpen}
        onClose={() => setUpgradePickerOpen(false)}
        onSelect={(initialValues) => {
          setUpgradeInitialValues(initialValues)
          setUpgradeModalOpen(true)
        }}
        onViewHistory={(name, namespace) => {
          setHistoryRelease({ name, namespace })
          setHistoryOpen(true)
        }}
        namespaceOptions={releaseNamespaces}
        defaultNamespace={defaultReleaseNamespace}
      />

      <HelmInstallModal
        open={upgradeModalOpen}
        onClose={() => {
          setUpgradeModalOpen(false)
          setUpgradeInitialValues(undefined)
        }}
        onInstalled={() => refetch()}
        defaultNamespace={defaultReleaseNamespace}
        mode="upgrade"
        initialValues={upgradeInitialValues}
      />

      <HelmBulkUninstallModal
        open={uninstallModalOpen}
        onClose={() => setUninstallModalOpen(false)}
        onCompleted={() => refetch()}
        namespaceOptions={releaseNamespaces}
        defaultNamespace={defaultReleaseNamespace}
      />

      {historyRelease && (
        <HelmHistoryModal
          open={historyOpen}
          onClose={() => {
            setHistoryOpen(false)
            setHistoryRelease(null)
          }}
          releaseName={historyRelease.name}
          namespace={historyRelease.namespace}
        />
      )}
    </div>
  )
}
