"""Tests for weather profile generation."""
from tests.synthetic.weather import WeatherProfile


class TestWeatherProfile:
    def test_southeast_us_february(self):
        wp = WeatherProfile("southeast_us", month=2)
        assert wp.avg_high > wp.avg_low
        assert wp.sunrise < wp.sunset

    def test_get_conditions_for_hour(self):
        wp = WeatherProfile("southeast_us", month=2)
        cond = wp.get_conditions(day=0, hour=14.0, seed=42)
        assert "temp_f" in cond
        assert "humidity_pct" in cond
        assert "wind_mph" in cond
        assert cond["temp_f"] > 0

    def test_temperature_peaks_afternoon(self):
        wp = WeatherProfile("southeast_us", month=7)
        morning = wp.get_conditions(day=0, hour=8.0, seed=42)
        afternoon = wp.get_conditions(day=0, hour=14.0, seed=42)
        assert afternoon["temp_f"] > morning["temp_f"]

    def test_deterministic_with_seed(self):
        wp = WeatherProfile("southeast_us", month=2)
        a = wp.get_conditions(day=5, hour=12.0, seed=42)
        b = wp.get_conditions(day=5, hour=12.0, seed=42)
        assert a == b

    def test_daylight_hours(self):
        wp = WeatherProfile("southeast_us", month=6)
        wp_winter = WeatherProfile("southeast_us", month=12)
        assert wp.daylight_hours > wp_winter.daylight_hours
