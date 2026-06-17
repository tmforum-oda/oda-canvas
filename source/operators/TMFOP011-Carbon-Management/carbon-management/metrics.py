"""
Metrics Module

Defines and exposes Prometheus metrics for the operator.

"""

from prometheus_client import Counter, Gauge


# Total number of reconciliations
reconciles_total = Counter(
    'carbon_management_reconciles_total',
    'Total number of reconciles',
    ['app']
)

# Total number of reconciliation errors
reconcile_errors_total = Counter(
    'carbon_management_reconcile_errors_total',
    'Total number of reconcile errors',
    ['app']
)

# Current carbon intensity value
carbon_intensity_metric = Gauge(
    'carbon_management_carbon_intensity',
    'Current carbon intensity value',
    ['app']
)

# Default maximum replicas (when carbon data is unavailable)
default_max_replicas_metric = Gauge(
    'carbon_management_default_max_replicas',
    'Default maximum replicas configured',
    ['app']
)

# Current maximum replicas being applied
max_replicas_metric = Gauge(
    'carbon_management_max_replicas',
    'Current maximum replicas being applied',
    ['app']
)
