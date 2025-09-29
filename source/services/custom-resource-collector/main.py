"""
Main application entry point for the Custom-Resource Collector.
Orchestrates all components and handles application lifecycle.
"""

import logging
import asyncio
import signal
import sys
from typing import List

from config import load_config, CollectorConfig
from kubernetes_client import KubernetesClient, ComponentWatcher
from registry_client import ComponentRegistryClient
from synchronizer import ComponentSynchronizer
from monitoring import MonitoringManager


logger = logging.getLogger(__name__)


class CustomResourceCollector:
    """Main Custom-Resource Collector application"""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Initialize components
        self.k8s_client = None
        self.registry_client = None
        self.synchronizer = None
        self.watcher = None
        self.monitoring = None
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level.upper()),
            format=self.config.logging.format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('collector.log')
            ]
        )
        
        # Set specific logger levels
        logging.getLogger('kubernetes').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Custom-Resource Collector")
        
        try:
            # Initialize Kubernetes client
            logger.info("Initializing Kubernetes client...")
            self.k8s_client = KubernetesClient(self.config.kubernetes)
            
            # Test Kubernetes connection
            if not self.k8s_client.test_connection():
                raise RuntimeError("Kubernetes connection test failed")
            
            # Check if ODA Component CRD exists
            if not self.k8s_client.check_crd_exists(
                group=self.config.component_group,
                version=self.config.component_version,
                plural=self.config.component_plural
            ):
                logger.warning(f"ODA Component CRD not found. Continuing anyway...")
            
            # Initialize Component Registry client
            logger.info("Initializing Component Registry client...")
            self.registry_client = ComponentRegistryClient(self.config.component_registry)
            
            # Test registry connection
            if not self.registry_client.health_check():
                raise RuntimeError("Component Registry health check failed")
            
            # Initialize synchronizer
            logger.info("Initializing component synchronizer...")
            self.synchronizer = ComponentSynchronizer(
                self.config, self.k8s_client, self.registry_client
            )
            
            # Initialize component watcher
            logger.info("Initializing component watcher...")
            self.watcher = ComponentWatcher(self.k8s_client)
            self.watcher.add_event_handler(self.synchronizer.handle_component_event)
            
            # Initialize monitoring
            logger.info("Initializing monitoring...")
            self.monitoring = MonitoringManager(self.config.monitoring)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def start(self):
        """Start the collector application"""
        logger.info("Starting Custom-Resource Collector")
        
        try:
            # Start monitoring
            await self.monitoring.start()
            
            # Update health status
            self.monitoring.health.update_kubernetes_health(True)
            self.monitoring.health.update_registry_health(True)
            
            # Perform initial full synchronization
            logger.info("Performing initial full synchronization...")
            await self.synchronizer.perform_full_sync()
            
            # Start background processing tasks
            logger.info("Starting background processing tasks...")
            sync_tasks = await self.synchronizer.start_processing()
            self.tasks.extend(sync_tasks)
            
            # Start component watcher
            logger.info("Starting component watcher...")
            watch_task = asyncio.create_task(
                self.watcher.start_watching(namespace=self.config.kubernetes.namespace)
            )
            self.tasks.append(watch_task)
            
            # Start status reporting task
            status_task = asyncio.create_task(self._status_reporter())
            self.tasks.append(status_task)
            
            self.running = True
            logger.info("Custom-Resource Collector started successfully")
            
            # Log configuration summary
            self._log_configuration_summary()
            
        except Exception as e:
            logger.error(f"Failed to start collector: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the collector application"""
        logger.info("Stopping Custom-Resource Collector")
        
        self.running = False
        
        # Cancel all background tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks, return_exceptions=True),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete within timeout")
        
        # Stop monitoring
        if self.monitoring:
            await self.monitoring.stop()
        
        # Close clients
        if self.k8s_client:
            self.k8s_client.close()
        
        logger.info("Custom-Resource Collector stopped")
    
    async def _status_reporter(self):
        """Periodic status reporting task"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                if self.synchronizer:
                    status = self.synchronizer.get_sync_status()
                    
                    # Update monitoring
                    if self.monitoring:
                        self.monitoring.update_from_synchronizer(status)
                    
                    # Log status summary
                    logger.info(
                        f"Status: {status['processed_components']}/{status['total_components']} "
                        f"components synced, {status['failed_components']} failed, "
                        f"queue size: {status['queue_size']}"
                    )
                    
                    # Update health based on sync status
                    if self.monitoring:
                        if status['failed_components'] > 0:
                            self.monitoring.health.record_error()
                        else:
                            self.monitoring.health.reset_error_count()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")
                if self.monitoring:
                    self.monitoring.health.record_error()
    
    def _log_configuration_summary(self):
        """Log configuration summary"""
        logger.info("Configuration Summary:")
        logger.info(f"  Kubernetes namespace: {self.config.kubernetes.namespace}")
        logger.info(f"  ODA Component group: {self.config.component_group}")
        logger.info(f"  ODA Component version: {self.config.component_version}")
        logger.info(f"  Component Registry URL: {self.config.component_registry.base_url}")
        logger.info(f"  Sync interval: {self.config.sync_interval}s")
        logger.info(f"  Batch size: {self.config.batch_size}")
        logger.info(f"  Monitoring enabled: {self.config.monitoring.enabled}")
        if self.config.monitoring.enabled:
            logger.info(f"  Metrics port: {self.config.monitoring.port}")
    
    async def run_forever(self):
        """Run the collector until interrupted"""
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Wait for all tasks to complete
            while self.running:
                await asyncio.sleep(1)
                
                # Check if any critical task has failed
                for task in self.tasks:
                    if task.done() and not task.cancelled():
                        try:
                            task.result()
                        except Exception as e:
                            logger.error(f"Critical task failed: {e}")
                            self.running = False
                            break
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self.stop()


async def main():
    """Main application entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Create and initialize collector
        collector = CustomResourceCollector(config)
        await collector.initialize()
        
        # Start collector
        await collector.start()
        
        # Run forever
        await collector.run_forever()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())