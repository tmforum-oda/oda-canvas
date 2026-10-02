"""
Utility Functions

Helper functions for the operator.

"""

from datetime import datetime, timedelta


def get_requeue_duration(now: datetime, interval: int) -> float:
    """
    Calculate the duration until the next interval boundary
    
    The controller should requeue at the next interval boundary.
    For example, if the interval is 5 minutes and the current time is 12:37,
    the controller should requeue at 12:40 (3 minutes from now).
    
    Args:
        now: Current datetime
        interval: Interval in minutes
        
    Returns:
        Duration in seconds until the next interval
    """
    
    # Calculate the difference between current minute and next interval
    # e.g., if interval is 5 and current minute is 37, diff is 3
    current_minute = now.minute
    diff = interval - (current_minute % interval)
    
    # Add the difference to get the next interval time
    next_interval = now + timedelta(minutes=diff)
    
    # Zero out seconds and microseconds
    next_interval = next_interval.replace(second=0, microsecond=0)
    
    # Calculate duration from now to next interval
    duration = (next_interval - now).total_seconds()
    
    # Ensure we don't return 0 or negative values
    if duration <= 0:
        duration = interval * 60  # Return full interval in seconds
    
    return duration
