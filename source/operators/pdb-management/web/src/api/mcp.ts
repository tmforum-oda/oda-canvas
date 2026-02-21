import axios, { AxiosInstance, AxiosError } from 'axios';
import { 
  MCPServerInfo, 
  MCPTool, 
  MCPResource, 
  ToolExecution, 
  ApiResponse,
  HealthCheck 
} from '@/types';

class MCPClient {
  private api: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    this.api = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`[MCP] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[MCP] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor
    this.api.interceptors.response.use(
      (response) => {
        console.log(`[MCP] Response ${response.status}:`, response.data);
        return response;
      },
      (error: AxiosError) => {
        console.error('[MCP] Response error:', error);
        if (error.response?.status === 401) {
          // Handle unauthorized
          console.warn('[MCP] Unauthorized access');
        } else if (error.response?.status >= 500) {
          // Handle server errors
          console.error('[MCP] Server error:', error.response.data);
        }
        return Promise.reject(error);
      }
    );
  }

  // Helper method for JSON-RPC calls
  private async callMCPMethod(method: string, params: any = {}): Promise<any> {
    const requestId = Math.random().toString(36).substring(7);
    const request = {
      id: requestId,
      method,
      params,
    };

    try {
      const response = await this.api.post('/mcp', request);
      const result = response.data;
      
      if (result.error) {
        throw new Error(`MCP Error: ${result.error.message} (Code: ${result.error.code})`);
      }
      
      return result.result;
    } catch (error) {
      console.error(`[MCP] ${method} failed:`, error);
      throw error;
    }
  }

  // Health check
  async checkHealth(): Promise<HealthCheck> {
    try {
      const response = await this.api.get('/health');
      // Handle raw response from MCP server
      const data = response.data;
      return {
        status: data.status || 'unhealthy',
        version: data.version || 'unknown',
        uptime: data.uptime || 0,
        checks: {
          database: data.initialized || false,
          mcp: data.checks?.mcp ?? (data.status === 'healthy'),
          kubernetes: data.checks?.kubernetes ?? false,
        },
      };
    } catch (error) {
      console.error('[MCP] Health check failed:', error);
      throw new Error('Health check failed');
    }
  }

  // Get server information
  async getServerInfo(): Promise<MCPServerInfo> {
    try {
      // Get tools to verify server is working and get basic info
      const tools = await this.listTools();
      
      // Return mock server info since MCP doesn't have a direct info endpoint
      return {
        name: 'PDB Management MCP Server',
        version: '1.0.0',
        tools,
        resources: [], // Would need to call resources/list if needed
        capabilities: {
          tools: { listChanged: false },
          resources: { subscribe: false, listChanged: false },
          logging: {},
          prompts: { listChanged: false },
        },
      };
    } catch (error) {
      console.warn('[MCP] Server info not available, using fallback');
      return {
        name: 'PDB Management MCP Server',
        version: '1.0.0',
        tools: [],
        resources: [],
        capabilities: {
          tools: { listChanged: false },
          resources: { subscribe: false, listChanged: false },
          logging: {},
          prompts: { listChanged: false },
        },
      };
    }
  }

  // List available tools
  async listTools(): Promise<MCPTool[]> {
    try {
      const result = await this.callMCPMethod('tools/list');
      // Convert from MCP format to our internal format
      return result.tools.map((tool: any) => ({
        name: tool.name,
        description: tool.description,
        parameters: tool.inputSchema || {},
        required: tool.inputSchema?.required || [],
      }));
    } catch (error) {
      console.error('[MCP] Failed to list tools:', error);
      return []; // Return empty array on failure
    }
  }

  // Execute a tool
  async executeTool(
    toolName: string, 
    parameters: Record<string, any>
  ): Promise<ToolExecution> {
    try {
      const startTime = new Date();
      console.log(`[MCP] Executing tool: ${toolName}`, parameters);

      const result = await this.callMCPMethod('tools/call', {
        name: toolName,
        arguments: parameters,
      });

      const endTime = new Date();
      const duration = endTime.getTime() - startTime.getTime();

      // Extract text content from MCP response
      let textResult = '';
      if (result.content && Array.isArray(result.content)) {
        textResult = result.content
          .filter((item: any) => item.type === 'text')
          .map((item: any) => item.text)
          .join('\n');
      }

      return {
        id: crypto.randomUUID(),
        toolName,
        parameters,
        result: textResult || result,
        startTime,
        endTime,
        duration,
      };
    } catch (error) {
      console.error(`[MCP] Tool execution failed for ${toolName}:`, error);
      
      const endTime = new Date();
      const startTime = new Date(endTime.getTime() - 1000); // Estimate start time
      
      return {
        id: crypto.randomUUID(),
        toolName,
        parameters,
        error: error instanceof Error ? error.message : 'Unknown error',
        startTime,
        endTime,
        duration: endTime.getTime() - startTime.getTime(),
      };
    }
  }

  // List available resources
  async listResources(): Promise<MCPResource[]> {
    try {
      const result = await this.callMCPMethod('resources/list');
      return result.resources || [];
    } catch (error) {
      console.error('[MCP] Failed to list resources:', error);
      return []; // Return empty array on failure
    }
  }

  // Read a resource
  async readResource(uri: string): Promise<any> {
    try {
      const result = await this.callMCPMethod('resources/read', { uri });
      return result;
    } catch (error) {
      console.error(`[MCP] Failed to read resource ${uri}:`, error);
      throw error;
    }
  }

  // PDB Management specific methods
  async listPDBs(namespace?: string): Promise<any[]> {
    return this.executeTool('list_pdbs', namespace ? { namespace } : {})
      .then(result => result.result || []);
  }

  async getPDB(name: string, namespace: string): Promise<any> {
    return this.executeTool('get_pdb', { name, namespace })
      .then(result => result.result);
  }

  async createPDB(spec: any): Promise<any> {
    return this.executeTool('create_pdb', { spec })
      .then(result => result.result);
  }

  async updatePDB(name: string, namespace: string, spec: any): Promise<any> {
    return this.executeTool('update_pdb', { name, namespace, spec })
      .then(result => result.result);
  }

  async deletePDB(name: string, namespace: string): Promise<any> {
    return this.executeTool('delete_pdb', { name, namespace })
      .then(result => result.result);
  }

  async listPolicies(): Promise<any[]> {
    // Use validate_policy_compliance to get policies list
    try {
      const compliance = await this.validatePolicyCompliance();
      if (compliance?.policies && Array.isArray(compliance.policies)) {
        // Transform to expected format
        return compliance.policies.map((p: any) => ({
          id: `${p.namespace}/${p.name}`,
          name: p.name,
          namespace: p.namespace,
          description: `${p.availabilityClass} policy with ${p.enforcement} enforcement`,
          availabilityClass: p.availabilityClass,
          enforcement: p.enforcement,
          priority: p.priority,
          status: 'active',
          selector: p.componentSelector,
          applicableDeployments: p.applicableDeployments,
        }));
      }
      return [];
    } catch (error) {
      console.error('[MCP] Failed to list policies:', error);
      return [];
    }
  }

  async getPolicy(id: string): Promise<any> {
    // Find policy from the list
    const policies = await this.listPolicies();
    return policies.find(p => p.id === id || p.name === id);
  }

  async createPolicy(policy: any): Promise<any> {
    return this.executeTool('create_availability_policy', policy)
      .then(result => result.result);
  }

  async updatePolicy(id: string, policy: any): Promise<any> {
    // Update is not directly supported, return error
    console.warn('[MCP] Policy update not supported via MCP tools');
    throw new Error('Policy update requires direct Kubernetes access');
  }

  async deletePolicy(id: string): Promise<any> {
    // Delete is not directly supported, return error
    console.warn('[MCP] Policy delete not supported via MCP tools');
    throw new Error('Policy delete requires direct Kubernetes access');
  }

  async analyzeCluster(namespace?: string, detailed: boolean = true): Promise<any> {
    const result = await this.executeTool('analyze_cluster_availability', {
      namespace,
      detailed
    });
    // Parse the result if it's a string
    if (typeof result.result === 'string') {
      try {
        return JSON.parse(result.result);
      } catch {
        return result.result;
      }
    }
    return result.result;
  }

  async analyzeWorkloadPatterns(namespace?: string): Promise<any> {
    const result = await this.executeTool('analyze_workload_patterns', { namespace });
    if (typeof result.result === 'string') {
      try {
        return JSON.parse(result.result);
      } catch {
        return result.result;
      }
    }
    return result.result;
  }

  async getClusterMetrics(): Promise<any> {
    // Use analyze_cluster_availability to get metrics
    return this.analyzeCluster();
  }

  async validatePolicyCompliance(namespace?: string): Promise<any> {
    const result = await this.executeTool('validate_policy_compliance', {
      namespace,
      showDetails: true,
      includeFixed: true
    });
    if (typeof result.result === 'string') {
      try {
        return JSON.parse(result.result);
      } catch {
        return result.result;
      }
    }
    return result.result;
  }

  async monitorPDBEvents(namespaces?: string[]): Promise<any> {
    const result = await this.executeTool('monitor_pdb_events', {
      namespaces,
      maxEvents: 50,
      includeRelated: true
    });
    if (typeof result.result === 'string') {
      try {
        return JSON.parse(result.result);
      } catch {
        return result.result;
      }
    }
    return result.result;
  }

  async validatePolicy(policy: any): Promise<any> {
    return this.executeTool('validate_policy', { policy })
      .then(result => result.result);
  }

  async simulatePolicyImpact(policy: any): Promise<any> {
    return this.executeTool('simulate_policy_impact', { policy })
      .then(result => result.result);
  }

  async getRecommendations(namespace?: string): Promise<any[]> {
    return this.executeTool('get_recommendations', namespace ? { namespace } : {})
      .then(result => result.result || []);
  }

  async detectConflicts(): Promise<any[]> {
    return this.executeTool('detect_conflicts', {})
      .then(result => result.result || []);
  }

  async getNamespaces(): Promise<string[]> {
    return this.executeTool('list_namespaces', {})
      .then(result => result.result || []);
  }

  async getDeployments(namespace?: string): Promise<any[]> {
    return this.executeTool('list_deployments', namespace ? { namespace } : {})
      .then(result => result.result || []);
  }

  async getNodes(): Promise<any[]> {
    return this.executeTool('list_nodes', {})
      .then(result => result.result || []);
  }
}

// Create and export singleton instance
export const mcpClient = new MCPClient();
export default mcpClient;