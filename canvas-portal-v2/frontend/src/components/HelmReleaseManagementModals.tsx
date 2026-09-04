import React, { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Input, Modal, Select, Spin, Table, Tooltip, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  DeleteOutlined,
  ExclamationCircleOutlined,
  HistoryOutlined,
  ReloadOutlined,
  SearchOutlined,
  SyncOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { listHelmReleases, uninstallHelmChart, type HelmRelease } from '@/api/helm'
import type { HelmInstallStep1Values } from '@/components/HelmInstallModal'
import StatusBadge from '@/components/StatusBadge'
import { queryClient } from '@/lib/queryClient'
import { colors } from '@/theme'

interface HelmReleaseModalProps {
  open: boolean
  onClose: () => void
  namespaceOptions: string[]
  defaultNamespace?: string
}

interface HelmUpgradePickerModalProps extends HelmReleaseModalProps {
  onSelect: (initialValues: Partial<HelmInstallStep1Values>) => void
  onViewHistory?: (release: string, namespace: string) => void
}

interface HelmBulkUninstallModalProps extends HelmReleaseModalProps {
  onCompleted?: () => void
}

type ReleaseKey = string

function releaseKey(release: HelmRelease): ReleaseKey {
  return `${release.namespace}:${release.name}`
}

function preferredNamespace(namespaceOptions: string[], defaultNamespace?: string): string {
  if (defaultNamespace && namespaceOptions.includes(defaultNamespace)) return defaultNamespace
  if (namespaceOptions.includes('components')) return 'components'
  return namespaceOptions[0] ?? 'components'
}

function parseChartReference(chart: string): { chartName: string; chartVersion: string } {
  const match = chart.match(/^(.+)-([0-9][0-9A-Za-z.+-]*)$/)
  if (!match) {
    return { chartName: chart, chartVersion: '' }
  }
  return {
    chartName: match[1],
    chartVersion: match[2],
  }
}

function extractErrorMessage(err: unknown, fallback: string): string {
  return (
    (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
    (err as { message?: string })?.message ??
    fallback
  )
}

function releaseMatchesSearch(release: HelmRelease, term: string): boolean {
  if (!term) return true
  const normalized = term.toLowerCase()
  return (
    release.name.toLowerCase().includes(normalized) ||
    release.namespace.toLowerCase().includes(normalized) ||
    release.chart.toLowerCase().includes(normalized) ||
    release.status.toLowerCase().includes(normalized)
  )
}

function releaseColumns(): ColumnsType<HelmRelease> {
  return [
    {
      title: 'Release',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name: string, record: HelmRelease) => (
        <div>
          <div style={{ fontWeight: 600, color: colors.textPrimary }}>{name}</div>
          <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace', marginTop: 2 }}>
            {record.namespace}
          </div>
        </div>
      ),
    },
    {
      title: 'Chart',
      dataIndex: 'chart',
      key: 'chart',
      render: (chart: string, record: HelmRelease) => {
        const parsed = parseChartReference(chart)
        return (
          <div>
            <div style={{ color: colors.textPrimary }}>{parsed.chartName || chart}</div>
            <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 2 }}>
              {parsed.chartVersion ? `chart ${parsed.chartVersion}` : chart}
              {record.app_version ? ` • app ${record.app_version}` : ''}
            </div>
          </div>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: string) => (
        <StatusBadge
          status={status}
          label={status.replace(/-/g, ' ')}
          size="sm"
        />
      ),
    },
    {
      title: 'Updated',
      dataIndex: 'updated',
      key: 'updated',
      width: 220,
      render: (updated?: string) =>
        updated ? (
          <Tooltip title={updated}>
            <span style={{ color: colors.textSecondary, fontSize: 12 }}>{updated}</span>
          </Tooltip>
        ) : (
          <span style={{ color: colors.textMuted }}>—</span>
        ),
    },
  ]
}

function ReleaseToolbar({
  namespace,
  namespaceOptions,
  onNamespaceChange,
  search,
  onSearchChange,
  onRefresh,
  loading,
}: {
  namespace: string
  namespaceOptions: string[]
  onNamespaceChange: (value: string) => void
  search: string
  onSearchChange: (value: string) => void
  onRefresh: () => void
  loading: boolean
}) {
  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
      <Select
        value={namespace}
        onChange={onNamespaceChange}
        style={{ width: 180 }}
        options={namespaceOptions.map((value) => ({ value, label: value }))}
      />
      <Input
        placeholder="Search releases..."
        prefix={<SearchOutlined style={{ color: colors.textMuted }} />}
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        allowClear
        style={{ flex: 1, minWidth: 220 }}
      />
      <Button
        icon={loading ? <SyncOutlined spin /> : <ReloadOutlined />}
        onClick={onRefresh}
        style={{
          background: 'transparent',
          border: `1px solid ${colors.border}`,
          color: colors.textSecondary,
        }}
      >
        Refresh
      </Button>
    </div>
  )
}

export function HelmUpgradePickerModal({
  open,
  onClose,
  onSelect,
  onViewHistory,
  namespaceOptions,
  defaultNamespace,
}: HelmUpgradePickerModalProps) {
  const [namespace, setNamespace] = useState(preferredNamespace(namespaceOptions, defaultNamespace))
  const [search, setSearch] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  useEffect(() => {
    if (!open) return
    setNamespace(preferredNamespace(namespaceOptions, defaultNamespace))
    setSearch('')
    setSelectedRowKeys([])
  }, [open, namespaceOptions, defaultNamespace])

  const {
    data: releases,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['helm-releases', namespace],
    queryFn: () => listHelmReleases(namespace),
    enabled: open && !!namespace,
  })

  const filteredReleases = useMemo(
    () => (releases ?? []).filter((release) => releaseMatchesSearch(release, search)),
    [releases, search],
  )

  const selectedRelease = useMemo(
    () => (releases ?? []).find((release) => releaseKey(release) === selectedRowKeys[0]),
    [releases, selectedRowKeys],
  )

  const handleChooseRelease = () => {
    if (!selectedRelease) return
    const { chartName, chartVersion } = parseChartReference(selectedRelease.chart)
    onSelect({
      source: 'repo',
      chart: chartName,
      version: chartVersion,
      repo_url: '',
      release_name: selectedRelease.name,
      namespace: selectedRelease.namespace,
    })
    onClose()
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={860}
      destroyOnClose
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: colors.textPrimary }}>
          <UploadOutlined style={{ color: colors.primary }} />
          Upgrade Deployed Component
        </div>
      }
      styles={{
        content: { background: colors.bgCard, padding: 0 },
        header: {
          background: colors.bgCard,
          borderBottom: `1px solid ${colors.border}`,
          padding: '14px 20px',
          margin: 0,
        },
        body: { padding: '20px 24px 24px' },
      }}
    >
      <Alert
        type="info"
        showIcon
        message="Pick the deployed release you want to upgrade"
        style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.primary}40` }}
      />

      <ReleaseToolbar
        namespace={namespace}
        namespaceOptions={namespaceOptions}
        onNamespaceChange={(value) => {
          setNamespace(value)
          setSearch('')
          setSelectedRowKeys([])
        }}
        search={search}
        onSearchChange={setSearch}
        onRefresh={() => refetch()}
        loading={isFetching}
      />

      {isError ? (
        <Alert
          type="error"
          message="Could not load deployed components"
          description={extractErrorMessage(error, 'Failed to load Helm releases')}
          style={{ marginBottom: 16 }}
        />
      ) : isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      ) : (
        <>
          <Table<HelmRelease>
            columns={releaseColumns()}
            dataSource={filteredReleases}
            rowKey={releaseKey}
            size="small"
            pagination={filteredReleases.length > 8 ? { pageSize: 8 } : false}
            rowSelection={{
              type: 'radio',
              selectedRowKeys,
              onChange: (keys) => setSelectedRowKeys(keys),
            }}
            locale={{
              emptyText: (
                <div style={{ color: colors.textMuted, padding: '10px 0' }}>
                  No deployed Helm releases found in <code>{namespace}</code>.
                </div>
              ),
            }}
            style={{ background: 'transparent' }}
            onRow={(record) => ({
              onClick: () => setSelectedRowKeys([releaseKey(record)]),
            })}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 16 }}>
            <div style={{ color: colors.textMuted, fontSize: 12 }}>
              {selectedRelease
                ? `Selected release: ${selectedRelease.name}`
                : 'Select one deployed release to continue.'}
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button
                onClick={onClose}
                style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
              >
                Cancel
              </Button>
              {onViewHistory && (
                <Button
                  icon={<HistoryOutlined />}
                  onClick={() => {
                    if (!selectedRelease) return
                    onViewHistory(selectedRelease.name, selectedRelease.namespace)
                    onClose()
                  }}
                  disabled={!selectedRelease}
                  style={{
                    background: 'transparent',
                    border: `1px solid ${colors.border}`,
                    color: colors.textSecondary,
                  }}
                >
                  View History
                </Button>
              )}
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={handleChooseRelease}
                disabled={!selectedRelease}
                style={{ background: colors.primary, border: 'none' }}
              >
                Configure Upgrade
              </Button>
            </div>
          </div>
        </>
      )}
    </Modal>
  )
}

export function HelmBulkUninstallModal({
  open,
  onClose,
  onCompleted,
  namespaceOptions,
  defaultNamespace,
}: HelmBulkUninstallModalProps) {
  const [namespace, setNamespace] = useState(preferredNamespace(namespaceOptions, defaultNamespace))
  const [search, setSearch] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [step, setStep] = useState<'select' | 'confirm'>('select')
  const [isRemoving, setIsRemoving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setNamespace(preferredNamespace(namespaceOptions, defaultNamespace))
    setSearch('')
    setSelectedRowKeys([])
    setStep('select')
    setActionError(null)
  }, [open, namespaceOptions, defaultNamespace])

  const {
    data: releases,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['helm-releases', namespace],
    queryFn: () => listHelmReleases(namespace),
    enabled: open && !!namespace,
  })

  const filteredReleases = useMemo(
    () => (releases ?? []).filter((release) => releaseMatchesSearch(release, search)),
    [releases, search],
  )

  const selectedReleases = useMemo(
    () => (releases ?? []).filter((release) => selectedRowKeys.includes(releaseKey(release))),
    [releases, selectedRowKeys],
  )

  const handleUninstallSelected = async () => {
    if (!selectedReleases.length) return
    setIsRemoving(true)
    setActionError(null)

    const results = await Promise.all(
      selectedReleases.map(async (release) => {
        try {
          await uninstallHelmChart({
            release_name: release.name,
            namespace: release.namespace,
          })
          return { ok: true as const, release }
        } catch (err: unknown) {
          return {
            ok: false as const,
            release,
            message: extractErrorMessage(err, `Failed to remove ${release.name}`),
          }
        }
      }),
    )

    const succeeded = results.filter((result) => result.ok)
    const failed = results.filter((result) => !result.ok)

    await queryClient.invalidateQueries({ queryKey: ['helm-releases'] })
    await refetch()

    if (succeeded.length > 0) {
      message.success(
        `${succeeded.length} component${succeeded.length === 1 ? '' : 's'} removed successfully`,
      )
      onCompleted?.()
    }

    if (failed.length === 0) {
      setIsRemoving(false)
      onClose()
      return
    }

    message.error(
      `${failed.length} uninstall${failed.length === 1 ? '' : 's'} failed. Review the errors and try again.`,
    )
    setSelectedRowKeys(failed.map((result) => releaseKey(result.release)))
    setActionError(
      failed.map((result) => `${result.release.name}: ${result.message}`).join('\n'),
    )
    setStep('confirm')
    setIsRemoving(false)
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={920}
      destroyOnClose
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: colors.textPrimary }}>
          <DeleteOutlined style={{ color: colors.statusDown }} />
          Uninstall Deployed Components
        </div>
      }
      styles={{
        content: { background: colors.bgCard, padding: 0 },
        header: {
          background: colors.bgCard,
          borderBottom: `1px solid ${colors.border}`,
          padding: '14px 20px',
          margin: 0,
        },
        body: { padding: '20px 24px 24px' },
      }}
    >
      {step === 'select' ? (
        <>
          <Alert
            type="warning"
            showIcon
            message="Select one or more deployed components to remove"
            style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.statusDeprecated}40` }}
          />

          <ReleaseToolbar
            namespace={namespace}
            namespaceOptions={namespaceOptions}
            onNamespaceChange={(value) => {
              setNamespace(value)
              setSearch('')
              setSelectedRowKeys([])
              setStep('select')
              setActionError(null)
            }}
            search={search}
            onSearchChange={setSearch}
            onRefresh={() => refetch()}
            loading={isFetching}
          />

          {isError ? (
            <Alert
              type="error"
              message="Could not load deployed components"
              description={extractErrorMessage(error, 'Failed to load Helm releases')}
              style={{ marginBottom: 16 }}
            />
          ) : isLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <Spin />
            </div>
          ) : (
            <>
              <Table<HelmRelease>
                columns={releaseColumns()}
                dataSource={filteredReleases}
                rowKey={releaseKey}
                size="small"
                pagination={filteredReleases.length > 8 ? { pageSize: 8 } : false}
                rowSelection={{
                  selectedRowKeys,
                  onChange: (keys) => setSelectedRowKeys(keys),
                  preserveSelectedRowKeys: true,
                }}
                locale={{
                  emptyText: (
                    <div style={{ color: colors.textMuted, padding: '10px 0' }}>
                      No deployed Helm releases found in <code>{namespace}</code>.
                    </div>
                  ),
                }}
                style={{ background: 'transparent' }}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 16 }}>
                <div style={{ color: colors.textMuted, fontSize: 12 }}>
                  {selectedReleases.length
                    ? `${selectedReleases.length} component${selectedReleases.length === 1 ? '' : 's'} selected for removal`
                    : 'Select at least one deployed component to continue.'}
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <Button
                    onClick={onClose}
                    style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
                  >
                    Cancel
                  </Button>
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => setStep('confirm')}
                    disabled={!selectedReleases.length}
                    style={{ border: 'none' }}
                  >
                    Review Removal
                  </Button>
                </div>
              </div>
            </>
          )}
        </>
      ) : (
        <>
          <Alert
            type="warning"
            showIcon
            icon={<ExclamationCircleOutlined />}
            message={`This will remove ${selectedReleases.length} deployed component${selectedReleases.length === 1 ? '' : 's'}`}
            description="Uninstalling a Helm release removes the release and the Kubernetes resources it manages. Pods, services, workloads, and related configuration created by these releases may be deleted."
            style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.statusDown}40` }}
          />

          {actionError && (
            <Alert
              type="error"
              message="Some uninstall actions failed"
              description={
                <pre style={{ margin: 0, fontSize: 11, whiteSpace: 'pre-wrap', maxHeight: 140, overflow: 'auto' }}>
                  {actionError}
                </pre>
              }
              style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.statusDown}40` }}
            />
          )}

          <div
            style={{
              border: `1px solid ${colors.border}`,
              borderRadius: 10,
              background: colors.surfaceSubtle,
              padding: 14,
              marginBottom: 18,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
              Releases To Remove
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {selectedReleases.map((release) => (
                <div
                  key={releaseKey(release)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    gap: 12,
                    padding: '10px 12px',
                    borderRadius: 8,
                    border: `1px solid ${colors.border}`,
                    background: colors.surfaceInset,
                  }}
                >
                  <div>
                    <div style={{ color: colors.textPrimary, fontWeight: 600 }}>{release.name}</div>
                    <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 3 }}>
                      {release.chart}
                    </div>
                    <div style={{ fontSize: 11, color: colors.textMuted, fontFamily: 'monospace', marginTop: 4 }}>
                      namespace: {release.namespace}
                    </div>
                  </div>
                  <StatusBadge status={release.status} label={release.status.replace(/-/g, ' ')} size="sm" />
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
            <Button
              onClick={() => setStep('select')}
              disabled={isRemoving}
              style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
            >
              Back
            </Button>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button
                onClick={onClose}
                disabled={isRemoving}
                style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
              >
                Cancel
              </Button>
              <Button
                danger
                icon={isRemoving ? <SyncOutlined spin /> : <DeleteOutlined />}
                onClick={handleUninstallSelected}
                disabled={isRemoving || !selectedReleases.length}
                style={{ border: 'none', minWidth: 160 }}
              >
                {isRemoving ? 'Removing…' : 'Uninstall Selected'}
              </Button>
            </div>
          </div>
        </>
      )}
    </Modal>
  )
}
