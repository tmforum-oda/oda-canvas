#!/usr/bin/env python3
"""
Command-line interface for the Custom-Resource Collector.
Provides commands for running, testing, and managing the collector.
"""

import argparse
import asyncio
import sys
import logging
from pathlib import Path

import main
from config import load_config
from kubernetes_client import KubernetesClient
from registry_client import ComponentRegistryClient


def setup_cli_logging(level: str = "INFO"):
    """Setup logging for CLI"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


async def test_connections(args):
    """Test connections to Kubernetes and Component Registry"""
    print("Testing connections...")
    
    config = load_config()
    
    # Test Kubernetes connection
    print("Testing Kubernetes connection...")
    try:
        k8s_client = KubernetesClient(config.kubernetes)
        if k8s_client.test_connection():
            print("✓ Kubernetes connection successful")
            
            # Check for ODA Component CRD
            if k8s_client.check_crd_exists(
                group=config.component_group,
                version=config.component_version,
                plural=config.component_plural
            ):
                print("✓ ODA Component CRD found")
            else:
                print("⚠ ODA Component CRD not found")
        else:
            print("✗ Kubernetes connection failed")
            return False
    except Exception as e:
        print(f"✗ Kubernetes connection error: {e}")
        return False
    finally:
        if 'k8s_client' in locals():
            k8s_client.close()
    
    # Test Component Registry connection
    print("Testing Component Registry connection...")
    try:
        registry_client = ComponentRegistryClient(config.component_registry)
        if registry_client.health_check():
            print("✓ Component Registry connection successful")
            
            # Get stats
            stats = registry_client.get_stats()
            if stats:
                print(f"  Registry stats: {stats}")
        else:
            print("✗ Component Registry connection failed")
            return False
    except Exception as e:
        print(f"✗ Component Registry connection error: {e}")
        return False
    
    print("All connection tests passed!")
    return True


async def list_components(args):
    """List ODA Components in Kubernetes"""
    print("Listing ODA Components...")
    
    config = load_config()
    
    try:
        k8s_client = KubernetesClient(config.kubernetes)
        components = k8s_client.list_oda_components(
            namespace=args.namespace or config.kubernetes.namespace,
            group=config.component_group,
            version=config.component_version,
            plural=config.component_plural
        )
        
        if not components:
            print("No ODA Components found")
            return
        
        print(f"Found {len(components)} ODA Components:")
        print()
        
        for component in components:
            name = component.metadata["name"]
            namespace = component.metadata.get("namespace", "default")
            version = component.spec.version
            api_count = len(component.spec.coreFunction.exposedAPIs or [])
            
            print(f"  Name: {name}")
            print(f"  Namespace: {namespace}")
            print(f"  Version: {version}")
            print(f"  Exposed APIs: {api_count}")
            
            if component.spec.coreFunction.exposedAPIs:
                for api in component.spec.coreFunction.exposedAPIs:
                    print(f"    - {api.name}: {api.specification}")
            print()
            
    except Exception as e:
        print(f"Error listing components: {e}")
        return False
    finally:
        if 'k8s_client' in locals():
            k8s_client.close()


async def sync_component(args):
    """Manually sync a specific component"""
    print(f"Syncing component: {args.component_name}")
    
    config = load_config()
    
    try:
        # Get component from Kubernetes
        k8s_client = KubernetesClient(config.kubernetes)
        component = k8s_client.get_oda_component(
            name=args.component_name,
            namespace=args.namespace or config.kubernetes.namespace,
            group=config.component_group,
            version=config.component_version,
            plural=config.component_plural
        )
        
        if not component:
            print(f"Component '{args.component_name}' not found")
            return False
        
        # Initialize registry client and synchronizer
        registry_client = ComponentRegistryClient(config.component_registry)
        
        from synchronizer import ComponentSynchronizer
        synchronizer = ComponentSynchronizer(config, k8s_client, registry_client)
        
        # Perform sync
        result = await synchronizer._sync_component_to_registry(component)
        
        if result.success:
            print(f"✓ Component '{args.component_name}' synced successfully")
            if result.registry_id:
                print(f"  Registry ID: {result.registry_id}")
        else:
            print(f"✗ Failed to sync component '{args.component_name}': {result.error_message}")
            return False
            
    except Exception as e:
        print(f"Error syncing component: {e}")
        return False
    finally:
        if 'k8s_client' in locals():
            k8s_client.close()


async def run_collector(args):
    """Run the collector application"""
    setup_cli_logging(args.log_level)
    await main.main()


def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Custom-Resource Collector for ODA Canvas Components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                                    # Run the collector
  %(prog)s test                                   # Test connections
  %(prog)s list --namespace oda-components        # List components
  %(prog)s sync my-component --namespace default  # Sync specific component
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="Custom-Resource Collector 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the collector")
    run_parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
        default="INFO",
        help="Set logging level"
    )
    run_parser.set_defaults(func=run_collector)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test connections")
    test_parser.set_defaults(func=test_connections)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List ODA Components")
    list_parser.add_argument(
        "--namespace", 
        help="Kubernetes namespace (default: from config)"
    )
    list_parser.set_defaults(func=list_components)
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Manually sync a component")
    sync_parser.add_argument(
        "component_name", 
        help="Name of the component to sync"
    )
    sync_parser.add_argument(
        "--namespace", 
        help="Kubernetes namespace (default: from config)"
    )
    sync_parser.set_defaults(func=sync_component)
    
    return parser


async def cli_main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        result = await args.func(args)
        if result is False:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    
    from dotenv import load_dotenv
    load_dotenv()  # take environment variables
    
    if len(sys.argv) == 1:
#        sys.argv = ["cli.py", "list", "--namespace", "components"]
        sys.argv = ["cli.py", "sync", "demo-b-productcatalogmanagement", "--namespace", "components"]

    asyncio.run(cli_main())
