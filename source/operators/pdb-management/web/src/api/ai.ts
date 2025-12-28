import axios, { AxiosInstance } from 'axios';
import { AIProvider, AIConfig, ChatMessage, ToolCall } from '@/types';

interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  maxTokens?: number;
  temperature?: number;
  tools?: any[];
  toolChoice?: string;
}

interface ChatResponse {
  message: ChatMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

class AIClient {
  private api: AxiosInstance;
  private config: AIConfig;

  constructor(config: AIConfig) {
    this.config = config;
    this.api = axios.create({
      baseURL: '/api',
      timeout: 120000, // 2 minutes for AI responses
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`[AI] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[AI] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor
    this.api.interceptors.response.use(
      (response) => {
        console.log(`[AI] Response ${response.status}`);
        return response;
      },
      (error) => {
        console.error('[AI] Response error:', error);
        return Promise.reject(error);
      }
    );
  }

  updateConfig(config: AIConfig) {
    this.config = config;
  }

  async chat(
    messages: ChatMessage[],
    options: {
      tools?: any[];
      toolChoice?: string;
      stream?: boolean;
    } = {}
  ): Promise<ChatResponse> {
    try {
      // Get available MCP tools if not provided
      if (!options.tools) {
        const { default: mcpClient } = await import('./mcp');
        const mcpTools = await mcpClient.listTools();
        if (mcpTools.length > 0) {
          // Use chatWithTools to let AI provider choose tools intelligently
          return await this.chatWithTools(messages, mcpTools);
        }
      }

      // Fallback to direct tool usage if tools are provided
      if (options.tools && options.tools.length > 0) {
        return await this.chatWithTools(messages, options.tools);
      }

      // Final fallback - simple response without tools
      return {
        message: {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'I can help you with PDB management tasks, but MCP tools are not currently available. Please ensure the MCP server is running and try again.',
          timestamp: new Date(),
        },
      };
    } catch (error) {
      console.error('[AI] Chat request failed:', error);
      throw error;
    }
  }

  // Helper function to format any value for display
  private formatValue(value: any, indent: string = ''): string {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        return value.map((item, index) => {
          if (typeof item === 'object') {
            return `${indent}${index + 1}. ${this.formatValue(item, indent + '   ')}`;
          }
          return `${indent}• ${item}`;
        }).join('\n');
      } else {
        // For objects, try to extract meaningful fields
        const text = value.message || value.description || value.name || value.title || value.text;
        if (text) {
          return text;
        }
        // If no meaningful field found, format as key-value pairs
        const entries = Object.entries(value)
          .filter(([key]) => !key.startsWith('_')) // Skip private fields
          .map(([key, val]) => `${key}: ${this.formatValue(val, indent + '  ')}`)
          .join(', ');
        return entries || JSON.stringify(value);
      }
    }
    
    return String(value);
  }

  // Helper function to format cluster availability analysis
  private formatClusterAnalysis(data: any, namespace?: string): string {
    try {
      const parsed = typeof data === 'string' ? JSON.parse(data) : data;
      
      if (!parsed.summary) {
        return 'No PDB analysis data available.';
      }
      
      const { summary, coverage } = parsed;
      const nsFilter = namespace ? ` in namespace "${namespace}"` : '';
      
      let response = `## PDB Analysis${nsFilter}\n\n`;
      
      // Summary section - more concise
      response += `**Summary**: ${summary.deploymentsWithPDB}/${summary.totalDeployments} deployments have PDB protection (${summary.coveragePercentage}%)\n\n`;
      
      // Availability classes if present - condensed
      if (summary.availabilityClasses && Object.keys(summary.availabilityClasses).length > 0) {
        const classes = Object.entries(summary.availabilityClasses)
          .map(([name, count]) => `${name}: ${count}`)
          .join(', ');
        response += `**Availability Classes**: ${classes}\n\n`;
      }
      
      // Coverage by namespace if not filtering by specific namespace - condensed
      if (!namespace && coverage.byNamespace && Object.keys(coverage.byNamespace).length > 0) {
        response += `**Namespace Coverage**:\n`;
        for (const [ns, nsData] of Object.entries(coverage.byNamespace)) {
          const nsInfo = nsData as any;
          response += `• ${ns}: ${nsInfo.percentage}%\n`;
        }
        response += '\n';
      }
      
      // Issues if present - limit to top 5 and be more concise
      if (parsed.issues && parsed.issues.length > 0) {
        const maxIssues = 5;
        const issuesToShow = parsed.issues.slice(0, maxIssues);
        response += `**Issues Found** (showing ${issuesToShow.length}${parsed.issues.length > maxIssues ? ` of ${parsed.issues.length}` : ''}):\n`;
        issuesToShow.forEach((issue: any, index: number) => {
          const issueText = issue.description || issue.message || issue.issue || String(issue);
          const resource = issue.resource ? ` in ${issue.resource}` : '';
          response += `${index + 1}. ${issueText}${resource}\n`;
        });
        response += '\n';
      }
      
      // Conclusion
      if (summary.totalDeployments === 0) {
        response += `No deployments found${nsFilter}.`;
      } else if (summary.coveragePercentage === 100) {
        response += `All deployments${nsFilter} have PDB protection.`;
      } else {
        response += `Consider adding PDB policies for ${summary.deploymentsWithoutPDB} unprotected deployment(s).`;
      }
      
      return response;
    } catch (error) {
      console.error('Error formatting cluster analysis:', error);
      return 'Unable to format the analysis data. Please check the raw response in the browser console.';
    }
  }

  // Helper function to format policy recommendations  
  private formatPolicyRecommendations(data: any): string {
    try {
      const parsed = typeof data === 'string' ? JSON.parse(data) : data;
      
      let response = `## Policy Recommendations\n\n`;
      
      if (parsed.policies && Array.isArray(parsed.policies)) {
        // Format as a simple summary
        response += `**Found ${parsed.policies.length} policy recommendation(s):**\n\n`;
        
        parsed.policies.forEach((policy: any, index: number) => {
          response += `**${index + 1}. ${policy.name || `Policy ${index + 1}`}**\n`;
          response += `• Type: ${policy.type || 'Unknown'}\n`;
          response += `• Scope: ${policy.scope || 'Unknown'}\n`;
          response += `• Availability Class: ${policy.availabilityClass || 'standard'}\n`;
          response += `• Enforcement: ${policy.enforcement || 'advisory'}\n`;
          if (policy.reasoning && policy.reasoning.length > 0) {
            response += `• Reason: ${policy.reasoning[0]}\n`;
          }
          response += '\n';
        });
        
        if (parsed.summary) {
          response += `**Summary**: ${parsed.summary.totalPolicies} total policies found\n`;
        }
      } else if (parsed.recommendations && Array.isArray(parsed.recommendations)) {
        // Handle alternative format
        parsed.recommendations.slice(0, 3).forEach((rec: any, index: number) => {
          response += `**${index + 1}. ${rec.name || rec.title || `Recommendation ${index + 1}`}**\n`;
          response += `Priority: ${rec.priority || 'Medium'} | ${rec.description || 'No description'}\n\n`;
        });
      } else if (parsed.error) {
        response += `Error: ${parsed.error}`;
      } else {
        response += `No policy conflicts or overlaps detected. Your current policies appear to be well-configured.`;
      }
      
      return response;
    } catch (error) {
      console.error('Error formatting recommendations:', error);
      return 'Unable to format the recommendation data. Please check the raw response in the browser console.';
    }
  }

  // Helper function to format workload patterns
  private formatWorkloadPatterns(data: any): string {
    try {
      const parsed = typeof data === 'string' ? JSON.parse(data) : data;
      
      let response = `## Workload Patterns Analysis\n\n`;
      
      if (parsed.patterns && Array.isArray(parsed.patterns)) {
        parsed.patterns.forEach((pattern: any, index: number) => {
          response += `### Pattern ${index + 1}: ${pattern.type || 'Unknown'}\n`;
          response += `**Components:** ${pattern.componentCount || 0}\n`;
          response += `**Characteristics:** ${pattern.characteristics || 'None specified'}\n\n`;
        });
      } else if (parsed.summary) {
        response += `**Summary:** ${parsed.summary}\n\n`;
      }
      
      if (parsed.recommendations && Array.isArray(parsed.recommendations)) {
        response += `### Recommendations\n`;
        parsed.recommendations.forEach((rec: string) => {
          response += `• ${rec}\n`;
        });
      }
      
      return response;
    } catch (error) {
      console.error('Error formatting workload patterns:', error);
      return 'Unable to format the workload patterns data. Please check the raw response in the browser console.';
    }
  }

  private async selectAndExecuteTool(query: string): Promise<string> {
    // Import MCP client dynamically to avoid circular dependencies
    const { default: mcpClient } = await import('./mcp');
    
    // Normalize query
    const queryLower = query.toLowerCase().trim();
    
    try {
      // Extract namespace from query using improved patterns
      const extractNamespace = (text: string): string | undefined => {
        // Pattern: "namespace pdb-demo" or "namespace: pdb-demo"
        let match = text.match(/namespace\s*:?\s*([\w-]+)/i);
        if (match) return match[1];
        
        // Pattern: "in the pdb-demo namespace" 
        match = text.match(/in\s+the\s+([\w-]+)\s+namespace/i);
        if (match) return match[1];
        
        // Pattern: "in pdb-demo"
        match = text.match(/in\s+([\w-]+)(?:\s+namespace)?/i);
        if (match && match[1] !== 'the') return match[1];
        
        return undefined;
      };
      
      // Intelligent question routing based on intent analysis
      // Questions about deployment status, availability, node failure impact, missing policies
      if (this.isAvailabilityAnalysisQuery(queryLower)) {
        const namespace = extractNamespace(query);
        const result = await mcpClient.executeTool('analyze_cluster_availability', { 
          namespace,
          detailed: true 
        });
        
        if (result.error) {
          return `Error: ${result.error}`;
        }
        
        return this.formatClusterAnalysis(result.result, namespace);
      }
      
      // Questions about policy recommendations, suggestions, best practices
      if (this.isPolicyRecommendationQuery(queryLower)) {
        const result = await mcpClient.executeTool('recommend_policies', { scope: 'cluster' });
        
        if (result.error) {
          return `Error: ${result.error}`;
        }
        
        return this.formatPolicyRecommendations(result.result);
      }
      
      // Questions about workload patterns, architecture analysis
      if (this.isWorkloadPatternQuery(queryLower)) {
        const result = await mcpClient.executeTool('analyze_workload_patterns', {});
        
        if (result.error) {
          return `Error: ${result.error}`;
        }
        
        return this.formatWorkloadPatterns(result.result);
      }
      
      // Default: For any PDB/deployment/availability related question, use analyze_cluster_availability
      // This catches questions that don't match specific patterns but are still PDB-related
      if (this.isPDBRelatedQuery(queryLower)) {
        const namespace = extractNamespace(query);
        const result = await mcpClient.executeTool('analyze_cluster_availability', { 
          namespace,
          detailed: true 
        });
        
        if (result.error) {
          return `Error: ${result.error}`;
        }
        
        return this.formatClusterAnalysis(result.result, namespace);
      }
      
      // If nothing matches, provide help
      return `I can help you with PDB management tasks. Try asking:
      
• About deployments: "Which deployments don't have availability policies?"
• About node failures: "Which deployments would be affected by a node failure?"
• About PDB status: "List all PDBs" or "Show PDB coverage"
• For recommendations: "What policies do you recommend?"
• About workload patterns: "Analyze workload patterns"

Ask me anything about Pod Disruption Budget management!`;
      
    } catch (error) {
      console.error('[AI] Tool execution failed:', error);
      return `I encountered an error while processing your request: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or ask about PDB management topics.`;
    }
  }

  // Helper method to determine if query is asking about availability analysis
  private isAvailabilityAnalysisQuery(query: string): boolean {
    const availabilityKeywords = [
      'deployment', 'deployments', 'pod', 'pods', 'service', 'services',
      'affected', 'impact', 'node failure', 'failure', 'availability',
      'protection', 'protected', 'unprotected', 'covered', 'coverage',
      'pdb', 'budget', 'disruption', 'policy', 'policies',
      'list', 'show', 'display', 'analyze', 'analysis', 'check', 'status',
      'which', 'what', 'how many', 'count', 'missing', 'without', 'have', 'don\'t have'
    ];
    
    const availabilityPhrases = [
      'node failure', 'affected by', 'don\'t have', 'without policies',
      'missing policies', 'availability policies', 'disruption budget',
      'pdb coverage', 'cluster analysis', 'deployment status'
    ];
    
    // Check for phrases first (more specific)
    for (const phrase of availabilityPhrases) {
      if (query.includes(phrase)) {
        return true;
      }
    }
    
    // Then check for individual keywords
    const hasAvailabilityKeyword = availabilityKeywords.some(keyword => 
      query.includes(keyword)
    );
    
    return hasAvailabilityKeyword;
  }

  // Helper method to determine if query is asking for policy recommendations
  private isPolicyRecommendationQuery(query: string): boolean {
    const recommendationKeywords = [
      'recommend', 'suggestion', 'suggest', 'advice', 'should', 'best practice',
      'configure', 'setup', 'create', 'implement', 'optimize', 'improve'
    ];
    
    const recommendationPhrases = [
      'what should', 'how should', 'best practice', 'recommend for',
      'suggest for', 'what policies', 'how to configure', 'should i use'
    ];
    
    // Check for phrases first
    for (const phrase of recommendationPhrases) {
      if (query.includes(phrase)) {
        return true;
      }
    }
    
    // Then check for individual keywords
    return recommendationKeywords.some(keyword => query.includes(keyword));
  }

  // Helper method to determine if query is asking about workload patterns
  private isWorkloadPatternQuery(query: string): boolean {
    const workloadKeywords = [
      'workload', 'pattern', 'architecture', 'design', 'structure',
      'component', 'microservice', 'application', 'topology'
    ];
    
    const workloadPhrases = [
      'workload pattern', 'application pattern', 'deployment pattern',
      'architecture analysis', 'component analysis'
    ];
    
    // Check for phrases first
    for (const phrase of workloadPhrases) {
      if (query.includes(phrase)) {
        return true;
      }
    }
    
    // Then check for individual keywords
    return workloadKeywords.some(keyword => query.includes(keyword));
  }

  // Helper method to determine if query is PDB-related (catches general questions)
  private isPDBRelatedQuery(query: string): boolean {
    const pdbKeywords = [
      'pdb', 'pod disruption budget', 'disruption', 'availability',
      'kubernetes', 'cluster', 'deployment', 'pod', 'service',
      'namespace', 'policy', 'protection'
    ];
    
    return pdbKeywords.some(keyword => query.includes(keyword));
  }

  async chatWithTools(
    messages: ChatMessage[],
    availableTools: any[]
  ): Promise<ChatResponse> {
    try {
      // Check if we have a valid API key
      if (!this.config.apiKey) {
        return {
          message: {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Please configure your AI provider API key in the sidebar to use this feature.',
            timestamp: new Date(),
          },
        };
      }

      // Convert MCP tools to the format expected by AI providers
      const tools = availableTools.map(tool => ({
        type: 'function',
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters,
        },
      }));

      // Create system message about available tools
      const systemMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'system',
        content: `You are a helpful assistant for managing Kubernetes Pod Disruption Budgets (PDBs). You have access to the following tools:

${availableTools.map(tool => `- ${tool.name}: ${tool.description}`).join('\n')}

When users ask questions about PDBs, deployments, policies, or cluster analysis, choose the most appropriate tool to help them. Always explain which tool you're using and why.`,
        timestamp: new Date(),
      };

      const messagesWithSystem = [systemMessage, ...messages];

      // Make actual API call to the AI provider
      const response = await this.callAIProvider(messagesWithSystem, tools);

      // If the AI wants to use tools, execute them via MCP
      if (response.message.toolCalls && response.message.toolCalls.length > 0) {
        const { default: mcpClient } = await import('./mcp');
        
        // Execute tool calls
        const executedTools = await Promise.all(
          response.message.toolCalls.map(async (toolCall) => {
            try {
              console.log(`[AI] ${this.config.provider} is calling tool: ${toolCall.name}`);
              const result = await mcpClient.executeTool(
                toolCall.name,
                toolCall.parameters
              );
              
              return {
                ...toolCall,
                result: result.result,
                status: 'completed' as const,
              };
            } catch (error) {
              return {
                ...toolCall,
                error: error instanceof Error ? error.message : 'Tool execution failed',
                status: 'error' as const,
              };
            }
          })
        );

        // Format tool results and create a follow-up message
        const toolResults = executedTools.map(tool => {
          if (tool.status === 'completed') {
            // Format the result based on the tool used
            let formattedResult: string;
            switch (tool.name) {
              case 'analyze_cluster_availability':
                formattedResult = this.formatClusterAnalysis(tool.result, tool.parameters?.namespace);
                break;
              case 'recommend_policies':
                formattedResult = this.formatPolicyRecommendations(tool.result);
                break;
              case 'analyze_workload_patterns':
                formattedResult = this.formatWorkloadPatterns(tool.result);
                break;
              default:
                formattedResult = JSON.stringify(tool.result, null, 2);
            }
            return formattedResult;
          } else {
            return `Error executing ${tool.name}: ${tool.error}`;
          }
        }).join('\n\n');

        const providerName = this.config.provider === 'claude' ? 'Claude' : 
                           this.config.provider === 'openai' ? 'OpenAI' :
                           this.config.provider === 'azure-openai' ? 'Azure OpenAI' :
                           this.config.provider === 'gemini' ? 'Gemini' : 'AI';

        const toolsUsed = executedTools.map(t => t.name).join(', ');
        const finalResponse = `**${providerName} used tools: ${toolsUsed}**\n\n${toolResults}`;

        return {
          message: {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: finalResponse,
            timestamp: new Date(),
            toolCalls: executedTools,
          },
        };
      }

      return response;
    } catch (error) {
      console.error('[AI] Chat with tools failed:', error);
      return {
        message: {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Error communicating with ${this.config.provider}: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your API key and try again.`,
          timestamp: new Date(),
        },
      };
    }
  }

  // New method to make actual AI provider API calls via MCP server proxy
  private async callAIProvider(messages: ChatMessage[], tools: any[]): Promise<ChatResponse> {
    // Convert ChatMessage format to match the backend AI message format
    const backendMessages = messages.map(msg => ({
      id: msg.id || crypto.randomUUID(),
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp || new Date(),
      toolCalls: msg.toolCalls || [],
    }));

    // Convert tools to backend format
    const backendTools = tools.map(tool => ({
      type: tool.type || 'function',
      function: {
        name: tool.function?.name || tool.name,
        description: tool.function?.description || tool.description,
        parameters: tool.function?.parameters || tool.parameters,
      },
    }));

    const proxyRequest = {
      config: {
        provider: this.config.provider,
        apiKey: this.config.apiKey,
        baseURL: this.config.baseURL,
        model: this.config.model,
        maxTokens: this.config.maxTokens,
        temperature: this.config.temperature,
      },
      request: {
        messages: backendMessages,
        tools: backendTools,
        maxTokens: this.config.maxTokens,
        temperature: this.config.temperature,
      },
    };

    // Use relative path - nginx will proxy to MCP server
    const response = await fetch('/api/ai/proxy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(proxyRequest),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AI proxy request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'AI proxy request failed');
    }

    // Convert backend response to frontend format
    return {
      message: {
        id: data.data.message.id || crypto.randomUUID(),
        role: data.data.message.role,
        content: data.data.message.content,
        timestamp: new Date(data.data.message.timestamp),
        toolCalls: data.data.message.toolCalls || [],
      },
      usage: data.data.usage,
    };
  }


  async streamChat(
    messages: ChatMessage[],
    onChunk: (chunk: string) => void,
    options: {
      tools?: any[];
      toolChoice?: string;
    } = {}
  ): Promise<void> {
    try {
      const request: ChatRequest = {
        messages: messages.map(msg => ({
          ...msg,
          content: msg.content,
        })),
        model: this.config.model,
        maxTokens: this.config.maxTokens,
        temperature: this.config.temperature,
        tools: options.tools,
        toolChoice: options.toolChoice,
      };

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: this.config.provider,
          config: this.config,
          request,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                onChunk(parsed.content);
              }
            } catch (e) {
              // Ignore JSON parse errors for malformed chunks
            }
          }
        }
      }
    } catch (error) {
      console.error('[AI] Stream chat failed:', error);
      throw error;
    }
  }

  // Provider-specific methods
  async getModels(): Promise<string[]> {
    try {
      const response = await this.api.get('/ai/models', {
        params: { provider: this.config.provider },
      });

      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get models');
      }

      return response.data.data || [];
    } catch (error) {
      console.error('[AI] Failed to get models:', error);
      // Return default models for each provider
      switch (this.config.provider) {
        case 'claude':
          return [
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-3-opus-20240229',
          ];
        case 'openai':
          return [
            'gpt-4-turbo-preview',
            'gpt-4',
            'gpt-3.5-turbo',
          ];
        case 'azure-openai':
          return [
            'gpt-4',
            'gpt-35-turbo',
          ];
        case 'gemini':
          return [
            'gemini-pro',
            'gemini-pro-vision',
          ];
        default:
          return [];
      }
    }
  }

  async validateConfig(config: AIConfig): Promise<boolean> {
    try {
      const response = await this.api.post('/ai/validate', {
        provider: config.provider,
        config,
      });

      return response.data.success;
    } catch (error) {
      console.error('[AI] Config validation failed:', error);
      return false;
    }
  }

  // Utility methods
  formatMessagesForProvider(messages: ChatMessage[]): any[] {
    switch (this.config.provider) {
      case 'claude':
        return messages
          .filter(msg => msg.role !== 'system') // Claude handles system messages differently
          .map(msg => ({
            role: msg.role === 'assistant' ? 'assistant' : 'user',
            content: msg.content,
          }));
      
      case 'openai':
      case 'azure-openai':
        return messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        }));
      
      case 'gemini':
        return messages
          .filter(msg => msg.role !== 'system') // Gemini doesn't support system messages
          .map(msg => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }],
          }));
      
      default:
        return messages;
    }
  }

  getProviderLimits(): {
    maxTokens: number;
    maxMessages: number;
    supportsTools: boolean;
    supportsStreaming: boolean;
  } {
    switch (this.config.provider) {
      case 'claude':
        return {
          maxTokens: 200000,
          maxMessages: 1000,
          supportsTools: true,
          supportsStreaming: true,
        };
      
      case 'openai':
        return {
          maxTokens: 128000,
          maxMessages: 1000,
          supportsTools: true,
          supportsStreaming: true,
        };
      
      case 'azure-openai':
        return {
          maxTokens: 128000,
          maxMessages: 1000,
          supportsTools: true,
          supportsStreaming: true,
        };
      
      case 'gemini':
        return {
          maxTokens: 32000,
          maxMessages: 1000,
          supportsTools: false,
          supportsStreaming: true,
        };
      
      default:
        return {
          maxTokens: 4000,
          maxMessages: 100,
          supportsTools: false,
          supportsStreaming: false,
        };
    }
  }
}

// Export a function to create AI client instances
export const createAIClient = (config: AIConfig): AIClient => {
  return new AIClient(config);
};

export default AIClient;