import React, { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Dropdown,
  Empty,
  Popconfirm,
  Progress,
  Segmented,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  AppstoreOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ClusterOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  DownloadOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  HistoryOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  CanvasConformanceRun,
  CanvasConformanceRunMode,
  deleteCanvasConformanceRun,
  downloadCanvasConformanceCucumberJson,
  downloadCanvasConformanceLog,
  downloadCanvasConformanceReportHtml,
  getCanvasConformanceCatalog,
  getCanvasConformanceConfig,
  getCanvasConformanceLogs,
  listCanvasConformanceRuns,
  startCanvasConformanceRun,
} from '@/api/conformance'
import { colors } from '@/theme'

function statusTag(run: CanvasConformanceRun) {
  if (run.status === 'succeeded') {
    return <Tag icon={<CheckCircleOutlined />} color="success">Succeeded</Tag>
  }
  if (run.status === 'failed') {
    return <Tag icon={<CloseCircleOutlined />} color="error">Failed</Tag>
  }
  if (run.status === 'running') {
    return <Tag icon={<SyncOutlined spin />} color="processing">Running</Tag>
  }
  if (run.status === 'queued') {
    return <Tag icon={<ClockCircleOutlined />} color="warning">Queued</Tag>
  }
  return <Tag>{run.status}</Tag>
}

function formatDate(value?: string | null) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '-'
}

function formatDuration(value?: number | null) {
  if (value === null || value === undefined) return '-'
  if (value < 60) return `${value.toFixed(1)}s`
  return `${Math.floor(value / 60)}m ${Math.round(value % 60)}s`
}

function ComingSoon({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div
      style={{
        background: colors.bgCard,
        border: `1px dashed ${colors.border}`,
        borderRadius: 8,
        padding: '48px 32px',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 8,
          background: colors.primarySurface,
          border: `1px solid ${colors.primaryBorder}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.primary,
          fontSize: 26,
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 17, fontWeight: 700, color: colors.textPrimary }}>
          {title}
        </div>
        <Tag
          style={{
            marginTop: 6,
            background: colors.statusDeprecatedBg,
            color: colors.statusDeprecated,
            border: `1px solid ${colors.statusDeprecated}30`,
            borderRadius: 999,
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          WORK IN PROGRESS
        </Tag>
      </div>
      <p
        style={{
          fontSize: 13,
          color: colors.textSecondary,
          maxWidth: 520,
          lineHeight: 1.6,
          margin: 0,
        }}
      >
        {description}
      </p>
    </div>
  )
}

function CanvasSuite() {
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<CanvasConformanceRunMode>('tags')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  const configQuery = useQuery({
    queryKey: ['canvas-conformance-config'],
    queryFn: getCanvasConformanceConfig,
  })

  const catalogQuery = useQuery({
    queryKey: ['canvas-conformance-catalog'],
    queryFn: () => getCanvasConformanceCatalog(false),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })

  const refreshCatalog = async () => {
    try {
      const fresh = await getCanvasConformanceCatalog(true)
      queryClient.setQueryData(['canvas-conformance-catalog'], fresh)
      message.success(`Catalog refreshed: ${fresh.features.length} feature files`)
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Unable to refresh catalog'
      message.error(detail)
    }
  }

  const runsQuery = useQuery({
    queryKey: ['canvas-conformance-runs'],
    queryFn: () => listCanvasConformanceRuns(30),
    refetchInterval: 5000,
  })

  const runs = runsQuery.data?.runs ?? []
  const activeRun = runsQuery.data?.active_run ?? null
  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? activeRun ?? runs[0],
    [activeRun, runs, selectedRunId],
  )
  const selectedRunActive = selectedRun?.status === 'queued' || selectedRun?.status === 'running'

  const logsQuery = useQuery({
    queryKey: ['canvas-conformance-logs', selectedRun?.id],
    queryFn: () => getCanvasConformanceLogs(selectedRun!.id, 800),
    enabled: Boolean(selectedRun?.id),
    refetchInterval: selectedRunActive ? 3000 : false,
  })

  useEffect(() => {
    if (!runs.length) return
    if (selectedRunId && runs.some((run) => run.id === selectedRunId)) return
    setSelectedRunId(activeRun?.id ?? runs[0].id)
  }, [activeRun?.id, runs, selectedRunId])

  const tagOptions = useMemo(() => {
    const catalog = catalogQuery.data
    if (!catalog) return [] as { label: string; value: string }[]
    return [...catalog.use_case_tags, ...catalog.feature_tags].map((tag) => ({
      label: tag,
      value: tag,
    }))
  }, [catalogQuery.data])

  const featureOptions = useMemo(() => {
    const catalog = catalogQuery.data
    if (!catalog) return [] as { label: string; value: string }[]
    return catalog.features.map((name) => ({ label: name, value: name }))
  }, [catalogQuery.data])

  const handleDownload = async (runId: string, kind: 'log' | 'json' | 'html') => {
    try {
      if (kind === 'log') await downloadCanvasConformanceLog(runId)
      else if (kind === 'json') await downloadCanvasConformanceCucumberJson(runId)
      else await downloadCanvasConformanceReportHtml(runId)
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Unable to download file'
      message.error(detail)
    }
  }

  const handleDeleteRun = async (runId: string) => {
    try {
      await deleteCanvasConformanceRun(runId)
      message.success(`Run ${runId} deleted`)
      if (selectedRunId === runId) {
        setSelectedRunId(null)
      }
      await queryClient.invalidateQueries({ queryKey: ['canvas-conformance-runs'] })
      await queryClient.invalidateQueries({ queryKey: ['canvas-conformance-logs', runId] })
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Unable to delete run'
      message.error(detail)
    }
  }

  const startRun = async () => {
    if (mode === 'tags' && selectedTags.length === 0) {
      message.error('Pick at least one tag to run')
      return
    }
    if (mode === 'features' && selectedFeatures.length === 0) {
      message.error('Pick at least one feature file to run')
      return
    }

    setStarting(true)
    try {
      const run = await startCanvasConformanceRun({
        mode,
        tags: mode === 'tags' ? selectedTags.join(' or ') : undefined,
        features: mode === 'features' ? selectedFeatures : undefined,
      })
      setSelectedRunId(run.id)
      message.success(`Canvas conformance run ${run.id} started`)
      await queryClient.invalidateQueries({ queryKey: ['canvas-conformance-runs'] })
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Unable to start conformance run'
      message.error(detail)
    } finally {
      setStarting(false)
    }
  }

  const columns: ColumnsType<CanvasConformanceRun> = [
    {
      title: 'Run',
      dataIndex: 'id',
      width: 130,
      render: (id: string, run) => (
        <Button type="link" size="small" onClick={() => setSelectedRunId(run.id)}>
          {id}
        </Button>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 130,
      render: (_: string, run) => statusTag(run),
    },
    {
      title: 'Suite',
      dataIndex: 'mode',
      width: 120,
      render: (value: CanvasConformanceRunMode) => value,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      width: 180,
      render: formatDate,
    },
    {
      title: 'Duration',
      dataIndex: 'duration_seconds',
      width: 110,
      render: formatDuration,
    },
    {
      title: 'Result',
      dataIndex: 'result',
      render: (_, run) => (
        <Space size={6} wrap>
          <Tag color="success">P {run.result.passed}</Tag>
          <Tag color="error">F {run.result.failed}</Tag>
          <Tag>S {run.result.skipped}</Tag>
          <Tag>Total {run.result.total}</Tag>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, run) => {
        const isActive = run.status === 'queued' || run.status === 'running'
        return (
          <Space size={4}>
            <Dropdown
              menu={{
                items: [
                  { key: 'log', label: 'Download log (.log)' },
                  { key: 'json', label: 'Download cucumber JSON' },
                  { key: 'html', label: 'Download HTML report' },
                ],
                onClick: ({ key }) => handleDownload(run.id, key as 'log' | 'json' | 'html'),
              }}
              trigger={['click']}
            >
              <Button type="text" size="small" icon={<DownloadOutlined />} title="Download artifacts" />
            </Dropdown>
            <Popconfirm
              title="Delete this run?"
              description="The run record, log file, and cucumber report will be permanently deleted."
              okText="Delete"
              okButtonProps={{ danger: true }}
              cancelText="Cancel"
              onConfirm={() => handleDeleteRun(run.id)}
              disabled={isActive}
            >
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={isActive}
                title={isActive ? 'Cannot delete a running run' : 'Delete run'}
              />
            </Popconfirm>
          </Space>
        )
      },
    },
  ]

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <Card
        title={
          <Space>
            <ClusterOutlined />
            Canvas Conformance Suite
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => runsQuery.refetch()} loading={runsQuery.isFetching}>
            Refresh
          </Button>
        }
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
            <Descriptions.Item label="Repo">
              {catalogQuery.data?.repo ?? configQuery.data?.repo_url ?? '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Branch">
              {catalogQuery.data?.branch ?? configQuery.data?.branch ?? '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Features path">
              {catalogQuery.data?.path ?? '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Keycloak realm">
              {configQuery.data?.keycloak_realm ?? '-'}
            </Descriptions.Item>
          </Descriptions>

          {catalogQuery.isError && (
            <Alert
              type="warning"
              showIcon
              message="Unable to load the feature catalog from GitHub"
              description={(catalogQuery.error as any)?.response?.data?.detail || (catalogQuery.error as any)?.message}
            />
          )}

          <Space wrap>
            <Segmented
              value={mode}
              onChange={(value) => setMode(value as CanvasConformanceRunMode)}
              options={[
                { label: 'Tags', value: 'tags' },
                { label: 'Feature files', value: 'features' },
              ]}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={refreshCatalog}
              loading={catalogQuery.isFetching}
            >
              Refresh catalog
            </Button>
          </Space>

          {mode === 'tags' && (
            <Select
              mode="multiple"
              allowClear
              showSearch
              value={selectedTags}
              onChange={(value) => setSelectedTags(value as string[])}
              options={tagOptions}
              loading={catalogQuery.isLoading}
              placeholder="Pick one or more tags (e.g. @UC002, @UC003-F001)"
              style={{ width: '100%' }}
            />
          )}

          {mode === 'features' && (
            <Select
              mode="multiple"
              allowClear
              showSearch
              value={selectedFeatures}
              onChange={(value) => setSelectedFeatures(value as string[])}
              options={featureOptions}
              loading={catalogQuery.isLoading}
              placeholder="Pick one or more feature files"
              style={{ width: '100%' }}
            />
          )}

          <Space wrap>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={startRun}
              loading={starting}
              disabled={Boolean(activeRun)}
            >
              Start run
            </Button>
            {activeRun && (
              <Typography.Text type="secondary">
                Run {activeRun.id} is {activeRun.phase}: {activeRun.message}
              </Typography.Text>
            )}
          </Space>
        </Space>
      </Card>

      {selectedRun ? (
        <Card
          title={
            <Space>
              <FileTextOutlined />
              Run {selectedRun.id}
            </Space>
          }
          extra={statusTag(selectedRun)}
        >
          <Space direction="vertical" size={14} style={{ width: '100%' }}>
            <Progress percent={selectedRun.progress} status={selectedRun.status === 'failed' ? 'exception' : undefined} />
            <Descriptions bordered size="small" column={{ xs: 1, md: 3 }}>
              <Descriptions.Item label="Phase">{selectedRun.phase}</Descriptions.Item>
              <Descriptions.Item label="Started">{formatDate(selectedRun.started_at)}</Descriptions.Item>
              <Descriptions.Item label="Finished">{formatDate(selectedRun.finished_at)}</Descriptions.Item>
              <Descriptions.Item label="Mode">{selectedRun.mode}</Descriptions.Item>
              <Descriptions.Item label="Branch">{selectedRun.branch}</Descriptions.Item>
              <Descriptions.Item label="Exit code">{selectedRun.exit_code ?? '-'}</Descriptions.Item>
            </Descriptions>
            <Typography.Text>{selectedRun.message}</Typography.Text>
            {selectedRun.features.length > 0 && (
              <Space size={6} wrap>
                {selectedRun.features.map((feature) => (
                  <Tag key={feature}>{feature}</Tag>
                ))}
              </Space>
            )}
            <div
              style={{
                background: colors.codeBg,
                color: colors.codeText,
                borderRadius: 8,
                minHeight: 220,
                maxHeight: 420,
                overflow: 'auto',
                padding: 14,
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                fontSize: 12,
                lineHeight: 1.55,
                whiteSpace: 'pre-wrap',
              }}
            >
              {(logsQuery.data ?? selectedRun.log_tail).join('\n') || 'Logs will appear after the run starts.'}
            </div>
          </Space>
        </Card>
      ) : (
        <Card>
          <Empty description="No conformance runs yet" />
        </Card>
      )}

      <Card
        title={
          <Space>
            <HistoryOutlined />
            Validation history
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={runs}
          loading={runsQuery.isLoading}
          size="small"
          pagination={{ pageSize: 8 }}
          onRow={(run) => ({
            onClick: () => setSelectedRunId(run.id),
          })}
        />
      </Card>
    </div>
  )
}

export default function BDDPage() {
  const [tab, setTab] = useState<'canvas' | 'components'>('canvas')

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 8,
            background: colors.primaryGradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
          }}
        >
          <ExperimentOutlined />
        </div>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
            BDD
          </h1>
        </div>
      </div>

      <Tabs
        activeKey={tab}
        onChange={(key) => setTab(key as 'canvas' | 'components')}
        items={[
          {
            key: 'canvas',
            label: (
              <span>
                <ClusterOutlined /> Canvas
              </span>
            ),
            children: <CanvasSuite />,
          },
          {
            key: 'components',
            label: (
              <span>
                <AppstoreOutlined /> Components
              </span>
            ),
            children: (
              <ComingSoon
                icon={<AppstoreOutlined />}
                title="Component Conformance Suite"
                description="Pick a deployed component and run its TMF functional-block scenarios. Results are stored per component."
              />
            ),
          },
        ]}
        tabBarStyle={{ marginBottom: 18 }}
      />
    </div>
  )
}
