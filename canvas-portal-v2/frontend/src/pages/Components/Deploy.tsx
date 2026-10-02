import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Input, Spin, Tag, message } from 'antd'
import {
  AppstoreOutlined,
  DeploymentUnitOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { fetchComponents } from '@/api/components'
import HelmInstallModal, { type HelmInstallStep1Values } from '@/components/HelmInstallModal'
import {
  addHelmRepository,
  deleteHelmRepository,
  listHelmRepositories,
  syncHelmRepository,
} from '@/api/helm'
import { colors } from '@/theme'

export default function ComponentsDeployPage() {
  const navigate = useNavigate()
  const [helmModalOpen, setHelmModalOpen] = useState(false)
  const [helmInitialValues, setHelmInitialValues] = useState<Partial<HelmInstallStep1Values>>()
  const [repoName, setRepoName] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [addingRepo, setAddingRepo] = useState(false)
  const [busyRepoName, setBusyRepoName] = useState<string | null>(null)

  const { data: components, isLoading, isError, refetch } = useQuery({
    queryKey: ['components'],
    queryFn: fetchComponents,
  })
  const {
    data: repositories,
    isLoading: loadingRepos,
    isError: reposError,
    refetch: refetchRepos,
  } = useQuery({
    queryKey: ['helm-repositories'],
    queryFn: listHelmRepositories,
  })

  const namespaces = Array.from(
    new Set((components ?? []).map((component) => component.namespace).filter(Boolean)),
  ).sort()
  const defaultNamespace = namespaces.includes('components') ? 'components' : namespaces[0] ?? 'components'
  const healthyCount = (components ?? []).filter((component) =>
    ['ready', 'running'].includes((component.status ?? '').toLowerCase()),
  ).length
  const readyRepos = (repositories ?? []).filter((repo) => repo.status === 'ready').length

  const openInstallModal = (initial?: Partial<HelmInstallStep1Values>) => {
    setHelmInitialValues(initial)
    setHelmModalOpen(true)
  }

  const handleAddRepository = async () => {
    setAddingRepo(true)
    try {
      await addHelmRepository({ name: repoName, url: repoUrl })
      message.success(`Repository "${repoName}" added and synced`)
      setRepoName('')
      setRepoUrl('')
      await refetchRepos()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
        ?? (err as { message?: string })?.message
        ?? 'Failed to add Helm repository'
      message.error(detail)
    } finally {
      setAddingRepo(false)
    }
  }

  const handleSyncRepository = async (name: string) => {
    setBusyRepoName(name)
    try {
      await syncHelmRepository(name)
      message.success(`Repository "${name}" synced`)
      await refetchRepos()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
        ?? (err as { message?: string })?.message
        ?? `Failed to sync ${name}`
      message.error(detail)
    } finally {
      setBusyRepoName(null)
    }
  }

  const handleDeleteRepository = async (name: string) => {
    setBusyRepoName(name)
    try {
      await deleteHelmRepository(name)
      message.success(`Repository "${name}" removed`)
      await refetchRepos()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
        ?? (err as { message?: string })?.message
        ?? `Failed to delete ${name}`
      message.error(detail)
    } finally {
      setBusyRepoName(null)
    }
  }

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
            <DeploymentUnitOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
              Deploy Components
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
            icon={<SyncOutlined />}
            onClick={() => navigate('/components/lifecycle')}
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
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

<div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
        {[
          { label: 'Discovered Components', value: components?.length ?? 0, color: colors.primary },
          { label: 'Healthy / Running', value: healthyCount, color: colors.statusLive },
          { label: 'Ready Repos', value: readyRepos, color: colors.textPrimary },
          { label: 'Default Namespace', value: defaultNamespace, color: colors.textPrimary },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 10,
              padding: '12px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flex: '1 1 180px',
            }}
          >
            <span style={{ fontSize: 24, fontWeight: 700, color: stat.color }}>{stat.value}</span>
            <span style={{ fontSize: 13, color: colors.textSecondary }}>{stat.label}</span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Card
          style={{
            flex: '1 1 420px',
            background: colors.bgCard,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          bodyStyle={{ padding: '22px 24px' }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: colors.textMuted,
              textTransform: 'uppercase',
              letterSpacing: 1,
              marginBottom: 10,
            }}
          >
            New Deployment
          </div>
          <h2 style={{ fontSize: 18, color: colors.textPrimary, margin: '0 0 10px' }}>
            Install a Helm chart into the canvas
          </h2>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 18 }}>
            {['Repository charts', 'Edit values before install'].map((item) => (
              <Tag
                key={item}
                style={{
                  background: colors.surfaceSelected,
                  color: colors.tmfText,
                  border: 'none',
                  borderRadius: 999,
                  padding: '4px 10px',
                }}
              >
                {item}
              </Tag>
            ))}
          </div>
          <Button
            type="primary"
            icon={<DeploymentUnitOutlined />}
            onClick={() => openInstallModal()}
            style={{ background: colors.primary, border: 'none' }}
          >
            Install Component
          </Button>
        </Card>

      </div>

      <div style={{ marginTop: 16 }}>
        <Card
          style={{
            background: colors.bgCard,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          bodyStyle={{ padding: '22px 24px' }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: colors.textMuted,
              textTransform: 'uppercase',
              letterSpacing: 1,
              marginBottom: 10,
            }}
          >
            Helm Repositories
          </div>
          <h2 style={{ fontSize: 18, color: colors.textPrimary, margin: '0 0 18px' }}>
            Add and sync chart sources
          </h2>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            <Input
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              placeholder="Repository name"
              style={{ flex: '1 1 180px', minWidth: 180 }}
            />
            <Input
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://example.github.io/charts"
              style={{ flex: '2 1 320px', minWidth: 260 }}
            />
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddRepository}
              disabled={!repoName.trim() || !repoUrl.trim()}
              loading={addingRepo}
              style={{ background: colors.primary, border: 'none' }}
            >
              Add Repo
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchRepos()}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            >
              Refresh
            </Button>
          </div>

          {reposError && (
            <Alert
              type="error"
              showIcon
              message="Could not load Helm repositories"
              style={{ marginBottom: 16 }}
            />
          )}

          {loadingRepos ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}>
              <Spin />
            </div>
          ) : (repositories ?? []).length === 0 ? (
            <div style={{ color: colors.textMuted, fontSize: 13 }}>
              No Helm repositories configured yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {(repositories ?? []).map((repo) => (
                <div
                  key={repo.name}
                  style={{
                    border: `1px solid ${colors.border}`,
                    borderRadius: 10,
                    padding: '14px 16px',
                    background: colors.surfaceSubtle,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ color: colors.textPrimary, fontWeight: 600 }}>{repo.name}</span>
                        <Tag
                          style={{
                            background: repo.status === 'ready' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                            color: repo.status === 'ready' ? colors.statusLive : colors.statusDown,
                            border: 'none',
                            borderRadius: 999,
                          }}
                        >
                          {repo.status}
                        </Tag>
                        <Tag
                          style={{
                            background: colors.hoverSurface,
                            color: colors.textSecondary,
                            border: 'none',
                            borderRadius: 999,
                          }}
                        >
                          {repo.chart_count} charts
                        </Tag>
                      </div>
                      <div style={{ color: colors.textMuted, fontSize: 12, marginTop: 6 }}>
                        <code>{repo.url}</code>
                      </div>
                      {repo.last_synced_at && (
                        <div style={{ color: colors.textMuted, fontSize: 11, marginTop: 6 }}>
                          Last synced: {repo.last_synced_at}
                        </div>
                      )}
                      {repo.error && (
                        <div style={{ color: colors.statusDown, fontSize: 12, marginTop: 6 }}>
                          {repo.error}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <Button
                        icon={<SyncOutlined />}
                        loading={busyRepoName === repo.name}
                        onClick={() => handleSyncRepository(repo.name)}
                        style={{
                          background: 'transparent',
                          border: `1px solid ${colors.border}`,
                          color: colors.textSecondary,
                        }}
                      >
                        Sync
                      </Button>
                      <Button
                        icon={<DeploymentUnitOutlined />}
                        disabled={repo.status !== 'ready'}
                        onClick={() =>
                          openInstallModal({
                            source: 'repo',
                            repo_name: repo.name,
                            repo_url: repo.url,
                          })
                        }
                        style={{
                          background: colors.infoSurface,
                          border: `1px solid ${colors.primary}40`,
                          color: colors.primary,
                        }}
                      >
                        Install From Repo
                      </Button>
                      <Button
                        icon={<DeleteOutlined />}
                        danger
                        disabled={busyRepoName === repo.name}
                        onClick={() => handleDeleteRepository(repo.name)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <HelmInstallModal
        open={helmModalOpen}
        onClose={() => {
          setHelmModalOpen(false)
          setHelmInitialValues(undefined)
        }}
        onInstalled={() => refetch()}
        defaultNamespace={defaultNamespace}
        mode="install"
        initialValues={helmInitialValues}
      />
    </div>
  )
}
