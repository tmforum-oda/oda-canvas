"""
Carbon Forecast Fetcher Module

Defines the abstract base class for carbon forecast fetchers and the
CarbonForecast data model used by the carbon operator.

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class CarbonForecast:
    """Represents a carbon intensity forecast data point"""
    timestamp: datetime
    value: float
    duration: int  # in minutes
    location: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization, ensuring no bytes fields"""
        def safe(val):
            if isinstance(val, bytes):
                return val.decode('utf-8')
            return val
        return {
            "timestamp": safe(self.timestamp.isoformat()),
            "value": safe(self.value),
            "duration": safe(self.duration),
            "location": safe(self.location) if self.location is not None else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CarbonForecast':
        """Create CarbonForecast from dictionary"""
        timestamp = data['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return cls(
            timestamp=timestamp,
            value=data['value'],
            duration=data['duration'],
            location=data.get('location')
        )


def find_carbon_forecast(forecasts: List[CarbonForecast], target_time: datetime) -> Optional[CarbonForecast]:
    """
    Find the carbon forecast that applies to the given time
    
    Args:
        forecasts: List of carbon forecasts
        target_time: The time to find forecast for
        
    Returns:
        CarbonForecast if found, None otherwise
    """
    for forecast in forecasts:
        forecast_start = forecast.timestamp
        forecast_end = forecast_start + timedelta(minutes=forecast.duration)
        
        if (target_time >= forecast_start or target_time == forecast_start) and target_time < forecast_end:
            return forecast
    
    return None


class CarbonForecastFetcher(ABC):
    """Abstract base class for carbon forecast fetchers"""
    
    @abstractmethod
    def fetch(self) -> List[CarbonForecast]:
        """Fetch carbon forecast data"""
        pass
