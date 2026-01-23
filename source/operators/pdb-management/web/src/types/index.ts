// Core MCP Types
export interface MCPTool {
  name: string;
  description: string;
  parameters: Record<string, any>;
  required?: string[];
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface MCPServerInfo {
  name: string;
  version: string;
  tools: MCPTool[];
  resources: MCPResource[];
  capabilities: MCPCapabilities;
}

export interface MCPCapabilities {
  tools?: {
    listChanged?: boolean;
  };
  resources?: {
    subscribe?: boolean;
    listChanged?: boolean;
  };
  logging?: {};
  prompts?: {
    listChanged?: boolean;
  };
}

// AI Provider Types
export type AIProvider = 'claude' | 'openai' | 'azure-openai' | 'gemini';

export interface AIConfig {
  provider: AIProvider;
  apiKey?: string;
  endpoint?: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  error?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

// PDB Management Types
export interface PodDisruptionBudget {
  metadata: {
    name: string;
    namespace: string;
    labels?: Record<string, string>;
    annotations?: Record<string, string>;
    creationTimestamp: string;
  };
  spec: {
    minAvailable?: number | string;
    maxUnavailable?: number | string;
    selector: {
      matchLabels?: Record<string, string>;
      matchExpressions?: LabelSelectorRequirement[];
    };
    unhealthyPodEvictionPolicy?: 'Always' | 'IfHealthyBudget';
  };
  status: {
    currentHealthy: number;
    desiredHealthy: number;
    disruptionsAllowed: number;
    expectedPods: number;
    observedGeneration?: number;
    conditions?: PDBCondition[];
  };
}

export interface LabelSelectorRequirement {
  key: string;
  operator: 'In' | 'NotIn' | 'Exists' | 'DoesNotExist';
  values?: string[];
}

export interface PDBCondition {
  type: string;
  status: 'True' | 'False' | 'Unknown';
  lastTransitionTime: string;
  reason?: string;
  message?: string;
}

// Policy Types
export interface AvailabilityPolicy {
  id: string;
  name: string;
  description: string;
  namespace?: string;
  selector: PolicySelector;
  availabilityRules: AvailabilityRule[];
  priority: number;
  enforcement: 'strict' | 'advisory' | 'flexible';
  maintenanceWindows?: MaintenanceWindow[];
  createdAt: Date;
  updatedAt: Date;
  status: 'active' | 'inactive' | 'draft';
}

export interface PolicySelector {
  matchLabels?: Record<string, string>;
  matchExpressions?: LabelSelectorRequirement[];
  namespaces?: string[];
  deploymentTypes?: string[];
}

export interface AvailabilityRule {
  type: 'minAvailable' | 'maxUnavailable';
  value: number | string;
  condition?: string;
  schedule?: string;
}

export interface MaintenanceWindow {
  id: string;
  name: string;
  schedule: string;
  duration: string;
  timezone: string;
  suspendPolicies: boolean;
  description?: string;
}

// Cluster Analysis Types
export interface ClusterMetrics {
  totalPods: number;
  totalDeployments: number;
  totalPDBs: number;
  totalPolicies: number;
  healthyPods: number;
  unhealthyPods: number;
  nodesCount: number;
  lastUpdated: Date;
}

export interface NamespaceAnalysis {
  namespace: string;
  podsCount: number;
  deploymentsCount: number;
  pdbsCount: number;
  policiesCount: number;
  coveragePercentage: number;
  riskLevel: 'low' | 'medium' | 'high';
  recommendations: string[];
}

export interface PolicyConflict {
  id: string;
  type: 'overlap' | 'contradiction' | 'priority';
  severity: 'low' | 'medium' | 'high';
  policies: string[];
  resource: string;
  description: string;
  resolution?: string;
}

// UI State Types
export interface AppState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  aiConfig: AIConfig;
  mcpConnected: boolean;
  wsConnected: boolean;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
  currentModel: string;
}

export interface ToolState {
  availableTools: MCPTool[];
  executingTool?: string;
  toolHistory: ToolExecution[];
}

export interface ToolExecution {
  id: string;
  toolName: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime: number;
  checks: {
    database: boolean;
    mcp: boolean;
    kubernetes: boolean;
  };
}

// Form Types
export interface PolicyFormData {
  name: string;
  description: string;
  namespace: string;
  enforcement: 'strict' | 'advisory' | 'flexible';
  priority: number;
  selector: {
    matchLabels: Record<string, string>;
    namespaces: string[];
  };
  availabilityRules: {
    type: 'minAvailable' | 'maxUnavailable';
    value: string;
  }[];
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
}

export interface WSConnectionState {
  connected: boolean;
  reconnecting: boolean;
  lastConnected?: Date;
  error?: string;
}