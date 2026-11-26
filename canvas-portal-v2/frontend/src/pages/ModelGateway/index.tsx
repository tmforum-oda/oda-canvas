import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ApiOutlined,
  CopyOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'

import {
  createModelGatewayService,
  deleteModelGatewayService,
  fetchModelGatewayServices,
  proxyModelGatewayChat,
  proxyModelGatewayModels,
  proxyModelGatewayToken,
  updateModelGatewayService,
  validateModelGatewayService,
  type ModelGatewayService,
  type ModelGatewayServicePayload,
  type ModelGatewayValidationPayload,
} from '@/api/modelGateway'
import { colors } from '@/theme'

const { Paragraph, Text } = Typography

const DEFAULT_NAMESPACE = 'components'

const DEFAULT_SPEC_YAML = `environmentalFunction:
  type: development
  businessContext: portal-managed
trafficSplitStrategy: round-robin
dependentAIModels:
  - name: example-model
    provider: openai
    version: gpt-4o-mini
    priority: 1
    modality: text
    endpoint: https://api.openai.com/v1
    auth:
      method: bearer
      secretRefs:
        - name: openai-credentials
          key: api-key
gateway:
  authMethod: keycloak
guardrails: {}
`

interface EditorState {
  open: boolean
  service?: ModelGatewayService
}

interface DeleteState {
  open: boolean
  service?: ModelGatewayService
}

interface FormValues {
  name: string
  namespace: string
  specYaml: string
}

// Derive the Keycloak token endpoint for a ModelGatewayService. Operators
// typically set jwtAuth.publicKeyUrl to the realm's JWKS URL; the token
// endpoint sits on the same path, with /certs → /token. Falls back to an
// explicit jwtAuth.tokenUrl (if the operator emits one), or a derivable
// issuer/issuerUrl + realm.
function deriveTokenUrl(service: ModelGatewayService): string {
  const jwt = (service.jwtAuth ?? {}) as Record<string, unknown>

  const explicit = typeof jwt.tokenUrl === 'string' ? jwt.tokenUrl : ''
  if (explicit) return explicit

  const publicKeyUrl = typeof jwt.publicKeyUrl === 'string' ? jwt.publicKeyUrl : ''
  if (publicKeyUrl.includes('/protocol/openid-connect/')) {
    return publicKeyUrl.replace(/\/protocol\/openid-connect\/[^/?#]+.*/, '/protocol/openid-connect/token')
  }

  const issuer = typeof jwt.issuer === 'string' ? jwt.issuer : typeof jwt.issuerUrl === 'string' ? jwt.issuerUrl : ''
  if (issuer) {
    return `${issuer.replace(/\/$/, '')}/protocol/openid-connect/token`
  }

  return ''
}

function extractApiError(error: unknown, fallback: string) {
  if (!error || typeof error !== 'object') return fallback
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = e.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => (d as { msg?: string }).msg ?? JSON.stringify(d)).join('; ')
  return e.message ?? fallback
}

export default function ModelGatewayPage() {
  const queryClient = useQueryClient()
  const [editor, setEditor] = useState<EditorState>({ open: false })
  const [deleteState, setDeleteState] = useState<DeleteState>({ open: false })
  const [testService, setTestService] = useState<ModelGatewayService | null>(null)

  const listQuery = useQuery({
    queryKey: ['model-gateway-services'],
    queryFn: fetchModelGatewayServices,
    refetchInterval: 30_000,
  })

  const items = listQuery.data?.items ?? []
  const available = listQuery.data?.available ?? false

  const columns: ColumnsType<ModelGatewayService> = useMemo(
    () => [
      {
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
        render: (_: unknown, record) => (
          <div>
            <div style={{ fontWeight: 600, color: colors.textPrimary }}>{record.name}</div>
            <div style={{ fontSize: 11, color: colors.textMuted }}>{record.namespace}</div>
          </div>
        ),
      },
      {
        title: 'Models',
        dataIndex: 'modelNames',
        key: 'modelNames',
        render: (value: string, record) => {
          const names = (value && value.length > 0 ? value : record.dependentAIModels.map((m) => m.name).join(', '))
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
          if (names.length === 0) return <Text type="secondary">—</Text>
          return (
            <Space size={4} wrap>
              {names.map((n) => (
                <Tag key={n} color="geekblue">
                  {n}
                </Tag>
              ))}
            </Space>
          )
        },
      },
      {
        title: 'Strategy',
        dataIndex: 'trafficSplitStrategy',
        key: 'trafficSplitStrategy',
        width: 140,
        render: (value: string) => (value ? <Tag color="purple">{value}</Tag> : <Text type="secondary">—</Text>),
      },
      {
        title: 'Endpoint',
        dataIndex: 'endpointUrl',
        key: 'endpointUrl',
        render: (value: string) =>
          value ? (
            <Space size={6}>
              <Text code copyable={{ text: value, icon: <CopyOutlined /> }} style={{ fontSize: 11 }}>
                {value}
              </Text>
            </Space>
          ) : (
            <Text type="secondary">resolving…</Text>
          ),
      },
      {
        title: 'Created',
        dataIndex: 'createdAt',
        key: 'createdAt',
        width: 160,
        render: (value: string) => (value ? new Date(value).toLocaleString() : <Text type="secondary">—</Text>),
      },
      {
        title: 'Actions',
        key: 'actions',
        width: 200,
        render: (_: unknown, record) => (
          <Space size={4}>
            <Tooltip title="Test connection">
              <Button
                size="small"
                icon={<ThunderboltOutlined />}
                onClick={() => setTestService(record)}
                disabled={!record.endpointUrl}
              />
            </Tooltip>
            <Tooltip title="Edit">
              <Button size="small" icon={<EditOutlined />} onClick={() => setEditor({ open: true, service: record })} />
            </Tooltip>
            <Tooltip title="Delete">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => setDeleteState({ open: true, service: record })}
              />
            </Tooltip>
          </Space>
        ),
      },
    ],
    [],
  )

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
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
            <ApiOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>Model Gateway Services</h1>
            <p style={{ fontSize: 12, color: colors.textMuted, margin: '2px 0 0' }}>
              ODA <code>modelgatewayservices.oda.tmforum.org</code> · {items.length} declared
            </p>
          </div>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => listQuery.refetch()}
            loading={listQuery.isFetching}
            style={{ background: 'transparent', border: `1px solid ${colors.border}`, color: colors.textSecondary }}
          >
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setEditor({ open: true })}
            disabled={!available}
          >
            New service
          </Button>
        </Space>
      </div>

      {listQuery.isLoading ? (
        <div style={{ padding: 80, display: 'flex', justifyContent: 'center' }}>
          <Spin />
        </div>
      ) : listQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message="Failed to load Model Gateway Services"
          description={extractApiError(listQuery.error, 'Unknown error')}
        />
      ) : !available ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              <code>modelgatewayservices.oda.tmforum.org</code> CRD is not installed in this cluster.
            </span>
          }
        />
      ) : (
        <Table<ModelGatewayService>
          rowKey={(record) => `${record.namespace}/${record.name}`}
          columns={columns}
          dataSource={items}
          pagination={false}
          locale={{ emptyText: 'No Model Gateway Services declared yet.' }}
          size="middle"
        />
      )}

      <EditorModal
        state={editor}
        onClose={() => setEditor({ open: false })}
        onSaved={() => {
          setEditor({ open: false })
          queryClient.invalidateQueries({ queryKey: ['model-gateway-services'] })
        }}
      />

      <DeleteModal
        state={deleteState}
        onClose={() => setDeleteState({ open: false })}
        onDeleted={() => {
          setDeleteState({ open: false })
          queryClient.invalidateQueries({ queryKey: ['model-gateway-services'] })
        }}
      />

      <TestDrawer service={testService} onClose={() => setTestService(null)} />
    </div>
  )
}

function EditorModal({
  state,
  onClose,
  onSaved,
}: {
  state: EditorState
  onClose: () => void
  onSaved: () => void
}) {
  const [form] = Form.useForm<FormValues>()
  const isEdit = !!state.service

  React.useEffect(() => {
    if (!state.open) return
    if (state.service) {
      // dump spec as YAML-ish (using JSON for simplicity — backend accepts either)
      form.setFieldsValue({
        name: state.service.name,
        namespace: state.service.namespace,
        specYaml: JSON.stringify(state.service.spec, null, 2),
      })
    } else {
      form.setFieldsValue({ name: '', namespace: DEFAULT_NAMESPACE, specYaml: DEFAULT_SPEC_YAML })
    }
  }, [state, form])

  function buildValidationPayload(values: FormValues): ModelGatewayValidationPayload | null {
    const yaml = values.specYaml?.trim()
    if (!yaml) {
      message.error('Spec is required')
      return null
    }
    return {
      name: values.name.trim(),
      namespace: values.namespace.trim(),
      specYaml: yaml,
      mode: isEdit ? 'update' : 'create',
    }
  }

  const validateMutation = useMutation({
    mutationFn: (payload: ModelGatewayValidationPayload) => validateModelGatewayService(payload),
    onSuccess: () => message.success('Spec validated by Kubernetes'),
    onError: (err) => message.error(extractApiError(err, 'Validation failed')),
  })

  const saveMutation = useMutation<ModelGatewayService, unknown, ModelGatewayValidationPayload>({
    mutationFn: async (payload) => {
      await validateModelGatewayService(payload)
      const savePayload: ModelGatewayServicePayload = {
        name: payload.name,
        namespace: payload.namespace,
        specYaml: payload.specYaml,
      }
      return isEdit
        ? updateModelGatewayService(savePayload.namespace, savePayload.name, { specYaml: savePayload.specYaml })
        : createModelGatewayService(savePayload)
    },
    onSuccess: () => {
      message.success(`${isEdit ? 'Updated' : 'Created'} ModelGatewayService`)
      onSaved()
    },
    onError: (err) => message.error(extractApiError(err, 'Save failed')),
  })

  async function handleValidate() {
    const values = await form.validateFields()
    const payload = buildValidationPayload(values)
    if (payload) validateMutation.mutate(payload)
  }

  async function handleSubmit() {
    const values = await form.validateFields()
    const payload = buildValidationPayload(values)
    if (payload) saveMutation.mutate(payload)
  }

  return (
    <Modal
      open={state.open}
      title={isEdit ? `Edit ${state.service?.namespace}/${state.service?.name}` : 'New ModelGatewayService'}
      onCancel={onClose}
      width={760}
      destroyOnClose
      footer={[
        <Button key="cancel" onClick={onClose}>
          Cancel
        </Button>,
        <Button key="validate" onClick={handleValidate} loading={validateMutation.isPending}>
          Validate
        </Button>,
        <Button key="save" type="primary" onClick={handleSubmit} loading={saveMutation.isPending}>
          {isEdit ? 'Save' : 'Create'}
        </Button>,
      ]}
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
        message="Validate runs a dry-run against the Kubernetes API before saving."
      />
      <Form form={form} layout="vertical">
        <Form.Item label="Name" name="name" rules={[{ required: true, message: 'Name is required' }]}>
          <Input disabled={isEdit} placeholder="demo-modelgatewayservice" />
        </Form.Item>
        <Form.Item label="Namespace" name="namespace" rules={[{ required: true, message: 'Namespace is required' }]}>
          <Input disabled={isEdit} placeholder={DEFAULT_NAMESPACE} />
        </Form.Item>
        <Form.Item label="Spec (YAML or JSON)" name="specYaml" rules={[{ required: true, message: 'Spec is required' }]}>
          <Input.TextArea
            autoSize={{ minRows: 16, maxRows: 28 }}
            style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 12 }}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

function DeleteModal({
  state,
  onClose,
  onDeleted,
}: {
  state: DeleteState
  onClose: () => void
  onDeleted: () => void
}) {
  const [confirmName, setConfirmName] = useState('')
  const target = state.service

  React.useEffect(() => {
    if (!state.open) setConfirmName('')
  }, [state.open])

  const deleteMutation = useMutation({
    mutationFn: () => deleteModelGatewayService(target!.namespace, target!.name),
    onSuccess: () => {
      message.success(`Deleted ${target!.namespace}/${target!.name}`)
      onDeleted()
    },
    onError: (err) => message.error(extractApiError(err, 'Delete failed')),
  })

  if (!target) return null

  return (
    <Modal
      open={state.open}
      title="Delete ModelGatewayService"
      onCancel={onClose}
      okText="Delete"
      okButtonProps={{
        danger: true,
        disabled: confirmName !== target.name,
        loading: deleteMutation.isPending,
      }}
      onOk={() => deleteMutation.mutate()}
    >
      <Paragraph>
        This will delete <Text strong>{target.namespace}/{target.name}</Text>. The model-gateway operator will remove the
        underlying Deployment/Service and revoke its Keycloak client.
      </Paragraph>
      <Paragraph>
        Type <Text code>{target.name}</Text> to confirm:
      </Paragraph>
      <Input
        value={confirmName}
        onChange={(e) => setConfirmName(e.target.value)}
        placeholder={target.name}
        autoFocus
      />
    </Modal>
  )
}

function TestDrawer({
  service,
  onClose,
}: {
  service: ModelGatewayService | null
  onClose: () => void
}) {
  const [token, setToken] = useState('')
  const [tokenUrl, setTokenUrl] = useState('')
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [model, setModel] = useState('')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [chatPrompt, setChatPrompt] = useState('Hello! Briefly introduce yourself.')
  const [chatResponse, setChatResponse] = useState<string>('')
  const [tokenResponse, setTokenResponse] = useState<string>('')
  const [modelsResponse, setModelsResponse] = useState<string>('')

  React.useEffect(() => {
    if (!service) return
    setToken('')
    setChatResponse('')
    setTokenResponse('')
    setModelsResponse('')
    setAvailableModels([])
    setTokenUrl(deriveTokenUrl(service))
    setClientId('')
    setClientSecret('')
    setModel('')
  }, [service])

  const gatewayUrl = service?.endpointUrl ?? ''

  const tokenMutation = useMutation({
    mutationFn: () =>
      proxyModelGatewayToken({ token_url: tokenUrl, client_id: clientId, client_secret: clientSecret }),
    onSuccess: (data) => {
      const accessToken = typeof data.access_token === 'string' ? (data.access_token as string) : ''
      if (accessToken) setToken(accessToken)
      setTokenResponse(JSON.stringify(data, null, 2))
    },
    onError: (err) => setTokenResponse(extractApiError(err, 'Token request failed')),
  })

  const modelsMutation = useMutation({
    mutationFn: () => proxyModelGatewayModels(gatewayUrl, token),
    onSuccess: (data) => {
      setModelsResponse(JSON.stringify(data, null, 2))
      const raw = (data as { data?: unknown }).data
      const arr = Array.isArray(raw) ? raw : []
      const ids = arr
        .map((entry) => {
          if (entry && typeof entry === 'object' && 'id' in entry) {
            const id = (entry as { id?: unknown }).id
            return typeof id === 'string' ? id : ''
          }
          return ''
        })
        .filter(Boolean)
      setAvailableModels(ids)
      if (ids.length > 0) setModel(ids[0])
    },
    onError: (err) => {
      setModelsResponse(extractApiError(err, 'Models request failed'))
      setAvailableModels([])
    },
  })

  const chatMutation = useMutation({
    mutationFn: () =>
      proxyModelGatewayChat({ gateway_url: gatewayUrl, token, model, message: chatPrompt }),
    onSuccess: (data) => setChatResponse(JSON.stringify(data, null, 2)),
    onError: (err) => setChatResponse(extractApiError(err, 'Chat request failed')),
  })

  return (
    <Drawer
      open={!!service}
      onClose={onClose}
      title={service ? `Test ${service.namespace}/${service.name}` : ''}
      width={760}
      destroyOnClose
    >
      {service && (
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <Alert
            type="info"
            showIcon
            message={`Endpoint: ${gatewayUrl || 'not yet resolved'}`}
          />

          <section>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>1. Get token</h3>
            <Space direction="vertical" style={{ width: '100%' }} size={6}>
              <Tooltip
                placement="topLeft"
                title={
                  tokenUrl
                    ? 'Auto-derived from jwtAuth.publicKeyUrl on this MGS. Edit if your realm uses a different token endpoint.'
                    : 'Could not derive — the MGS has no jwtAuth.publicKeyUrl/issuer. Paste your Keycloak token endpoint.'
                }
              >
                <Input addonBefore="token_url" value={tokenUrl} onChange={(e) => setTokenUrl(e.target.value)} />
              </Tooltip>
              <Input
                addonBefore="client_id"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="Keycloak client id for this MGS"
              />
              <Input.Password
                addonBefore="client_secret"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
              />
              <Button
                type="primary"
                onClick={() => tokenMutation.mutate()}
                loading={tokenMutation.isPending}
                disabled={!tokenUrl || !clientId || !clientSecret}
              >
                Request token
              </Button>
              {tokenResponse && (
                <Input.TextArea readOnly value={tokenResponse} autoSize={{ minRows: 3, maxRows: 8 }} />
              )}
            </Space>
          </section>

          <section>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>2. List models</h3>
            <Space direction="vertical" style={{ width: '100%' }} size={6}>
              <Input.Password
                addonBefore="token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="paste or auto-filled from step 1"
              />
              <Button
                type="primary"
                onClick={() => modelsMutation.mutate()}
                loading={modelsMutation.isPending}
                disabled={!token || !gatewayUrl}
              >
                GET models
              </Button>
              {modelsResponse && (
                <Input.TextArea readOnly value={modelsResponse} autoSize={{ minRows: 3, maxRows: 8 }} />
              )}
            </Space>
          </section>

          <section>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>3. Chat completion</h3>
            <Space direction="vertical" style={{ width: '100%' }} size={6}>
              {availableModels.length > 0 ? (
                <div style={{ display: 'flex', alignItems: 'stretch' }}>
                  <span
                    style={{
                      padding: '4px 11px',
                      background: '#fafafa',
                      border: '1px solid #d9d9d9',
                      borderRight: 'none',
                      borderRadius: '6px 0 0 6px',
                      color: 'rgba(0,0,0,0.88)',
                      display: 'flex',
                      alignItems: 'center',
                      fontSize: 14,
                    }}
                  >
                    model
                  </span>
                  <Select
                    value={model || undefined}
                    onChange={setModel}
                    options={availableModels.map((id) => ({ value: id, label: id }))}
                    placeholder="Select a model returned by GET models"
                    showSearch
                    style={{ flex: 1, borderTopLeftRadius: 0, borderBottomLeftRadius: 0 }}
                    popupMatchSelectWidth
                  />
                </div>
              ) : (
                <Input
                  addonBefore="model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="Run GET models above to populate this dropdown"
                />
              )}
              <Input.TextArea
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                autoSize={{ minRows: 2, maxRows: 6 }}
              />
              <Button
                type="primary"
                onClick={() => chatMutation.mutate()}
                loading={chatMutation.isPending}
                disabled={!token || !gatewayUrl || !model || !chatPrompt}
              >
                Send chat
              </Button>
              {chatResponse && (
                <Input.TextArea readOnly value={chatResponse} autoSize={{ minRows: 4, maxRows: 12 }} />
              )}
            </Space>
          </section>
        </Space>
      )}
    </Drawer>
  )
}
