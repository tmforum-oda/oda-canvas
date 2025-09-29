#!/usr/bin/env python3
"""
Simple start script for the Custom-Resource Collector.
This bypasses import issues by creating a minimal test version.
"""

import os
import sys
import requests
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_component_registry():
    """Test connection to the Component Registry microservice"""
    registry_url = os.getenv("COMPONENT_REGISTRY_URL", "https://compreg.ihc-dt.cluster-2.de")
    
    try:
        logger.info(f"Testing connection to Component Registry at {registry_url}")
        
        # Test health endpoint
        response = requests.get(f"{registry_url}/health", timeout=10)
        response.raise_for_status()
        
        health_data = response.json()
        logger.info(f"✓ Component Registry is healthy: {health_data}")
        
        # Test stats endpoint
        response = requests.get(f"{registry_url}/stats", timeout=10)
        response.raise_for_status()
        
        stats_data = response.json()
        logger.info(f"✓ Registry statistics: {stats_data}")
        
        # Test labels endpoint
        response = requests.get(f"{registry_url}/labels/", timeout=10)
        response.raise_for_status()
        
        labels_data = response.json()
        logger.info(f"✓ Found {len(labels_data)} labels in registry")
        
        # Test registries endpoint
        response = requests.get(f"{registry_url}/registries/", timeout=10)
        response.raise_for_status()
        
        registries_data = response.json()
        logger.info(f"✓ Found {len(registries_data)} registries")
        
        # Test components endpoint
        response = requests.get(f"{registry_url}/components/", timeout=10)
        response.raise_for_status()
        
        components_data = response.json()
        logger.info(f"✓ Found {len(components_data)} components")
        
        # Test exposed APIs endpoint
        response = requests.get(f"{registry_url}/exposed-apis/", timeout=10)
        response.raise_for_status()
        
        apis_data = response.json()
        logger.info(f"✓ Found {len(apis_data)} exposed APIs")
        
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Cannot connect to Component Registry at {registry_url}")
        logger.error("  Make sure the Component Registry microservice is running")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ Timeout connecting to Component Registry at {registry_url}")
        return False
    except Exception as e:
        logger.error(f"✗ Error testing Component Registry: {e}")
        return False


def k8s_load_config(proxy=True):
    import kubernetes
    if kubernetes.client.Configuration._default:
        return
    try:
        kubernetes.config.load_incluster_config()
        print("loaded incluster config")
    except kubernetes.config.ConfigException:
        # try:
        #    kube_config_file = "~/.kube/config-vps5"
        #    kubernetes.config.load_kube_config(config_file=kube_config_file)
        # except kubernetes.config.ConfigException:
        try:
            kubernetes.config.load_kube_config()
            print("loaded default config")
        except kubernetes.config.ConfigException:
            raise Exception("Could not configure kubernetes python client")
        if proxy:
            proxy = os.getenv("HTTPS_PROXY", "http://sia-lb.telekom.de:8080")
            kubernetes.client.Configuration._default.proxy = proxy
            print(f"set proxy to {proxy}")


def test_kubernetes():
    """Test connection to Kubernetes cluster"""
    try:
        from kubernetes import client, config
        
        logger.info("Testing Kubernetes connection...")
        
        # Try to load kube config
        try:
            
            k8s_load_config(proxy=True)
            # config.load_kube_config()
            logger.info("✓ Loaded kubeconfig from file")
        except:
            try:
                config.load_incluster_config()
                logger.info("✓ Loaded in-cluster config")
            except:
                logger.error("✗ Failed to load Kubernetes configuration")
                return False
        
        # Test API connection
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace(limit=1)
        logger.info("✓ Successfully connected to Kubernetes API")
        
        # Check for ODA Component CRD
        try:
            extensions_v1 = client.ApiextensionsV1Api()
            crd_name = "components.oda.tmforum.org"
            crd = extensions_v1.read_custom_resource_definition(name=crd_name)
            logger.info(f"✓ Found ODA Component CRD: {crd_name}")
        except client.rest.ApiException as e:
            if e.status == 404:
                logger.warning("⚠ ODA Component CRD not found - will monitor anyway")
            else:
                logger.error(f"✗ Error checking for CRD: {e}")
        
        return True
        
    except ImportError:
        logger.error("✗ Kubernetes Python client not installed")
        logger.error("  Install with: pip install kubernetes")
        return False
    except Exception as e:
        logger.error(f"✗ Error testing Kubernetes: {e}")
        return False

def simulate_collector():
    """Simulate the Custom-Resource Collector functionality"""
    logger.info("🚀 Starting Custom-Resource Collector simulation...")
    
    # Test connections
    if not test_component_registry():
        logger.error("Failed to connect to Component Registry - stopping")
        return False
    
    if not test_kubernetes():
        logger.error("Failed to connect to Kubernetes - stopping")
        return False
    
    logger.info("✅ All connection tests passed!")
    
    # Simulate monitoring
    logger.info("🔍 Simulating ODA Component monitoring...")
    logger.info("  - Watching for ODA Component Custom Resources")
    logger.info("  - Monitoring namespace: default")
    logger.info("  - API Group: oda.tmforum.org/v1beta3")
    logger.info("  - Resource: components")
    
    # Simulate sync operations
    logger.info("🔄 Simulating synchronization operations...")
    logger.info("  - Processing component events (ADDED, MODIFIED, DELETED)")
    logger.info("  - Syncing components with Component Registry")
    logger.info("  - Creating labels and exposed APIs")
    logger.info("  - Updating component status")
    
    # Simulate metrics
    logger.info("📊 Simulating metrics collection...")
    logger.info("  - Prometheus metrics available on port 8080")
    logger.info("  - Health checks enabled")
    logger.info("  - Component sync statistics tracked")
    
    logger.info("✅ Custom-Resource Collector simulation running successfully!")
    logger.info("💡 To run the full collector, fix the Python import issues and use:")
    logger.info("   python cli.py run")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Custom-Resource Collector for ODA Canvas")
    print("=" * 60)
    
    if simulate_collector():
        print("\n🎉 Collector simulation completed successfully!")
        print("\nNext steps:")
        print("1. Ensure ODA Component CRDs are installed in Kubernetes")
        print("2. Deploy ODA Components to monitor")
        print("3. Fix Python import issues for full functionality")
        print("4. Run: python cli.py run")
    else:
        print("\n❌ Collector simulation failed!")
        print("Check the error messages above and fix connectivity issues.")
        sys.exit(1)