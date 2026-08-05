"""
Carbon Forecast TMF628 API Fetcher Module

Fetches carbon intensity forecast data from TMF628 Performance Management API.
This fetcher calls the TMF628 Carbon Intensity Service deployed on ODA Canvas
and transforms PerformanceMeasurement responses into CarbonForecast objects.

"""

import requests
from datetime import datetime, timezone
from typing import List, Optional
from carbon_forecast_fetcher import CarbonForecast, CarbonForecastFetcher


class CarbonForecastTMF628Fetcher(CarbonForecastFetcher):
    """
    Fetches carbon intensity forecast from TMF628 Performance Management API
    
    This fetcher calls the TMF628 Carbon Intensity Service endpoint and
    transforms PerformanceMeasurement (TMF628) responses into CarbonForecast
    objects for use by the carbon operator.
    
    Preferred method: fetch_current() - gets only the current forecast using time-based filtering
    Legacy method: fetch() - gets all forecasts and returns them as a list
    """
    
    def __init__(
        self,
        base_url: str,
        region: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize TMF628 fetcher
        
        Args:
            base_url: Base URL of TMF628 API (e.g., http://carbon-intensity-service.canvas.svc.cluster.local/tmf-api/performance/v5)
            region: Optional region filter (e.g., "UK-South", "EU-West", "US-East")
            timeout: HTTP request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.region = region
        self.timeout = timeout
    
    def fetch_current(self, target_time: Optional[datetime] = None) -> CarbonForecast:
        """
        Fetch current carbon forecast for a specific time
        
        Args:
            target_time: The timestamp to get forecast for (defaults to now in UTC)
            
        Returns:
            CarbonForecast object for the specified time
            
        Raises:
            ValueError: If API is unreachable or no forecast found for the time
        """
        if target_time is None:
            target_time = datetime.now(timezone.utc)
        
        endpoint = f"{self.base_url}/performanceMeasurement"
        
        try:
            # Build query parameters
            params = {
                'validForTimestamp': target_time.isoformat()
            }
            if self.region:
                params['region'] = self.region
            
            # Call TMF628 API with time filter
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            
            # Check response status
            if response.status_code != 200:
                raise ValueError(
                    f"TMF628 API returned status {response.status_code}: {response.text}"
                )
            
            # Parse JSON response
            measurements = response.json()
            
            if not isinstance(measurements, list):
                raise ValueError(
                    f"Expected array of PerformanceMeasurement, got {type(measurements)}"
                )
            
            if len(measurements) == 0:
                region_msg = f" for region '{self.region}'" if self.region else ""
                raise ValueError(
                    f"No carbon intensity forecast found for timestamp {target_time.isoformat()}{region_msg}"
                )
            
            # Transform the first (and should be only) measurement to CarbonForecast
            try:
                forecast = self._transform_measurement(measurements[0])
                return forecast
            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(f"Failed to transform measurement: {e}")
                
        except requests.exceptions.Timeout:
            raise ValueError(
                f"TMF628 API request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.ConnectionError as e:
            raise ValueError(
                f"Failed to connect to TMF628 API at {endpoint}: {e}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(
                f"TMF628 API request failed: {e}"
            )
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Unexpected error fetching from TMF628 API: {e}"
            )
    
    def fetch(self) -> List[CarbonForecast]:
        """
        Fetch carbon forecast from TMF628 API
        
        Returns:
            List of CarbonForecast objects
            
        Raises:
            ValueError: If API is unreachable or returns invalid data
        """
        endpoint = f"{self.base_url}/performanceMeasurement"
        
        try:
            # Call TMF628 API
            response = requests.get(
                endpoint,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            
            # Check response status
            if response.status_code != 200:
                raise ValueError(
                    f"TMF628 API returned status {response.status_code}: {response.text}"
                )
            
            # Parse JSON response
            measurements = response.json()
            
            if not isinstance(measurements, list):
                raise ValueError(
                    f"Expected array of PerformanceMeasurement, got {type(measurements)}"
                )
            
            # Transform TMF628 measurements to CarbonForecast objects
            forecasts = []
            for measurement in measurements:
                try:
                    forecast = self._transform_measurement(measurement)
                    
                    # Apply region filter if specified
                    if self.region is None or forecast.location == self.region:
                        forecasts.append(forecast)
                        
                except (KeyError, ValueError, TypeError) as e:
                    # Log transformation errors but continue processing other measurements
                    # This allows partial success if some measurements are malformed
                    print(f"Warning: Failed to transform measurement {measurement.get('id', 'unknown')}: {e}")
                    continue
            
            if not forecasts:
                if self.region:
                    raise ValueError(
                        f"No carbon intensity measurements found for region '{self.region}'"
                    )
                else:
                    raise ValueError("No valid carbon intensity measurements found in response")
            
            return forecasts
            
        except requests.exceptions.Timeout:
            raise ValueError(
                f"TMF628 API request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.ConnectionError as e:
            raise ValueError(
                f"Failed to connect to TMF628 API at {endpoint}: {e}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(
                f"TMF628 API request failed: {e}"
            )
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Unexpected error fetching from TMF628 API: {e}"
            )
    
    def _transform_measurement(self, measurement: dict) -> CarbonForecast:
        """
        Transform TMF628 PerformanceMeasurement to CarbonForecast
        
        Args:
            measurement: TMF628 PerformanceMeasurement dict
            
        Returns:
            CarbonForecast object
            
        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Extract timestamp from validFor.startDateTime
        valid_for = measurement['validFor']
        start_time_str = valid_for['startDateTime']
        end_time_str = valid_for['endDateTime']
        
        # Parse ISO 8601 timestamps
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        
        # Calculate duration in minutes
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = int(duration_seconds / 60)
        
        # Extract carbon intensity value from performanceIndicatorValue array
        indicator_values = measurement['performanceIndicatorValue']
        if not indicator_values or len(indicator_values) == 0:
            raise ValueError("performanceIndicatorValue array is empty")
        
        # Get first indicator (carbon intensity)
        observed_value_str = indicator_values[0]['observedValue']
        carbon_intensity = float(observed_value_str)
        
        # Extract region from tag
        tag = measurement.get('tag', {})
        region = tag.get('region')
        
        return CarbonForecast(
            timestamp=start_time,
            value=carbon_intensity,
            duration=duration_minutes,
            location=region
        )
