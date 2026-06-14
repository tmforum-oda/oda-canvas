"""
Max Replica Getter Module

Calculates the maximum number of replicas based on carbon intensity.

"""

from typing import List, Optional

from models import CarbonIntensityConfig
from carbon_forecast_fetcher import CarbonForecast


def get_max_replicas(
    forecast: Optional[CarbonForecast],
    configs: List[CarbonIntensityConfig],
    default_max_replicas: int
) -> int:
    """
    Get the maximum number of replicas based on current carbon intensity
    
    The function finds the appropriate replica count by:
    1. Sorting the configs by carbon intensity threshold (ascending)
    2. Finding which range the current carbon intensity falls into
    3. Returning the corresponding max replicas
    
    If forecast data is unavailable, returns the default_max_replicas.
    
    Args:
        forecast: Current carbon forecast (can be None)
        configs: List of carbon intensity configurations
        default_max_replicas: Default max replicas to use when forecast is unavailable
        
    Returns:
        Maximum number of replicas
    """
    
    if forecast is None:
        return default_max_replicas
    
    carbon_intensity = forecast.value
    
    # Sort configs by carbon intensity threshold in ascending order
    sorted_configs = sorted(
        configs,
        key=lambda c: c.carbon_intensity_threshold
    )
    
    # Find the appropriate range for the current carbon intensity
    for index, config in enumerate(sorted_configs):
        # Determine lower bound
        lower_bound = 0.0
        if index > 0:
            lower_bound = float(sorted_configs[index - 1].carbon_intensity_threshold)
        
        # Upper bound is the current config's threshold
        upper_bound = float(config.carbon_intensity_threshold)
        
        # Check if carbon intensity falls within this range
        # Lower bound is exclusive, upper bound is inclusive
        if lower_bound < carbon_intensity <= upper_bound:
            return config.max_replicas
    
    # If carbon intensity is above all thresholds,
    # return the max replicas from the last config
    return sorted_configs[-1].max_replicas
