import logging
import kopf
from datetime import datetime, timezone
from kubernetes import client, config
from typing import Optional, Dict, Any

from carbon_tmf628_fetcher import CarbonForecastTMF628Fetcher
from max_replica_getter import get_max_replicas
from metrics import (
    reconciles_total,
    reconcile_errors_total,
    carbon_intensity_metric,
    default_max_replicas_metric,
    max_replicas_metric
)
from utils import get_requeue_duration
from models import CarbonManagementSpec
from scaled_object_manager import ScaledObjectManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

# Create Kubernetes API clients
api_client = client.ApiClient()
core_v1 = client.CoreV1Api(api_client)
apps_v1 = client.AppsV1Api(api_client)
custom_objects_api = client.CustomObjectsApi(api_client)

# Create ScaledObject manager
scaled_object_manager = ScaledObjectManager(apps_v1, custom_objects_api)


@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'carbonmanagements')
@kopf.on.update('oda.tmforum.org', 'v1alpha1', 'carbonmanagements')
@kopf.on.timer('oda.tmforum.org', 'v1alpha1', 'carbonmanagements', interval=300, initial_delay=10)
async def carbonManagement(
    spec: Dict[str, Any],
    name: str,
    namespace: str,
    uid: str,
    status: Dict[str, Any],
    patch: kopf.Patch,
    logger: kopf.Logger,
    **kwargs
) -> Dict[str, Any]:
    """
    Reconcile CarbonManagement resource
    
    This function:
    1. Fetches carbon forecast data
    2. Calculates max replicas based on carbon intensity
    3. Discovers deployments matching the selector
    4. Creates/updates KEDA ScaledObjects for each deployment
    5. Updates status and metrics
    """
    
    logger.info(f"Reconciling CarbonManagement: {name}")
    
    # Increment reconcile counter
    reconciles_total.labels(app=name).inc()
    
    now = datetime.now(timezone.utc)
    default_requeue_interval = 5  # minutes
    
    # Parse spec
    try:
        scaler_spec = CarbonManagementSpec.from_dict(spec)
    except Exception as e:
        logger.error(f"Failed to parse spec: {e}")
        reconcile_errors_total.labels(app=name).inc()
        set_status_condition(
            patch, 
            status="True",
            reason="SpecParseError",
            message=f"Failed to parse spec: {e}"
        )
        return {"requeue_after": get_requeue_duration(now, default_requeue_interval)}
    
    max_replica_count: Optional[int] = None
    requeue_interval = default_requeue_interval
    
    # Initialize carbon forecast fetcher
    try:
        tmf628_config = scaler_spec.carbon_intensity_forecast_data_source.tmf628_api
        fetcher = CarbonForecastTMF628Fetcher(
            base_url=tmf628_config.url,
            region=tmf628_config.region,
            timeout=tmf628_config.timeout
        )
        logger.info(f"Using TMF628 carbon forecast API at {tmf628_config.url}")
        if tmf628_config.region:
            logger.info(f"Filtering for region: {tmf628_config.region}")
    except Exception as e:
        logger.error(f"Failed to initialize carbon forecast fetcher: {e}")
        max_replica_count = scaler_spec.default_max_replicas
        set_status_condition(
            patch,
            status="True",
            reason="FetcherInitError",
            message=f"Failed to initialize fetcher, using default max replicas: {e}"
        )
    
    # Fetch current carbon forecast
    current_forecast = None
    if max_replica_count is None:
        try:
            current_forecast = fetcher.fetch_current(now)
            requeue_interval = current_forecast.duration
            logger.info(f"Current carbon intensity: {current_forecast.value} at {current_forecast.timestamp}")
        except Exception as e:
            logger.error(f"Failed to fetch current carbon forecast: {e}")
            max_replica_count = scaler_spec.default_max_replicas
            set_status_condition(
                patch,
                status="True",
                reason="CarbonDataFetchError",
                message=f"Failed to fetch carbon forecast, using default max replicas: {e}"
            )
    
    # Calculate max replicas based on carbon intensity
    if max_replica_count is None and current_forecast is not None:
        try:
            max_replica_count = get_max_replicas(
                current_forecast,
                scaler_spec.max_replicas_by_carbon_intensity,
                scaler_spec.default_max_replicas
            )
            logger.info(f"Calculated max replicas: {max_replica_count}")
        except Exception as e:
            logger.error(f"Failed to calculate max replicas: {e}")
            max_replica_count = scaler_spec.default_max_replicas
            set_status_condition(
                patch,
                status="True",
                reason="MaxReplicasCalculationError",
                message=f"Failed to calculate max replicas, using default: {e}"
            )
    
    # Ensure we have a max replica count
    if max_replica_count is None:
        max_replica_count = scaler_spec.default_max_replicas
        logger.warning(f"Using default max replicas: {max_replica_count}")
    
    # Update metrics
    if current_forecast:
        carbon_intensity_metric.labels(app=name).set(current_forecast.value)
    
    default_max_replicas_metric.labels(app=name).set(scaler_spec.default_max_replicas)
    max_replicas_metric.labels(app=name).set(max_replica_count)
    
    # Discover deployments and manage ScaledObjects
    try:
        # Discover deployments by label matching
        target_namespace = scaler_spec.deployment_selector.namespace or namespace
        deployments = scaled_object_manager.discover_deployments(
            match_labels=scaler_spec.deployment_selector.match_labels,
            namespace=target_namespace
        )
        
        if not deployments:
            logger.warning(f"No deployments found matching labels: {scaler_spec.deployment_selector.match_labels}")
            set_status_condition(
                patch,
                status="True",
                reason="NoDeploymentsFound",
                message="No deployments match the selector"
            )
            patch.setdefault("status", {})["deploymentsDiscovered"] = 0
            patch["status"]["scaledObjectsManaged"] = 0
            patch["status"]["scaledObjectsFailed"] = 0
            return {"requeue_after": get_requeue_duration(now, default_requeue_interval)}
        
        # Create owner references for automatic cleanup
        owner_references = [{
            "apiVersion": "oda.tmforum.org/v1alpha1",
            "kind": "CarbonManagement",
            "name": name,
            "uid": uid,
            "controller": True,
            "blockOwnerDeletion": True
        }]
        
        # Ensure ScaledObject for each deployment
        managed_count = 0
        failed_count = 0
        
        for dep in deployments:
            dep_name = dep['name']
            dep_namespace = dep['namespace']
            
            # Get deployment-specific overrides if configured
            overrides = None
            if scaler_spec.deployment_selector.deployment_overrides:
                overrides = scaler_spec.deployment_selector.deployment_overrides.get(dep_name)
            
            try:
                success, message = scaled_object_manager.ensure_scaled_object(
                    deployment_name=dep_name,
                    deployment_namespace=dep_namespace,
                    triggers=scaler_spec.scaled_object_template.triggers,
                    max_replica_count=max_replica_count,
                    owner_references=owner_references,
                    min_replica_count=scaler_spec.scaled_object_template.min_replica_count,
                    polling_interval=scaler_spec.scaled_object_template.polling_interval,
                    cooldown_period=scaler_spec.scaled_object_template.cooldown_period,
                    fallback=scaler_spec.scaled_object_template.fallback,
                    deployment_overrides=overrides
                )
                
                if success:
                    managed_count += 1
                    logger.info(f"Successfully managed ScaledObject for {dep_name}")
                else:
                    logger.error(f"Failed to ensure ScaledObject for {dep_name}: {message}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to ensure ScaledObject for {dep_name}: {e}")
                failed_count += 1
        
        # Cleanup orphaned ScaledObjects
        active_deployment_names = [d['name'] for d in deployments]
        deleted_count = scaled_object_manager.cleanup_orphaned_scaled_objects(
            namespace=target_namespace,
            active_deployments=active_deployment_names,
            owner_uid=uid
        )
        
        # Update status
        patch.setdefault("status", {})["deploymentsDiscovered"] = len(deployments)
        patch["status"]["scaledObjectsManaged"] = managed_count
        patch["status"]["scaledObjectsFailed"] = failed_count
        
        logger.info(f"Managed {managed_count} ScaledObjects, {failed_count} failed, {deleted_count} cleaned up")
        
        # Set condition based on results
        if failed_count > 0 and managed_count == 0:
            # All failed - likely KEDA not installed
            set_status_condition(
                patch,
                status="True",
                reason="KedaNotAvailable",
                message=f"Failed to manage all {failed_count} ScaledObjects. KEDA may not be installed. See: https://keda.sh/docs/deploy/"
            )
        elif failed_count > 0:
            # Some failed
            set_status_condition(
                patch,
                status="True",
                reason="PartialFailure",
                message=f"Managed {managed_count} ScaledObjects, but {failed_count} failed"
            )
        else:
            # All succeeded
            set_status_condition(
                patch,
                status="False",
                reason="Succeeded",
                message=f"Successfully managing {managed_count} ScaledObjects"
            )
            
    except Exception as e:
        logger.error(f"Failed to manage KEDA targets: {e}")
        reconcile_errors_total.labels(app=name).inc()
        set_status_condition(
            patch,
            status="True",
            reason="ReconciliationFailed",
            message=f"Failed to manage KEDA targets: {e}"
        )
    
    # Calculate requeue duration
    requeue_seconds = get_requeue_duration(now, requeue_interval)
    logger.info(f"Requeuing after {requeue_seconds} seconds")
    
    return {"requeue_after": requeue_seconds}


def set_status_condition(
    patch: kopf.Patch,
    status: str,
    reason: str,
    message: str
):
    """Set status condition on the CarbonManagement resource"""
    
    condition = {
        "type": "OperatorDegraded",
        "status": status,
        "reason": reason,
        "message": message,
        "lastTransitionTime": datetime.now(timezone.utc).isoformat()
    }
    
    # Initialize conditions if not present
    if "status" not in patch:
        patch["status"] = {}
    if "conditions" not in patch.get("status", {}):
        patch.setdefault("status", {})["conditions"] = []
    
    # Update or add condition
    conditions = patch["status"]["conditions"]
    updated = False
    for i, cond in enumerate(conditions):
        if cond.get("type") == "OperatorDegraded":
            conditions[i] = condition
            updated = True
            break
    
    if not updated:
        conditions.append(condition)


@kopf.on.delete('oda.tmforum.org', 'v1alpha1', 'CarbonManagements')
async def delete_carbon_management(
    name: str,
    namespace: str,
    uid: str,
    logger: kopf.Logger,
    **kwargs
) -> None:
    """
    Handle deletion of CarbonManagement resource
    
    This handler:
    1. Cleans up managed ScaledObjects (automatic mode)
    2. Allows the finalizer to be removed for graceful deletion
    
    Note: Owner references on ScaledObjects (blockOwnerDeletion: true)
    will handle automatic cascade deletion, so manual deletion is not needed.
    However, this handler ensures cleanup logic is logged and any errors are handled.
    """
    
    logger.info(f"Deleting CarbonManagement: {name}/{namespace}")
    
    try:
        # For automatic mode, ScaledObjects have owner references set
        # Kubernetes will automatically delete them due to blockOwnerDeletion: true
        # This handler just needs to complete so the finalizer is removed
        
        logger.info(f"CarbonManagement {name} deletion approved - finalizer will be removed")
        
    except Exception as e:
        logger.error(f"Error during deletion of {name}: {e}")
        # Log but don't raise - we want deletion to proceed even if cleanup has issues
        raise kopf.PermanentError(f"Failed to delete CarbonManagement: {e}")


@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, **_):
    """Configure the operator on startup"""
    
    # Set operator name
    settings.persistence.finalizer = 'carbon-management/finalizer'
    
    # Configure watching - use empty list to watch all namespaces (cluster-wide)
    settings.posting.level = logging.INFO
    settings.watching.server_timeout = 600
    settings.watching.client_timeout = 600
    
    logger.info("Carbon Management Operator started in cluster-wide mode")


@kopf.on.cleanup()
async def cleanup(**_):
    """Cleanup resources on operator shutdown"""
    logger.info("Carbon Management Operator shutting down")


if __name__ == '__main__':
    # Start the operator
    kopf.run(
        standalone=True
        # Kopf automatically handles:
        # - Health endpoints on port 8080 (/healthz, /readyz)
        # - Cluster-wide watching (configured in @kopf.on.startup)
    )
