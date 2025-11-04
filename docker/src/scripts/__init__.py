"""
Scripts for weather data collection
"""

from .run_collection import main as run_collection
from .monitor_data import main as monitor_data

__all__ = ['run_collection', 'monitor_data']
