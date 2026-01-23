#!/usr/bin/env python3
"""
Claude API integration with PDB Management MCP Server
"""
import os
import json
import requests
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

class ClaudeMCPIntegration:
    def __init__(self, 
                 claude_api_key: str = None,
                 mcp_url: str = "http://localhost:8090/mcp"):
        """
        Initialize Claude API with MCP integration
        
        Args:
            claude_api_key: Your Claude API key (or set ANTHROPIC_API_KEY env var)
            mcp_url: MCP server URL (default: localhost with port-forward)
        """
        self.claude_api_key = claude_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.claude_api_key:
            raise ValueError("Claude API key required. Set ANTHROPIC_API_KEY or pass claude_api_key")
        
        self.client = Anthropic(api_key=self.claude_api_key)
        self.mcp_url = mcp_url
        self.mcp_initialized = False
        self.mcp_tools = []
        
        # Initialize MCP connection
        self._initialize_mcp()
        self._load_mcp_tools()
    
    def _initialize_mcp(self):
        """Initialize MCP server connection"""
        try:
            response = requests.post(self.mcp_url, 
                json={
                    "jsonrpc": "2.0",
                    "id": "init",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "clientInfo": {
                            "name": "claude-api-client",
                            "version": "1.0.0"
                        }
                    }
                },
                proxies={'http': None, 'https': None},
                timeout=10
            )
            
            if response.status_code == 200:
                self.mcp_initialized = True
                print(f"MCP server initialized: {response.json().get('result', {}).get('serverInfo', {})}")
            else:
                print(f"Failed to initialize MCP: {response.status_code}")
        except Exception as e:
            print(f"Error initializing MCP: {e}")
    
    def _load_mcp_tools(self):
        """Load available MCP tools and convert to Claude tool format"""
        if not self.mcp_initialized:
            return
        
        try:
            response = requests.post(self.mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "list",
                    "method": "tools/list",
                    "params": {}
                },
                proxies={'http': None, 'https': None},
                timeout=10
            )
            
            if response.status_code == 200:
                tools = response.json().get('result', {}).get('tools', [])
                self.mcp_tools = self._convert_to_claude_tools(tools)
                print(f"Loaded {len(self.mcp_tools)} MCP tools")
            else:
                print(f"Failed to load MCP tools: {response.status_code}")
        except Exception as e:
            print(f"Error loading MCP tools: {e}")
    
    def _convert_to_claude_tools(self, mcp_tools: List[Dict]) -> List[Dict]:
        """Convert MCP tool definitions to Claude tool format"""
        claude_tools = []
        
        for tool in mcp_tools:
            # Convert MCP tool schema to Claude format
            claude_tool = {
                "name": tool['name'],
                "description": tool['description'],
                "input_schema": tool.get('inputSchema', {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result"""
        if not self.mcp_initialized:
            return {"error": "MCP not initialized"}
        
        try:
            response = requests.post(self.mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": f"call-{tool_name}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                },
                proxies={'http': None, 'https': None},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                else:
                    return {"error": f"No result in response: {result}"}
            else:
                return {"error": f"MCP call failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error calling MCP tool: {e}"}
    
    def chat_with_tools(self, 
                        user_message: str,
                        system_prompt: str = None,
                        max_tokens: int = 1024) -> str:
        """
        Send a message to Claude with MCP tools available
        
        Args:
            user_message: The user's message
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
        
        Returns:
            Claude's response as a string
        """
        if not system_prompt:
            system_prompt = """You are an AI assistant with access to Kubernetes PDB management tools.
You can analyze cluster availability, recommend policies, and create Pod Disruption Budgets.
Use the available tools to help the user manage their Kubernetes cluster effectively."""
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Send message to Claude with tools
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
                tools=self.mcp_tools
            )
            
            # Process Claude's response
            assistant_message = ""
            
            for content in response.content:
                if content.type == "text":
                    assistant_message += content.text
                elif content.type == "tool_use":
                    # Claude wants to use a tool
                    tool_name = content.name
                    tool_args = content.input
                    
                    print(f"\nClaude is calling tool: {tool_name}")
                    print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                    
                    # Call the MCP tool
                    tool_result = self._call_mcp_tool(tool_name, tool_args)
                    
                    # Send tool result back to Claude
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": str(tool_result)
                        }]
                    })
                    
                    # Get Claude's final response with tool results
                    final_response = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=messages,
                        tools=self.mcp_tools
                    )
                    
                    for final_content in final_response.content:
                        if final_content.type == "text":
                            assistant_message += "\n" + final_content.text
            
            return assistant_message
            
        except Exception as e:
            return f"Error communicating with Claude: {e}"
    
    def analyze_namespace(self, namespace: str = "default") -> str:
        """
        Ask Claude to analyze a specific namespace
        """
        prompt = f"Analyze the availability status of the {namespace} namespace and provide recommendations."
        return self.chat_with_tools(prompt)
    
    def recommend_policies(self, namespace: str = "default") -> str:
        """
        Ask Claude to recommend policies for a namespace
        """
        prompt = f"What availability policies do you recommend for the {namespace} namespace? Analyze the current deployments and suggest optimal configurations."
        return self.chat_with_tools(prompt)
    
    def create_policy_interactive(self, namespace: str = "default") -> str:
        """
        Interactively create a policy with Claude's help
        """
        prompt = f"""I need to create availability policies for the {namespace} namespace.
        First analyze what's there, then recommend the best approach, but don't create anything yet.
        Just tell me what you would recommend."""
        return self.chat_with_tools(prompt)


def main():
    """Example usage"""
    import sys
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set ANTHROPIC_API_KEY environment variable")
        print("Export it with: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Ensure port-forward is running
    print("Make sure port-forward is running:")
    print("kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090")
    print("-" * 50)
    
    # Create integration
    try:
        integration = ClaudeMCPIntegration()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        print("\nTroubleshooting:")
        print("1. Check port-forward is running")
        print("2. Check MCP server is healthy: curl http://localhost:8090/health")
        print("3. Verify ANTHROPIC_API_KEY is set correctly")
        sys.exit(1)
    
    # Interactive mode
    print("\nClaude + MCP Integration Ready!")
    print("Commands:")
    print("  analyze <namespace> - Analyze namespace availability")
    print("  recommend <namespace> - Get policy recommendations")
    print("  chat - Free-form chat with Claude")
    print("  quit - Exit")
    print("-" * 50)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.startswith("quit") or command == "exit":
                break
            
            elif command.startswith("analyze"):
                parts = command.split()
                namespace = parts[1] if len(parts) > 1 else "default"
                print(f"\nAnalyzing {namespace} namespace...")
                response = integration.analyze_namespace(namespace)
                print(response)
            
            elif command.startswith("recommend"):
                parts = command.split()
                namespace = parts[1] if len(parts) > 1 else "default"
                print(f"\nGetting recommendations for {namespace} namespace...")
                response = integration.recommend_policies(namespace)
                print(response)
            
            elif command == "chat":
                print("Enter your message (or 'back' to return):")
                message = input("Message: ").strip()
                if message and message != "back":
                    response = integration.chat_with_tools(message)
                    print(f"\nClaude: {response}")
            
            else:
                # Send as free-form message to Claude
                if command:
                    response = integration.chat_with_tools(command)
                    print(f"\nClaude: {response}")
                else:
                    print("Type a command or message")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()