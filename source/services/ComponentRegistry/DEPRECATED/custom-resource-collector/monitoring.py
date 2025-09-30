"""
Monitoring and metrics for the Custom-Resource Collector.
Provides Prometheus metrics and health checks.
"""

import logging
import time
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
import asyncio
from datetime import datetime

from config import MonitoringConfig
from models import ComponentCollectorMetrics


logger = logging.getLogger(__name__)


class MetricsCollector:
    """Prometheus metrics collector for the Custom-Resource Collector"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.enabled = config.enabled
        
        if self.enabled:
            self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Component metrics
        self.components_total = Counter(
            'oda_collector_components_total',
            'Total number of ODA Components processed',
            ['status']  # success, failed
        )
        
        self.components_current = Gauge(
            'oda_collector_components_current',
            'Current number of ODA Components being monitored'
        )
        
        self.component_sync_duration = Histogram(
            'oda_collector_component_sync_duration_seconds',
            'Time taken to sync a component',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        # API metrics
        self.apis_total = Counter(
            'oda_collector_apis_total',
            'Total number of Exposed APIs processed',
            ['status']  # success, failed
        )
        
        self.apis_current = Gauge(
            'oda_collector_apis_current',
            'Current number of Exposed APIs being monitored'
        )
        
        # Label metrics
        self.labels_created = Counter(
            'oda_collector_labels_created_total',
            'Total number of labels created in registry'
        )
        
        # Kubernetes metrics
        self.kubernetes_events = Counter(
            'oda_collector_kubernetes_events_total',
            'Total number of Kubernetes events processed',
            ['event_type']  # ADDED, MODIFIED, DELETED
        )
        
        self.kubernetes_watch_errors = Counter(
            'oda_collector_kubernetes_watch_errors_total',
            'Total number of Kubernetes watch errors'
        )
        
        # Registry API metrics
        self.registry_api_calls = Counter(
            'oda_collector_registry_api_calls_total',
            'Total number of Component Registry API calls',
            ['method', 'endpoint', 'status']
        )
        
        self.registry_api_duration = Histogram(
            'oda_collector_registry_api_duration_seconds',
            'Duration of Component Registry API calls',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Sync metrics
        self.full_sync_duration = Histogram(
            'oda_collector_full_sync_duration_seconds',
            'Time taken for full synchronization',
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        )
        
        self.sync_queue_size = Gauge(
            'oda_collector_sync_queue_size',
            'Current size of the synchronization queue'
        )
        
        self.last_sync_timestamp = Gauge(
            'oda_collector_last_sync_timestamp',
            'Timestamp of last successful full sync'
        )
        
        # Health metrics
        self.collector_up = Gauge(
            'oda_collector_up',
            'Whether the collector is running (1) or not (0)'
        )
        
        self.collector_info = Info(
            'oda_collector_info',
            'Information about the collector'
        )
        
        # Set initial values
        self.collector_up.set(1)
        self.collector_info.info({
            'version': '1.0.0',
            'component': 'custom-resource-collector'
        })
        
        logger.info("Prometheus metrics initialized")
    
    def record_component_sync(self, success: bool, duration: float = None):
        """Record component synchronization metrics"""
        if not self.enabled:
            return
            
        status = 'success' if success else 'failed'
        self.components_total.labels(status=status).inc()
        
        if duration is not None:
            self.component_sync_duration.observe(duration)
    
    def record_api_sync(self, success: bool):
        """Record API synchronization metrics"""
        if not self.enabled:
            return
            
        status = 'success' if success else 'failed'
        self.apis_total.labels(status=status).inc()
    
    def record_kubernetes_event(self, event_type: str):
        """Record Kubernetes event metrics"""
        if not self.enabled:
            return
            
        self.kubernetes_events.labels(event_type=event_type).inc()
    
    def record_registry_api_call(self, method: str, endpoint: str, status: str, duration: float):
        """Record Component Registry API call metrics"""
        if not self.enabled:
            return
            
        self.registry_api_calls.labels(method=method, endpoint=endpoint, status=status).inc()
        self.registry_api_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_full_sync(self, duration: float):
        """Record full synchronization metrics"""
        if not self.enabled:
            return
            
        self.full_sync_duration.observe(duration)
        self.last_sync_timestamp.set(time.time())
    
    def update_current_counts(self, components: int, apis: int, queue_size: int):
        """Update current count gauges"""
        if not self.enabled:
            return
            
        self.components_current.set(components)
        self.apis_current.set(apis)
        self.sync_queue_size.set(queue_size)
    
    def update_from_collector_metrics(self, metrics: ComponentCollectorMetrics):
        """Update metrics from collector metrics object"""
        if not self.enabled:
            return
        
        # Update counters (only increment by difference)
        self.labels_created._value._value = metrics.labels_created
        
        # Update gauges
        self.components_current.set(metrics.components_watched)
        
        if metrics.last_sync_time:
            self.last_sync_timestamp.set(metrics.last_sync_time.timestamp())
    
    def start_server(self):
        """Start the Prometheus metrics HTTP server"""
        if not self.enabled:
            logger.info("Metrics collection disabled, not starting metrics server")
            return
        
        try:
            start_http_server(self.config.port)
            logger.info(f"Metrics server started on port {self.config.port}")
            logger.info(f"Metrics available at: http://localhost:{self.config.port}{self.config.endpoint}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise


class HealthChecker:
    """Health checker for the Custom-Resource Collector"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.last_kubernetes_event = None
        self.last_registry_sync = None
        self.kubernetes_healthy = False
        self.registry_healthy = False
        self.component_count = 0
        self.error_count = 0
        self.max_errors = 100  # Maximum errors before marking unhealthy
    
    def update_kubernetes_health(self, healthy: bool, last_event_time: datetime = None):
        """Update Kubernetes connectivity health"""
        self.kubernetes_healthy = healthy
        if last_event_time:
            self.last_kubernetes_event = last_event_time
    
    def update_registry_health(self, healthy: bool, last_sync_time: datetime = None):
        """Update Component Registry health"""
        self.registry_healthy = healthy
        if last_sync_time:
            self.last_registry_sync = last_sync_time
    
    def update_component_count(self, count: int):
        """Update monitored component count"""
        self.component_count = count
    
    def record_error(self):
        """Record an error occurrence"""
        self.error_count += 1
    
    def reset_error_count(self):
        """Reset error count (called on successful operations)"""
        self.error_count = 0
    
    def is_healthy(self) -> bool:
        """Check overall health status"""
        # Check if too many errors
        if self.error_count > self.max_errors:
            return False
        
        # Check if Kubernetes connection is healthy
        if not self.kubernetes_healthy:
            return False
        
        # Check if Registry connection is healthy
        if not self.registry_healthy:
            return False
        
        # Check if we've processed events recently (if we've been running for more than 5 minutes)
        uptime = datetime.utcnow() - self.start_time
        if uptime.total_seconds() > 300:  # 5 minutes
            if self.last_kubernetes_event:
                time_since_last_event = datetime.utcnow() - self.last_kubernetes_event
                if time_since_last_event.total_seconds() > 600:  # 10 minutes
                    # No Kubernetes events for 10 minutes might indicate a problem
                    logger.warning("No Kubernetes events received for 10 minutes")
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "healthy": self.is_healthy(),
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "kubernetes": {
                "healthy": self.kubernetes_healthy,
                "last_event_time": self.last_kubernetes_event.isoformat() if self.last_kubernetes_event else None
            },
            "registry": {
                "healthy": self.registry_healthy,
                "last_sync_time": self.last_registry_sync.isoformat() if self.last_registry_sync else None
            },
            "components": {
                "monitored_count": self.component_count
            },
            "errors": {
                "total_count": self.error_count,
                "max_threshold": self.max_errors
            }
        }


class MonitoringManager:
    """Manager for all monitoring functionality"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics = MetricsCollector(config)
        self.health = HealthChecker()
        self._monitoring_task = None
    
    async def start(self):
        """Start monitoring services"""
        # Start metrics server
        if self.config.enabled:
            self.metrics.start_server()
        
        # Start monitoring update loop
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Monitoring services started")
    
    async def stop(self):
        """Stop monitoring services"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring services stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring update loop"""
        while True:
            try:
                # Update health status periodically
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Here you could add periodic health checks
                # For now, just log that monitoring is active
                logger.debug("Monitoring loop active")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    def update_from_synchronizer(self, sync_status: Dict):
        """Update monitoring from synchronizer status"""
        # Update health
        self.health.update_component_count(sync_status.get("total_components", 0))
        
        # Update metrics if enabled
        if self.config.enabled:
            metrics_data = sync_status.get("metrics", {})
            queue_size = sync_status.get("queue_size", 0)
            
            self.metrics.update_current_counts(
                components=sync_status.get("total_components", 0),
                apis=metrics_data.get("apis_synced", 0),
                queue_size=queue_size
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete monitoring status"""
        return {
            "health": self.health.get_health_status(),
            "metrics_enabled": self.config.enabled,
            "metrics_port": self.config.port if self.config.enabled else None,
            "metrics_endpoint": f"http://localhost:{self.config.port}{self.config.endpoint}" if self.config.enabled else None
        }