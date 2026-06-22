import React, { useEffect, useMemo, useState } from 'react'
import {
  Modal,
  Steps,
  Form,
  Input,
  InputNumber,
  Button,
  Radio,
  Alert,
  Spin,
  Select,
  Tooltip,
  message,
} from 'antd'
import { useQuery } from '@tanstack/react-query'
import {
  DeploymentUnitOutlined,
  EditOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  FolderOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons'
import {
  getChartValues,
  getReleaseValues,
  installHelmChart,
  listHelmRepositories,
  listHelmRepositoryCharts,
  listHelmReleases,
  type HelmRepositoryChart,
} from '@/api/helm'
import { fetchClusterOverview } from '@/api/cluster'
import { colors } from '@/theme'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ChartSource = 'repo' | 'local'

export interface HelmInstallStep1Values {
  source: ChartSource
  chart: string
  repo_name: string
  repo_url: string
  version: string
  release_name: string
  namespace: string
}

type Step1Values = HelmInstallStep1Values

type HelmActionMode = 'install' | 'upgrade'

interface HelmInstallModalProps {
  open: boolean
  onClose: () => void
  /** Called after a successful install so the parent can refresh its list */
  onInstalled?: () => void
  /** Pre-fill namespace from the currently viewed component/namespace */
  defaultNamespace?: string
  /** Install creates a new release flow, upgrade reuses the same editor for an existing release. */
  mode?: HelmActionMode
  /** Optional step-1 defaults, useful when upgrading an existing release. */
  initialValues?: Partial<HelmInstallStep1Values>
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const inputStyle: React.CSSProperties = {
  background: colors.surfaceMuted,
  border: `1px solid ${colors.border}`,
  color: colors.textPrimary,
  borderRadius: 6,
}

const labelStyle: React.CSSProperties = {
  color: colors.textSecondary,
  fontSize: 13,
}

const sectionTitle = (text: string) => (
  <div
    style={{
      fontSize: 11,
      fontWeight: 700,
      color: colors.textMuted,
      textTransform: 'uppercase',
      letterSpacing: 1,
      marginBottom: 12,
      marginTop: 4,
    }}
  >
    {text}
  </div>
)

// ---------------------------------------------------------------------------
// Step 1 — Chart Details
// ---------------------------------------------------------------------------

interface Step1Props {
  initialValues: Partial<Step1Values>
  onNext: (values: Step1Values) => void
  onCancel: () => void
  mode: HelmActionMode
}

function ChartDetailsStep({ initialValues, onNext, onCancel, mode }: Step1Props) {
  const [form] = Form.useForm<Step1Values>()
  const [source, setSource] = useState<ChartSource>(initialValues.source ?? 'repo')
  const selectedRepoName = Form.useWatch('repo_name', form)
  const selectedChartName = Form.useWatch('chart', form)
  const selectedNamespace = Form.useWatch('namespace', form)
  const actionLabel = mode === 'upgrade' ? 'Upgrade' : 'Install'

  // Existing releases in the target namespace, used to validate release-name
  // uniqueness in install mode. We refetch when the namespace changes; the
  // result is cached for 30s so typing the name doesn't re-trigger requests.
  const {
    data: existingReleases,
    isFetching: loadingReleases,
  } = useQuery({
    queryKey: ['helm-releases', selectedNamespace],
    queryFn: () => listHelmReleases(selectedNamespace || undefined),
    enabled: mode === 'install' && !!selectedNamespace,
    staleTime: 30_000,
  })

  const existingReleaseNames = useMemo(
    () => new Set((existingReleases ?? []).map((rel) => rel.name)),
    [existingReleases],
  )

  const {
    data: repositories,
    isLoading: loadingRepos,
    isError: reposError,
    refetch: refetchRepos,
  } = useQuery({
    queryKey: ['helm-repositories'],
    queryFn: listHelmRepositories,
    enabled: source === 'repo',
  })

  const {
    data: repoCharts,
    isLoading: loadingCharts,
    isError: chartsError,
    refetch: refetchCharts,
  } = useQuery({
    queryKey: ['helm-repository-charts', selectedRepoName],
    queryFn: () => listHelmRepositoryCharts(selectedRepoName),
    enabled: source === 'repo' && !!selectedRepoName,
  })

  // Namespaces the install dialog is allowed to target. Sourced from the
  // backend's `installNamespaces` field, which mirrors
  // rbac.canvasInstallAccess.targetNamespaces in values.yaml — i.e. only the
  // namespaces where a RoleBinding actually exists for the backend SA.
  // Picking any other namespace would fail at helm-install time with a
  // "secrets is forbidden" RBAC error, so we don't even let the user try.
  const { data: clusterOverview } = useQuery({
    queryKey: ['cluster-overview-namespaces'],
    queryFn: fetchClusterOverview,
  })

  const namespaceOptions = useMemo(() => {
    const names = new Set<string>(clusterOverview?.installNamespaces ?? [])
    // Keep the currently selected namespace selectable (e.g. an upgrade
    // target whose RBAC binding existed in a previous release of the portal
    // chart but was later removed from values.yaml).
    if (selectedNamespace) names.add(selectedNamespace)
    return Array.from(names).sort((a, b) => {
      if (a === 'components') return -1
      if (b === 'components') return 1
      return a.localeCompare(b)
    })
  }, [clusterOverview, selectedNamespace])

  const selectedRepository = useMemo(
    () => (repositories ?? []).find((repo) => repo.name === selectedRepoName),
    [repositories, selectedRepoName],
  )

  const selectedChart = useMemo<HelmRepositoryChart | undefined>(
    () => (repoCharts ?? []).find((chart) => chart.name === selectedChartName),
    [repoCharts, selectedChartName],
  )

  useEffect(() => {
    if (source !== 'repo') return
    if (!selectedRepoName) return
    form.setFieldsValue({
      repo_url: selectedRepository?.url ?? '',
    })
  }, [form, selectedRepoName, selectedRepository, source])

  // Re-validate release_name when the cached release list for the selected
  // namespace updates or the namespace itself changes, so the uniqueness error
  // appears/clears without the user retyping.
  useEffect(() => {
    if (mode !== 'install') return
    if (!form.getFieldValue('release_name')) return
    form.validateFields(['release_name']).catch(() => {/* inline error shown */})
  }, [form, mode, selectedNamespace, existingReleaseNames])

  useEffect(() => {
    if (source !== 'repo') return
    if (!selectedChart) {
      if (form.getFieldValue('version')) {
        form.setFieldValue('version', '')
      }
      return
    }
    const currentVersion = form.getFieldValue('version')
    const availableVersions = new Set(selectedChart.versions.map((entry) => entry.version))
    if (currentVersion && !availableVersions.has(currentVersion)) {
      form.setFieldValue('version', '')
    }
  }, [form, selectedChart, source])

  const handleNext = () => {
    form
      .validateFields()
      .then((vals) => {
        const normalized: Step1Values = {
          ...vals,
          source,
          repo_url: source === 'repo' ? selectedRepository?.url ?? vals.repo_url ?? '' : vals.repo_url ?? '',
          repo_name: source === 'repo' ? vals.repo_name : '',
          version: vals.version ?? '',
        }
        onNext(normalized)
      })
      .catch(() => {/* antd shows inline errors */})
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        source: 'repo',
        namespace: initialValues.namespace ?? 'components',
        repo_name: '',
        repo_url: '',
        version: '',
        chart: '',
        release_name: '',
        ...initialValues,
      }}
      requiredMark={false}
    >
      {mode === 'upgrade' && (
        <Alert
          type="info"
          showIcon
          message="Review the chart source before upgrading"
          description="The release name and namespace are prefilled from the selected deployed component. Confirm the chart reference, version, and repo URL before continuing."
          style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.primary}40` }}
        />
      )}

      {/* Chart source toggle */}
      <div style={{ marginBottom: 20 }}>
        {sectionTitle('Chart Source')}
        <Radio.Group
          value={source}
          onChange={(e) => setSource(e.target.value)}
          style={{ display: 'flex', gap: 10 }}
        >
          {(
            [
              { value: 'repo', icon: <CloudDownloadOutlined />, label: 'Helm Repository', desc: 'Install from a remote chart repo URL' },
            ] as const
          ).map((opt) => (
            <label
              key={opt.value}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                padding: '12px 14px',
                borderRadius: 8,
                border: `1px solid ${source === opt.value ? colors.primary : colors.border}`,
                background: source === opt.value ? colors.primarySurface : colors.surfaceSubtle,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <Radio value={opt.value} style={{ marginTop: 2 }} />
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: source === opt.value ? colors.primary : colors.textPrimary, fontWeight: 600, fontSize: 13 }}>
                  {opt.icon} {opt.label}
                </div>
                <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 2 }}>{opt.desc}</div>
              </div>
            </label>
          ))}
        </Radio.Group>
      </div>

      {/* Repo fields */}
      {source === 'repo' && (
        <>
          {sectionTitle('Chart Details')}
          <Form.Item
            name="repo_name"
            label={<span style={labelStyle}>Repository</span>}
            rules={[{ required: true, message: 'Select a repository' }]}
          >
            <Select
              showSearch
              loading={loadingRepos}
              placeholder={loadingRepos ? 'Loading repositories…' : 'Select a synced Helm repository'}
              optionFilterProp="label"
              style={{ width: '100%' }}
              options={(repositories ?? []).map((repo) => ({
                value: repo.name,
                label: `${repo.name} (${repo.chart_count} charts)`,
                disabled: repo.status !== 'ready',
              }))}
              onChange={() => {
                form.setFieldsValue({ chart: '', version: '' })
              }}
            />
          </Form.Item>
          {reposError && (
            <Alert
              type="error"
              showIcon
              message="Could not load Helm repositories"
              description="Add or sync repositories from the Deploy page, then reopen this install flow."
              action={
                <Button size="small" onClick={() => refetchRepos()}>
                  Retry
                </Button>
              }
              style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.statusDown}40` }}
            />
          )}
          {!loadingRepos && !reposError && (repositories ?? []).length === 0 && (
            <Alert
              type="warning"
              showIcon
              message="No Helm repositories configured"
              description="Add and sync at least one repository on the Deploy page before installing from a remote chart."
              style={{ marginBottom: 16, background: 'transparent', border: `1px solid rgba(245,158,11,0.35)` }}
            />
          )}
          {selectedRepository && (
            <div style={{ marginBottom: 12, fontSize: 12, color: colors.textMuted }}>
              Repo URL: <code>{selectedRepository.url}</code>
            </div>
          )}
          <Form.Item
            name="chart"
            label={<span style={labelStyle}>Chart</span>}
            rules={[{ required: true, message: 'Select a chart' }]}
          >
            <Select
              showSearch
              disabled={!selectedRepoName}
              loading={loadingCharts}
              placeholder={!selectedRepoName ? 'Select a repository first' : loadingCharts ? 'Loading charts…' : 'Select a chart'}
              optionFilterProp="label"
              style={{ width: '100%' }}
              options={(repoCharts ?? []).map((chart) => ({
                value: chart.name,
                label: chart.description ? `${chart.name} — ${chart.description}` : chart.name,
              }))}
              onChange={() => {
                form.setFieldValue('version', '')
              }}
            />
          </Form.Item>
          {selectedRepoName && chartsError && (
            <Alert
              type="error"
              showIcon
              message="Could not load charts for the selected repository"
              action={
                <Button size="small" onClick={() => refetchCharts()}>
                  Retry
                </Button>
              }
              style={{ marginBottom: 16, background: 'transparent', border: `1px solid ${colors.statusDown}40` }}
            />
          )}
          <Form.Item
            name="version"
            label={<span style={labelStyle}>Chart Version <span style={{ color: colors.textMuted }}>(optional)</span></span>}
          >
            <Select
              allowClear
              showSearch
              disabled={!selectedChart}
              placeholder={!selectedChart ? 'Select a chart first' : 'Leave blank for latest synced version'}
              optionFilterProp="label"
              style={{ width: '100%' }}
              options={(selectedChart?.versions ?? []).map((entry) => ({
                value: entry.version,
                label: entry.app_version ? `${entry.version} (app ${entry.app_version})` : entry.version,
              }))}
            />
          </Form.Item>
        </>
      )}

      {sectionTitle('Release Info')}
      <Form.Item
        name="release_name"
        label={
          <span style={labelStyle}>
            Release Name{mode === 'upgrade' && <span style={{ color: colors.textMuted, marginLeft: 6, fontSize: 11 }}>(locked — identifies existing release)</span>}
            {mode === 'install' && loadingReleases && (
              <span style={{ color: colors.textMuted, marginLeft: 6, fontSize: 11 }}>
                <SyncOutlined spin /> checking namespace…
              </span>
            )}
          </span>
        }
        validateTrigger={['onChange', 'onBlur']}
        rules={[
          { required: true, message: 'Release name is required' },
          {
            pattern: /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/,
            message: 'Use lowercase letters, digits, or hyphens (must start/end alphanumeric).',
          },
          {
            validator: (_, value: string) => {
              if (mode !== 'install') return Promise.resolve()
              if (!value || !selectedNamespace) return Promise.resolve()
              if (existingReleaseNames.has(value)) {
                return Promise.reject(
                  new Error(
                    `Release "${value}" already exists in namespace "${selectedNamespace}". Pick a unique name or use the Upgrade flow.`,
                  ),
                )
              }
              return Promise.resolve()
            },
          },
        ]}
      >
        <Input
          placeholder="e.g. my-productcatalog"
          style={mode === 'upgrade' ? { ...inputStyle, opacity: 0.6, cursor: 'not-allowed' } : inputStyle}
          disabled={mode === 'upgrade'}
        />
      </Form.Item>
      <Form.Item
        name="namespace"
        label={
          <span style={labelStyle}>
            Namespace{mode === 'upgrade' && <span style={{ color: colors.textMuted, marginLeft: 6, fontSize: 11 }}>(locked)</span>}
          </span>
        }
        rules={[{ required: true, message: 'Namespace is required' }]}
      >
        <Select
          showSearch
          disabled={mode === 'upgrade'}
          placeholder="Select a namespace"
          optionFilterProp="label"
          style={{ width: '100%' }}
          options={namespaceOptions.map((ns) => ({ value: ns, label: ns }))}
        />
      </Form.Item>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
        <Button
          onClick={onCancel}
          style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
        >
          Cancel
        </Button>
        <Button
          type="primary"
          onClick={handleNext}
          style={{ background: colors.primary, border: 'none' }}
        >
          {`Next: Edit Values & ${actionLabel} →`}
        </Button>
      </div>
    </Form>
  )
}

// ---------------------------------------------------------------------------
// Step 2 — Edit Values
// ---------------------------------------------------------------------------

interface Step2Props {
  step1: Step1Values
  onBack: () => void
  onInstalled: () => void
  onCancel: () => void
  mode: HelmActionMode
  installing: boolean
  setInstalling: (v: boolean) => void
}

function EditValuesStep({ step1, onBack, onInstalled, onCancel, mode, installing, setInstalling }: Step2Props) {
  const [valuesYaml, setValuesYaml] = useState<string>('')
  const [fetchingValues, setFetchingValues] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [timeoutMinutes, setTimeoutMinutes] = useState<number>(5)
  // For upgrade: track whether the editor currently holds the deployed values
  // (so we can show the "existing deployed values loaded" banner and switch
  // the Default-values CTA to an explicit overwrite confirmation).
  const [deployedValuesLoaded, setDeployedValuesLoaded] = useState(false)
  const [loadingDeployed, setLoadingDeployed] = useState(mode === 'upgrade')
  const actionLabel = mode === 'upgrade' ? 'Upgrade' : 'Install'

  // ------------------------------------------------------------------
  // On upgrade mount: auto-fetch the release's currently deployed values
  // (helm get values <release> -n <ns>). Falls through silently to an
  // empty editor if helm has no user values for this release yet.
  // ------------------------------------------------------------------
  useEffect(() => {
    if (mode !== 'upgrade') return
    let cancelled = false
    setLoadingDeployed(true)
    setFetchError(null)
    getReleaseValues(step1.release_name, step1.namespace)
      .then((yaml) => {
        if (cancelled) return
        setValuesYaml(yaml || '')
        setDeployedValuesLoaded(Boolean(yaml && yaml.trim()))
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
          ?? (err as { message?: string })?.message
          ?? 'Failed to load deployed values'
        setFetchError(msg)
        setDeployedValuesLoaded(false)
      })
      .finally(() => {
        if (!cancelled) setLoadingDeployed(false)
      })
    return () => {
      cancelled = true
    }
  }, [mode, step1.release_name, step1.namespace])

  // ------------------------------------------------------------------
  // Fetch default values.yaml from the chart
  // ------------------------------------------------------------------
  const handleFetchValues = async () => {
    setFetchingValues(true)
    setFetchError(null)
    try {
      const yaml = await getChartValues({
        chart: step1.chart || undefined,
        repo_url: step1.repo_url || undefined,
        version: step1.version || undefined,
      })
      setValuesYaml(yaml)
      setDeployedValuesLoaded(false)
      message.success(mode === 'upgrade'
        ? 'Overwritten with chart defaults — edit as needed'
        : 'Default values loaded — edit as needed')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? 'Failed to fetch values'
      setFetchError(msg)
    } finally {
      setFetchingValues(false)
    }
  }

  // ------------------------------------------------------------------
  // Install
  // ------------------------------------------------------------------
  const handleInstall = async () => {
    setInstalling(true)
    try {
      await installHelmChart({
        release_name: step1.release_name,
        chart: step1.chart,
        namespace: step1.namespace,
        repo_name: step1.repo_name || undefined,
        version: step1.version || undefined,
        repo_url: step1.repo_url || undefined,
        values_yaml: valuesYaml || undefined,
        timeout_minutes: timeoutMinutes,
      })
      message.success(`Release "${step1.release_name}" ${mode === 'upgrade' ? 'upgraded' : 'installed'} successfully`)
      onInstalled()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? `${actionLabel} failed`
      message.error(detail)
    } finally {
      setInstalling(false)
    }
  }

  return (
    <div>
      {/* Summary row */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 8,
          marginBottom: 16,
          padding: '10px 14px',
          background: colors.surfaceSubtle,
          borderRadius: 8,
          border: `1px solid ${colors.border}`,
          fontSize: 12,
          color: colors.textSecondary,
        }}
      >
        {[
          ['Chart', step1.chart],
          ['Release', step1.release_name],
          ['Namespace', step1.namespace],
          ...(step1.repo_name ? [['Repo', step1.repo_name]] : []),
          ...(step1.version ? [['Version', step1.version]] : []),
          ...(step1.repo_url ? [['Repo URL', step1.repo_url]] : []),
        ].map(([k, v]) => (
          <span key={k} style={{ display: 'flex', gap: 4 }}>
            <span style={{ color: colors.textMuted }}>{k}:</span>
            <span style={{ fontFamily: 'monospace', color: colors.textPrimary }}>{v}</span>
          </span>
        ))}
      </div>

      {/* Upgrade-only: tell the user that the editor is preloaded with the
          release's currently deployed values (and how to start from defaults). */}
      {mode === 'upgrade' && (loadingDeployed || deployedValuesLoaded) && (
        <Alert
          type="info"
          showIcon
          message={
            loadingDeployed
              ? 'Loading currently deployed values…'
              : 'Existing deployed values loaded. Edit, or overwrite with chart defaults.'
          }
          style={{ marginBottom: 10 }}
        />
      )}

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Fetch default values — available for both repo and local. In upgrade
            mode the editor is already preloaded with deployed values, so this
            becomes an explicit "overwrite with defaults" action. */}
        <Tooltip
          title={
            mode === 'upgrade'
              ? 'Replaces the deployed values currently in the editor with the chart’s default values. Useful for resetting.'
              : 'Runs helm show values to load the chart defaults'
          }
        >
          <Button
            icon={fetchingValues ? <SyncOutlined spin /> : <CloudDownloadOutlined />}
            onClick={handleFetchValues}
            disabled={fetchingValues || installing}
            style={{ background: colors.infoSurface, border: `1px solid ${colors.primary}40`, color: colors.primary }}
          >
            {fetchingValues
              ? 'Fetching…'
              : mode === 'upgrade'
                ? 'Click here to overwrite with default values'
                : 'Load Default Values'}
          </Button>
        </Tooltip>

        {/* Helm install timeout (minutes) */}
        <Tooltip title="Passes --timeout to helm. Increase for slow charts; the backend allows 1–60 minutes.">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '0 10px',
              height: 32,
              borderRadius: 6,
              border: `1px solid ${colors.border}`,
              background: colors.surfaceSubtle,
              color: colors.textSecondary,
              fontSize: 12,
            }}
          >
            <span>Timeout</span>
            <InputNumber
              size="small"
              min={1}
              max={60}
              value={timeoutMinutes}
              disabled={installing}
              onChange={(value) => {
                const next = typeof value === 'number' && Number.isFinite(value) ? value : 5
                setTimeoutMinutes(Math.max(1, Math.min(60, Math.round(next))))
              }}
              style={{ width: 64 }}
            />
            <span>min</span>
          </div>
        </Tooltip>

      </div>

      {/* Fetch error */}
      {fetchError && (
        <Alert
          type="error"
          message="Could not load default values"
          description={fetchError}
          style={{ marginBottom: 10, background: 'transparent', border: `1px solid ${colors.statusDown}40` }}
          closable
          onClose={() => setFetchError(null)}
        />
      )}

      {/* Values editor */}
      {sectionTitle(`values.yaml — edit before ${mode === 'upgrade' ? 'upgrade' : 'install'}`)}
      <textarea
        value={valuesYaml}
        onChange={(e) => setValuesYaml(e.target.value)}
        placeholder={
          mode === 'upgrade'
            ? `# No user-supplied values are stored on this release.\n# Type / paste the YAML to apply, or click "Click here to overwrite with default values" above.`
            : `# Click "Load Default Values" to prefill from the chart.\n# Or type / paste your custom values YAML here.\n\n# Example:\n# replicaCount: 1\n# image:\n#   tag: latest`
        }
        spellCheck={false}
        style={{
          width: '100%',
          minHeight: 260,
          resize: 'vertical',
          background: colors.surfaceInsetStrong,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          color: colors.textPrimary,
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
          fontSize: 12,
          lineHeight: 1.6,
          padding: '12px 14px',
          outline: 'none',
          boxSizing: 'border-box',
        }}
      />
      <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 4 }}>
        Leave blank to use chart defaults. Values here are passed as <code>-f values.yaml</code> to helm.
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 16 }}>
        <Button
          onClick={onBack}
          disabled={installing}
          style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
        >
          ← Back
        </Button>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button
            onClick={onCancel}
            disabled={installing}
            style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
          >
            Cancel
          </Button>
          <Button
            type="primary"
            icon={installing ? undefined : <DeploymentUnitOutlined />}
            loading={installing}
            onClick={handleInstall}
            disabled={installing}
            style={{
              background: installing ? `${colors.primary}80` : colors.primary,
              border: 'none',
              minWidth: 140,
              cursor: installing ? 'not-allowed' : 'pointer',
            }}
          >
            {installing ? `${actionLabel}ing…` : `${actionLabel} Release`}
          </Button>
        </div>
      </div>

      {installing && (
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8, color: colors.textMuted, fontSize: 12 }}>
          <Spin size="small" />
          Running <code>helm upgrade --install</code> for this {mode === 'upgrade' ? 'upgrade' : 'install'}… this may take up to 5 minutes.
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main modal
// ---------------------------------------------------------------------------

export default function HelmInstallModal({
  open,
  onClose,
  onInstalled,
  defaultNamespace,
  mode = 'install',
  initialValues,
}: HelmInstallModalProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [step1Values, setStep1Values] = useState<Step1Values | null>(null)
  const [installing, setInstalling] = useState(false)
  const actionLabel = mode === 'upgrade' ? 'Upgrade' : 'Install'

  const step1InitialValues: Partial<Step1Values> = {
    source: 'repo',
    ...initialValues,
  }

  if (!step1InitialValues.namespace) {
    step1InitialValues.namespace = defaultNamespace ?? 'components'
  }

  const handleClose = () => {
    if (installing) return
    setCurrentStep(0)
    setStep1Values(null)
    onClose()
  }

  const handleInstalled = () => {
    setInstalling(false)
    setCurrentStep(0)
    setStep1Values(null)
    onClose()
    onInstalled?.()
  }

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      footer={null}
      width={680}
      destroyOnClose
      closable={!installing}
      maskClosable={!installing}
      keyboard={!installing}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: colors.textPrimary }}>
          <DeploymentUnitOutlined style={{ color: colors.primary }} />
          {actionLabel} Helm Chart
          {installing && (
            <span style={{ fontSize: 12, color: colors.primary, fontWeight: 500 }}>
              · {actionLabel.toLowerCase()}ing…
            </span>
          )}
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
      {/* Steps indicator */}
      <Steps
        current={currentStep}
        size="small"
        style={{ marginBottom: 24 }}
        items={[
          { title: <span style={{ color: currentStep === 0 ? colors.primary : colors.textSecondary }}>Chart Details</span>, icon: <EditOutlined /> },
          { title: <span style={{ color: currentStep === 1 ? colors.primary : colors.textSecondary }}>{`Edit Values & ${actionLabel}`}</span>, icon: <CheckCircleOutlined /> },
        ]}
      />

      {currentStep === 0 && (
        <ChartDetailsStep
          initialValues={step1InitialValues}
          onNext={(vals) => {
            setStep1Values(vals)
            setCurrentStep(1)
          }}
          onCancel={handleClose}
          mode={mode}
        />
      )}

      {currentStep === 1 && step1Values && (
        <EditValuesStep
          step1={step1Values}
          onBack={() => setCurrentStep(0)}
          onInstalled={handleInstalled}
          onCancel={handleClose}
          mode={mode}
          installing={installing}
          setInstalling={setInstalling}
        />
      )}
    </Modal>
  )
}
