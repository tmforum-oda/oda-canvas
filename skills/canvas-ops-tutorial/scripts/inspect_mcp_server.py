"""Inspect an MCP server endpoint by initializing a session and listing tools, resources, and prompts.

Usage: python inspect_mcp_server.py <mcp-endpoint-url>

The script:
  1. Sends an MCP 'initialize' request (Streamable HTTP transport)
  2. Sends 'tools/list' to discover available tools
  3. Sends 'resources/list' to discover available resources
  4. Sends 'prompts/list' to discover available prompts
  5. Prints a structured summary

Requires: requests (pip install requests)

The endpoint URL should be the ExposedAPI URL for the MCP-type API,
e.g. https://localhost/pc1-productcatalogmanagement/mcp
"""
import json
import sys
import re

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)


def parse_sse_response(text):
    """Extract JSON data from an SSE text/event-stream response."""
    for line in text.strip().splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    # If it's not SSE, try parsing as plain JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def mcp_request(url, method, params, session_id=None):
    """Send a JSON-RPC request to the MCP server."""
    headers = {
        "Accept": "text/event-stream, application/json",
        "Content-Type": "application/json",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    payload = {
        "jsonrpc": "2.0",
        "id": method,
        "method": method,
        "params": params,
    }

    resp = requests.post(url, json=payload, headers=headers, verify=False, timeout=15)
    session_id_out = resp.headers.get("Mcp-Session-Id", session_id)
    parsed = parse_sse_response(resp.text)
    return parsed, session_id_out


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_mcp_server.py <mcp-endpoint-url>")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL format
    if not re.match(r'^https?://', url):
        print(f"ERROR: Invalid URL: {url}")
        sys.exit(1)

    print(f"Inspecting MCP server at: {url}\n")

    # Step 1: Initialize
    print("--- Initialize ---")
    init_result, session_id = mcp_request(url, "initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "canvas-inspector", "version": "1.0"},
    })

    if not init_result or "error" in init_result:
        error = init_result.get("error", {}) if init_result else {}
        print(f"  ERROR: Failed to initialize: {error.get('message', 'Unknown error')}")
        sys.exit(1)

    result = init_result.get("result", {})
    server_info = result.get("serverInfo", {})
    capabilities = result.get("capabilities", {})

    print(f"  Server:           {server_info.get('name', 'N/A')} v{server_info.get('version', 'N/A')}")
    print(f"  Protocol Version: {result.get('protocolVersion', 'N/A')}")
    print(f"  Session ID:       {session_id or 'N/A'}")
    print(f"  Capabilities:     {', '.join(capabilities.keys()) if capabilities else 'none'}")

    # Step 2: List tools
    if "tools" in capabilities:
        print("\n--- Tools ---")
        tools_result, _ = mcp_request(url, "tools/list", {}, session_id)
        if tools_result and "result" in tools_result:
            tools = tools_result["result"].get("tools", [])
            if tools:
                for t in tools:
                    name = t.get("name", "N/A")
                    desc = t.get("description", "").split("\n")[0][:80]
                    schema = t.get("inputSchema", {})
                    required = schema.get("required", [])
                    props = list(schema.get("properties", {}).keys())
                    print(f"  {name}")
                    print(f"    Description: {desc}")
                    if required:
                        print(f"    Required:    {', '.join(required)}")
                    if props:
                        optional = [p for p in props if p not in required]
                        if optional:
                            print(f"    Optional:    {', '.join(optional)}")
                print(f"\n  Total: {len(tools)} tool(s)")
            else:
                print("  No tools registered.")
        else:
            error = tools_result.get("error", {}) if tools_result else {}
            print(f"  ERROR: {error.get('message', 'Failed to list tools')}")
    else:
        print("\n--- Tools ---")
        print("  Not supported by this server.")

    # Step 3: List resources
    if "resources" in capabilities:
        print("\n--- Resources ---")
        res_result, _ = mcp_request(url, "resources/list", {}, session_id)
        if res_result and "result" in res_result:
            resources = res_result["result"].get("resources", [])
            if resources:
                for r in resources:
                    name = r.get("name", "N/A")
                    uri = r.get("uri", "N/A")
                    desc = r.get("description", "")
                    mime = r.get("mimeType", "")
                    print(f"  {name}")
                    print(f"    URI:  {uri}")
                    if desc:
                        print(f"    Desc: {desc[:80]}")
                    if mime:
                        print(f"    Type: {mime}")
                print(f"\n  Total: {len(resources)} resource(s)")
            else:
                print("  No resources registered.")
        else:
            error = res_result.get("error", {}) if res_result else {}
            print(f"  ERROR: {error.get('message', 'Failed to list resources')}")
    else:
        print("\n--- Resources ---")
        print("  Not supported by this server.")

    # Step 4: List prompts
    if "prompts" in capabilities:
        print("\n--- Prompts ---")
        prompts_result, _ = mcp_request(url, "prompts/list", {}, session_id)
        if prompts_result and "result" in prompts_result:
            prompts = prompts_result["result"].get("prompts", [])
            if prompts:
                for p in prompts:
                    name = p.get("name", "N/A")
                    desc = p.get("description", "")
                    args = p.get("arguments", [])
                    print(f"  {name}")
                    if desc:
                        print(f"    Description: {desc[:80]}")
                    if args:
                        arg_names = [a.get("name", "?") for a in args]
                        print(f"    Arguments:   {', '.join(arg_names)}")
                print(f"\n  Total: {len(prompts)} prompt(s)")
            else:
                print("  No prompts registered.")
        else:
            error = prompts_result.get("error", {}) if prompts_result else {}
            print(f"  ERROR: {error.get('message', 'Failed to list prompts')}")
    else:
        print("\n--- Prompts ---")
        print("  Not supported by this server.")


if __name__ == "__main__":
    main()
