"""
Weather Data Collection Project - Main Entry Point
"""

from src.scripts.run_collection import main as run_collection
from src.scripts.monitor_data import main as monitor_data


def main():
    """Main entry point for weather data collection"""
    print("Weather Data Collection Project")
    print("Available commands:")
    print("1. run_collection() - Start data collection")
    print("2. monitor_data() - Monitor data collection status")
    print("\nExample usage:")
    print("  from main import run_collection, monitor_data")
    print("  run_collection()  # Start collecting weather data")
    print("  monitor_data()    # Check collection status")


if __name__ == "__main__":
    main()
