import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { 
  AppState, 
  ChatState, 
  ToolState, 
  AIConfig, 
  ChatMessage, 
  MCPTool, 
  ToolExecution,
  WSConnectionState 
} from '@/types';

// App Store
interface AppStore extends AppState {
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setAIConfig: (config: AIConfig) => void;
  setMCPConnected: (connected: boolean) => void;
  setWSConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      aiConfig: {
        provider: 'claude',
        model: 'claude-sonnet-4-5-20250929',
        maxTokens: 4096,
        temperature: 0.7,
      },
      mcpConnected: false,
      wsConnected: false,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setAIConfig: (config) => set({ aiConfig: config }),
      setMCPConnected: (connected) => set({ mcpConnected: connected }),
      setWSConnected: (connected) => set({ wsConnected: connected }),
    }),
    {
      name: 'oda-pdb-app-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
        aiConfig: state.aiConfig,
      }),
    }
  )
);

// Chat Store
interface ChatStore extends ChatState {
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | undefined) => void;
  setCurrentModel: (model: string) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  error: undefined,
  currentModel: 'claude-sonnet-4-5-20250929',
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),
  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setCurrentModel: (model) => set({ currentModel: model }),
}));

// Tool Store
interface ToolStore extends ToolState {
  setAvailableTools: (tools: MCPTool[]) => void;
  setExecutingTool: (toolName: string | undefined) => void;
  addToolExecution: (execution: Omit<ToolExecution, 'id'>) => void;
  updateToolExecution: (id: string, updates: Partial<ToolExecution>) => void;
  clearToolHistory: () => void;
}

export const useToolStore = create<ToolStore>((set) => ({
  availableTools: [],
  executingTool: undefined,
  toolHistory: [],
  setAvailableTools: (tools) => set({ availableTools: tools }),
  setExecutingTool: (toolName) => set({ executingTool: toolName }),
  addToolExecution: (execution) =>
    set((state) => ({
      toolHistory: [
        {
          ...execution,
          id: crypto.randomUUID(),
        },
        ...state.toolHistory,
      ].slice(0, 100), // Keep only last 100 executions
    })),
  updateToolExecution: (id, updates) =>
    set((state) => ({
      toolHistory: state.toolHistory.map((exec) =>
        exec.id === id ? { ...exec, ...updates } : exec
      ),
    })),
  clearToolHistory: () => set({ toolHistory: [] }),
}));

// WebSocket Store
interface WSStore extends WSConnectionState {
  setConnected: (connected: boolean) => void;
  setReconnecting: (reconnecting: boolean) => void;
  setLastConnected: (date: Date) => void;
  setError: (error: string | undefined) => void;
  reset: () => void;
}

export const useWSStore = create<WSStore>((set) => ({
  connected: false,
  reconnecting: false,
  lastConnected: undefined,
  error: undefined,
  setConnected: (connected) => set({ connected, error: undefined }),
  setReconnecting: (reconnecting) => set({ reconnecting }),
  setLastConnected: (date) => set({ lastConnected: date }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      connected: false,
      reconnecting: false,
      lastConnected: undefined,
      error: undefined,
    }),
}));

// Policy Store
interface PolicyFormStore {
  formData: any;
  isDirty: boolean;
  setFormData: (data: any) => void;
  updateField: (field: string, value: any) => void;
  setDirty: (dirty: boolean) => void;
  reset: () => void;
}

export const usePolicyFormStore = create<PolicyFormStore>((set) => ({
  formData: {
    name: '',
    description: '',
    namespace: '',
    enforcement: 'flexible',
    priority: 100,
    selector: {
      matchLabels: {},
      namespaces: [],
    },
    availabilityRules: [
      {
        type: 'minAvailable',
        value: '1',
      },
    ],
  },
  isDirty: false,
  setFormData: (data) => set({ formData: data, isDirty: true }),
  updateField: (field, value) =>
    set((state) => ({
      formData: {
        ...state.formData,
        [field]: value,
      },
      isDirty: true,
    })),
  setDirty: (dirty) => set({ isDirty: dirty }),
  reset: () =>
    set({
      formData: {
        name: '',
        description: '',
        namespace: '',
        enforcement: 'flexible',
        priority: 100,
        selector: {
          matchLabels: {},
          namespaces: [],
        },
        availabilityRules: [
          {
            type: 'minAvailable',
            value: '1',
          },
        ],
      },
      isDirty: false,
    }),
}));

// Notification Store
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationStore {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          ...notification,
          id: crypto.randomUUID(),
        },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearAll: () => set({ notifications: [] }),
}));

// Export all stores
export {
  type AppStore,
  type ChatStore,
  type ToolStore,
  type WSStore,
  type PolicyFormStore,
  type NotificationStore,
  type Notification,
};