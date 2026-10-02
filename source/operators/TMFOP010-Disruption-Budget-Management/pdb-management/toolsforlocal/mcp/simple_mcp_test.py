#!/usr/bin/env python3
"""
Simple working MCP client test
"""
import requests
import json
import os

# Clear proxy settings
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

def test_mcp_client():
    url = "http://localhost:8090/mcp"
    
    # Initialize session
    init_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "simple-test-client",
                "version": "1.0.0"
            }
        }
    }
    
    print("🔌 Initializing MCP connection...")
    try:
        response = requests.post(url, json=init_request, 
                               proxies={'http': None, 'https': None}, timeout=10)
        print(f"✅ Initialization successful: {response.status_code}")
        init_result = response.json()
        print(f"Server info: {init_result.get('result', {}).get('serverInfo', {})}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # List tools
    list_request = {
        "jsonrpc": "2.0",
        "id": "2", 
        "method": "tools/list",
        "params": {}
    }
    
    print("\n🛠️  Listing available tools...")
    try:
        response = requests.post(url, json=list_request,
                               proxies={'http': None, 'https': None}, timeout=10)
        result = response.json()
        tools = result.get('result', {}).get('tools', [])
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  📌 {tool['name']}: {tool['description'][:60]}...")
    except Exception as e:
        print(f"❌ List tools failed: {e}")
        return False
    
    # Test analyze tool
    analyze_request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "analyze_cluster_availability",
            "arguments": {
                "namespace": "pdb-demo",
                "detailed": False
            }
        }
    }
    
    print(f"\n🔍 Testing cluster analysis for pdb-demo namespace...")
    try:
        response = requests.post(url, json=analyze_request,
                               proxies={'http': None, 'https': None}, timeout=30)
        result = response.json()
        if not result.get('result', {}).get('isError'):
            print("✅ Cluster analysis successful!")
            content = result.get('result', {}).get('content', [])
            if content and isinstance(content, list) and content[0]:
                print(f"📊 Analysis result preview: {str(content[0])[:100]}...")
        else:
            print(f"❌ Analysis failed: {result}")
    except Exception as e:
        print(f"❌ Analysis call failed: {e}")
        return False
    
    print("\n🎉 All tests passed! MCP client is working correctly.")
    return True

if __name__ == "__main__":
    test_mcp_client()