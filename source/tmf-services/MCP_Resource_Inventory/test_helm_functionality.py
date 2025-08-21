#!/usr/bin/env python3
"""
Quick test script to verify Helm integration is working properly.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_helm_functionality():
    """Test basic Helm functionality."""
    
    print("🧪 Testing Helm functionality...")
    
    try:
        from helm_api import HelmAPI
        
        helm = HelmAPI()
        
        # Test repository listing
        print("📋 Testing repository listing...")
        repos = await helm.list_repositories()
        print(f"✅ Found {len(repos)} repositories:")
        for repo in repos[:3]:  # Show first 3
            print(f"   - {repo.name}: {repo.url}")
        
        # Test chart search
        print("\n🔍 Testing chart search...")
        try:
            results = await helm.search_charts("productcatalog")
            print(f"✅ Search results: {len(results)} charts found")
            if results:
                print(f"   - Example: {results[0].get('name', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Search test: {e}")
        
        # Test release listing
        print("\n📦 Testing release listing...")
        try:
            releases = await helm.list_releases()
            print(f"✅ Found {len(releases)} releases")
            if releases:
                print(f"   - Example: {releases[0].name} ({releases[0].status})")
        except Exception as e:
            print(f"⚠️  Release listing: {e}")
        
        # Test ODA Component installation
        await test_oda_component_installation(helm)
        
        print("\n🎉 Helm functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Helm functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_oda_component_installation(helm):
    """Test installing and managing an ODA Component using Helm."""
    
    print("\n🚀 Testing ODA Component Installation...")
    
    chart_name = "oda-components/productcatalog"
    release_name = "test"
    namespace = "components"
    
    try:
        # Check if release already exists and clean up if needed
        print(f"🔍 Checking for existing release '{release_name}' in namespace '{namespace}'...")
        try:
            existing_releases = await helm.list_releases(namespace=namespace)
            existing_release = next((r for r in existing_releases if r.name == release_name), None)
            
            if existing_release:
                print(f"⚠️  Found existing release '{release_name}', cleaning up first...")
                await helm.uninstall_release(release_name, namespace=namespace)
                print(f"✅ Existing release uninstalled successfully")
                
                # Wait for cleanup to complete
                await asyncio.sleep(3)
        except Exception as e:
            print(f"ℹ️  No existing releases found or error checking: {e}")
          # Install the ODA Component
        print(f"📦 Installing ODA Component '{chart_name}' as release '{release_name}'...")
        install_result = await helm.install_chart(
            release_name=release_name,
            chart_name=chart_name,
            namespace=namespace,
            create_namespace=True,
            values={
                # ODA Component specific values can be added here
                "component": {
                    "name": "productcatalog-test",
                    "version": "v1beta3"
                }
            }
        )
        print(f"✅ ODA Component installed successfully: {install_result.get('name', release_name)}")
        
        # Verify installation by checking release status
        print(f"🔍 Verifying ODA Component installation...")
        await asyncio.sleep(2)  # Allow time for installation to process
        
        status = await helm.get_release_status(release_name, namespace=namespace)
        print(f"✅ Release status: {status.get('status', 'unknown')}")
        print(f"   - Revision: {status.get('revision', 'unknown')}")
        print(f"   - Namespace: {status.get('namespace', 'unknown')}")
        
        # List releases to confirm the ODA Component is present
        releases = await helm.list_releases(namespace=namespace)
        test_release = next((r for r in releases if r.name == release_name), None)
        
        if test_release:
            print(f"✅ ODA Component confirmed in Canvas:")
            print(f"   - Name: {test_release.name}")
            print(f"   - Status: {test_release.status}")
            print(f"   - Chart: {test_release.chart}")
            print(f"   - App Version: {getattr(test_release, 'app_version', 'N/A')}")
        else:
            print(f"⚠️  ODA Component not found in release list")
          # Test upgrade functionality
        print(f"\n🔄 Testing ODA Component upgrade...")
        try:
            upgrade_result = await helm.upgrade_chart(
                release_name=release_name,
                chart_name=chart_name,
                namespace=namespace,
                values={
                    "component": {
                        "name": "productcatalog-test-upgraded",
                        "version": "v1beta3"
                    }
                }
            )
            print(f"✅ ODA Component upgraded successfully")
            
            # Check new status
            updated_status = await helm.get_release_status(release_name, namespace=namespace)
            print(f"   - New revision: {updated_status.get('revision', 'unknown')}")
            
        except Exception as e:
            print(f"⚠️  Upgrade test failed: {e}")
        
        # Clean up the test installation
        print(f"\n🧹 Cleaning up test ODA Component...")
        await helm.uninstall_release(release_name, namespace=namespace)
        print(f"✅ Test ODA Component '{release_name}' removed from Canvas successfully")
        
        # Verify cleanup
        final_releases = await helm.list_releases(namespace=namespace)
        cleanup_confirmed = not any(r.name == release_name for r in final_releases)
        if cleanup_confirmed:
            print(f"✅ Cleanup verified - ODA Component no longer present in Canvas")
        else:
            print(f"⚠️  Cleanup verification failed - ODA Component may still be present")
        
    except Exception as e:
        print(f"❌ ODA Component installation test failed: {e}")
        # Attempt cleanup on failure
        try:
            print(f"🧹 Attempting cleanup after failure...")
            await helm.uninstall_release(release_name, namespace=namespace)
            print(f"✅ Emergency cleanup completed")
        except Exception as cleanup_error:
            print(f"⚠️  Emergency cleanup failed: {cleanup_error}")
        raise

async def main():
    """Main function."""
    success = await test_helm_functionality()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
