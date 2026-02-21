#!/usr/bin/env python3
"""
Simple MCP client for testing PDB Management Operator
"""
import requests
import json
import sys
from typing import Dict, Any, Optional
import argparse


class PDBManagementMCPClient:
    def __init__(self, mcp_url: str = "http://localhost:8090/mcp"):
        self.mcp_url = mcp_url
        self.request_id = 1
        self.initialized = False
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        # Disable proxies for localhost connections
        self.session.proxies = {'http': None, 'https': None}
    
    def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an MCP JSON-RPC request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": str(self.request_id),
            "method": method,
            "params": params or {}
        }
        
        self.request_id += 1
        
        try:
            response = self.session.post(self.mcp_url, json=request_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {e}"}
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP session"""
        if self.initialized:
            return {"status": "already_initialized"}
        
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "pdb-management-python-client",
                "version": "1.0.0"
            }
        }
        
        result = self._make_request("initialize", params)
        if "result" in result:
            self.initialized = True
            print("✅ MCP session initialized successfully")
        else:
            print(f"❌ Failed to initialize: {result}")
        
        return result
    
    def list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools"""
        if not self.initialized:
            self.initialize()
        
        return self._make_request("tools/list")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        if not self.initialized:
            self.initialize()
        
        params = {
            "name": tool_name,
            "arguments": arguments or {}
        }
        
        return self._make_request("tools/call", params)
    
    def analyze_cluster(self, namespace: Optional[str] = None, detailed: bool = True) -> Dict[str, Any]:
        """Analyze cluster availability"""
        args = {"detailed": detailed}
        if namespace:
            args["namespace"] = namespace
        
        print(f"🔍 Analyzing cluster availability{' for namespace: ' + namespace if namespace else ''}...")
        result = self.call_tool("analyze_cluster_availability", args)
        
        if "result" in result and not result["result"].get("isError"):
            print("✅ Analysis completed successfully")
        else:
            print(f"❌ Analysis failed: {result}")
        
        return result
    
    def recommend_policies(self, namespace: Optional[str] = None, scope: str = "namespace") -> Dict[str, Any]:
        """Get policy recommendations"""
        args = {"scope": scope}
        if namespace:
            args["namespace"] = namespace
        
        print(f"💡 Getting policy recommendations{' for namespace: ' + namespace if namespace else ''}...")
        result = self.call_tool("recommend_policies", args)
        
        if "result" in result and not result["result"].get("isError"):
            print("✅ Recommendations generated successfully")
        else:
            print(f"❌ Recommendations failed: {result}")
        
        return result
    
    def create_policy(self, namespace: str, auto_detect: bool = True, **kwargs) -> Dict[str, Any]:
        """Create an availability policy with intelligent detection"""
        args = {
            "namespace": namespace,
            "autoDetect": auto_detect,
            **kwargs
        }
        
        print(f"🚀 Creating availability policy for namespace: {namespace}...")
        result = self.call_tool("create_availability_policy", args)
        
        if "result" in result and not result["result"].get("isError"):
            print("✅ Policy created successfully")
        else:
            print(f"❌ Policy creation failed: {result}")
        
        return result
    
    def analyze_workload_patterns(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Analyze workload patterns"""
        args = {}
        if namespace:
            args["namespace"] = namespace
        
        print(f"📊 Analyzing workload patterns{' for namespace: ' + namespace if namespace else ''}...")
        result = self.call_tool("analyze_workload_patterns", args)
        
        if "result" in result and not result["result"].get("isError"):
            print("✅ Workload analysis completed")
        else:
            print(f"❌ Workload analysis failed: {result}")
        
        return result
    
    def pretty_print_result(self, result: Dict[str, Any]):
        """Pretty print the result"""
        if "result" in result:
            content = result["result"].get("content", [])
            if isinstance(content, list) and content:
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        print("\n📋 Result:")
                        print("-" * 50)
                        try:
                            # Try to parse as JSON for better formatting
                            data = json.loads(item["text"])
                            print(json.dumps(data, indent=2))
                        except:
                            # Print as-is if not JSON
                            print(item["text"])
                        print("-" * 50)
            else:
                print(f"\n📋 Result: {content}")
        else:
            print(f"\n❌ Error: {result}")


def main():
    parser = argparse.ArgumentParser(description="PDB Management MCP Client")
    parser.add_argument("--url", default="http://localhost:8090/mcp", help="MCP server URL")
    parser.add_argument("--namespace", "-n", help="Kubernetes namespace to target")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List tools
    subparsers.add_parser("list", help="List available MCP tools")
    
    # Analyze cluster
    analyze_parser = subparsers.add_parser("analyze", help="Analyze cluster availability")
    analyze_parser.add_argument("--detailed", action="store_true", help="Include detailed analysis")
    
    # Recommend policies
    recommend_parser = subparsers.add_parser("recommend", help="Get policy recommendations")
    recommend_parser.add_argument("--scope", choices=["namespace", "cluster", "component"], 
                                default="namespace", help="Recommendation scope")
    
    # Create policy
    create_parser = subparsers.add_parser("create", help="Create availability policy")
    create_parser.add_argument("--name", help="Policy name")
    create_parser.add_argument("--class", dest="availabilityClass", 
                             choices=["non-critical", "standard", "high-availability", "mission-critical", "custom"],
                             help="Availability class")
    create_parser.add_argument("--auto-detect", action="store_true", default=True, help="Enable auto-detection")
    create_parser.add_argument("--create-multiple", action="store_true", help="Create multiple policies")
    
    # Workload patterns
    subparsers.add_parser("patterns", help="Analyze workload patterns")
    
    # Interactive mode
    subparsers.add_parser("interactive", help="Interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create client
    client = PDBManagementMCPClient(args.url)
    
    try:
        if args.command == "list":
            result = client.list_tools()
            if "result" in result:
                tools = result["result"].get("tools", [])
                print(f"\n🛠️  Available Tools ({len(tools)}):")
                print("=" * 60)
                for tool in tools:
                    print(f"📌 {tool['name']}")
                    print(f"   {tool['description']}")
                    print()
            else:
                client.pretty_print_result(result)
        
        elif args.command == "analyze":
            result = client.analyze_cluster(args.namespace, args.detailed)
            client.pretty_print_result(result)
        
        elif args.command == "recommend":
            result = client.recommend_policies(args.namespace, args.scope)
            client.pretty_print_result(result)
        
        elif args.command == "create":
            if not args.namespace:
                print("❌ --namespace is required for create command")
                return
            
            kwargs = {}
            if args.name:
                kwargs["name"] = args.name
            if args.availabilityClass:
                kwargs["availabilityClass"] = args.availabilityClass
            if args.create_multiple:
                kwargs["createMultiple"] = True
            
            result = client.create_policy(args.namespace, args.auto_detect, **kwargs)
            client.pretty_print_result(result)
        
        elif args.command == "patterns":
            result = client.analyze_workload_patterns(args.namespace)
            client.pretty_print_result(result)
        
        elif args.command == "interactive":
            interactive_mode(client)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def interactive_mode(client: PDBManagementMCPClient):
    """Interactive mode for testing"""
    print("\n🎯 Interactive MCP Client")
    print("Type 'help' for commands or 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command in ["quit", "exit", "q"]:
                break
            elif command == "help":
                print("""
Available commands:
  list           - List available tools
  analyze [ns]   - Analyze cluster (optional namespace)  
  recommend [ns] - Get policy recommendations
  patterns [ns]  - Analyze workload patterns
  create <ns>    - Create policy for namespace
  help           - Show this help
  quit           - Exit interactive mode
""")
            elif command == "list":
                result = client.list_tools()
                if "result" in result:
                    tools = result["result"].get("tools", [])
                    for tool in tools:
                        print(f"• {tool['name']}: {tool['description']}")
                
            elif command.startswith("analyze"):
                parts = command.split()
                namespace = parts[1] if len(parts) > 1 else None
                result = client.analyze_cluster(namespace)
                client.pretty_print_result(result)
            
            elif command.startswith("recommend"):
                parts = command.split()
                namespace = parts[1] if len(parts) > 1 else None
                result = client.recommend_policies(namespace)
                client.pretty_print_result(result)
            
            elif command.startswith("patterns"):
                parts = command.split()
                namespace = parts[1] if len(parts) > 1 else None
                result = client.analyze_workload_patterns(namespace)
                client.pretty_print_result(result)
            
            elif command.startswith("create"):
                parts = command.split()
                if len(parts) < 2:
                    print("❌ Usage: create <namespace>")
                    continue
                namespace = parts[1]
                result = client.create_policy(namespace)
                client.pretty_print_result(result)
            
            else:
                print(f"❌ Unknown command: {command}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()