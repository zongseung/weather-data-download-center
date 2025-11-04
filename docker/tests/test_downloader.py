"""
Tests for weather downloader module
"""

import unittest
from datetime import datetime
from src.weather_downloader import WeatherDownloader, DownloadConfig


class TestWeatherDownloader(unittest.TestCase):
    """Test cases for WeatherDownloader class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.downloader = WeatherDownloader()
    
    def test_download_config_creation(self):
        """Test DownloadConfig creation"""
        config = DownloadConfig(
            login_id="test_id",
            password="test_password",
            config_name="단기예보",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        self.assertEqual(config.login_id, "test_id")
        self.assertEqual(config.password, "test_password")
        self.assertEqual(config.config_name, "단기예보")
        self.assertEqual(config.start_date, datetime(2024, 1, 1))
        self.assertEqual(config.end_date, datetime(2024, 1, 31))
    
    def test_weather_config_constants(self):
        """Test WeatherConfig constants"""
        from src.weather_downloader.config import WeatherConfig
        
        configs = WeatherConfig.get_config("단기예보")
        self.assertIn("code", configs)
        self.assertEqual(configs["code"], "424")
        
        variables = WeatherConfig.get_variables()
        self.assertIsInstance(variables, list)
        self.assertGreater(len(variables), 0)


if __name__ == "__main__":
    unittest.main()
