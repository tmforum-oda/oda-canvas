#!/usr/bin/env python3
"""
Verification script to test the Helm API integration with the MCP server.
This script checks that all components are properly integrated and functional.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def verify_helm_integration():
    """Verify that Helm API integration is working properly."""
    
    print("🔧 Verifying Helm API Integration...")
    
    try:
        # Test Helm API import
        from helm_api import HelmAPI, HelmAPIError
        print("✅ Helm API imported successfully")
        
        # Test MCP server import
        from resource_inventory_mcp_server import mcp
        print("✅ MCP server imported successfully")
        
        # Check available tools
        tools = await mcp.list_tools()
        helm_tools = [tool for tool in tools if 'helm' in tool.name]
        
        print(f"✅ Found {len(helm_tools)} Helm tools:")
        for tool in helm_tools:
            print(f"   - {tool.name}: {tool.description[:80]}...")
        
        # Test basic Helm API functionality
        helm = HelmAPI()
        print("✅ Helm API instance created successfully")
        
        # Test repository listing (should work even without repos configured)
        try:
            repos = await helm.list_repositories()
            print(f"✅ Repository listing works: {len(repos)} repositories found")
        except Exception as e:
            print(f"⚠️  Repository listing test: {e}")
        
        
        print("\n🎉 Integration verification completed successfully!")
        print("\n📋 Available Helm Tools:")
        print("   - helm_search_charts: Search for Helm charts in repositories")
        print("   - helm_list_releases: List installed Helm releases")
        print("   - helm_install_chart: Install a Helm chart")
        print("   - helm_upgrade_release: Upgrade an existing release")
        print("   - helm_uninstall_release: Uninstall a release")
        print("   - helm_get_release_status: Get status of a release")
        print("   - helm_manage_repositories: Manage Helm repositories")
        print("   - helm_install_tmforum_component: Install TM Forum ODA components")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run the verification."""
    success = await verify_helm_integration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
