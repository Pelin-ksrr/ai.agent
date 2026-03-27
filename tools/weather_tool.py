"""
Weather Tool — fetches current weather from Open-Meteo (no API key required).

Uses the free endpoint: https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true
"""

import requests
from tools.base_tool import BaseTool

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
_TIMEOUT = 10  # seconds

class WeatherTool(BaseTool):
    """Retrieves current weather conditions for a given city via Open-Meteo."""

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Gets current weather conditions (temperature, wind, humidity) for a city."

    def execute(self, city: str) -> str:
        city = city.strip()
        geo_url = _GEOCODE_URL.format(city=requests.utils.quote(city))
        try:
            geo_resp = requests.get(geo_url, timeout=_TIMEOUT)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            results = geo_data.get("results")
            if not results:
                return f"Error: Could not find location for '{city}'."
            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
        except Exception as exc:
            return f"Error: Failed to geocode city '{city}': {exc}"

        weather_url = _WEATHER_URL.format(lat=lat, lon=lon)
        try:
            w_resp = requests.get(weather_url, timeout=_TIMEOUT)
            w_resp.raise_for_status()
            w_data = w_resp.json()
            current = w_data.get("current_weather")
            if not current:
                return f"Error: No weather data for '{city}'."
            temp_c = current["temperature"]
            wind_kph = current["windspeed"]
            wind_dir = current["winddirection"]
            weather_code = current["weathercode"]
            return (
                f"Weather in {city.title()}:\n"
                f"  Temperature  : {temp_c}°C\n"
                f"  Wind Speed   : {wind_kph} km/h\n"
                f"  Wind Dir     : {wind_dir}°\n"
                f"  Weather Code : {weather_code} (see Open-Meteo docs)"
            )
        except Exception as exc:
            return f"Error: Failed to fetch weather for '{city}': {exc}"

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": (
                "Retrieves current weather conditions (temperature, humidity, wind speed) "
                "for a specified city using the wttr.in service."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "Name of the city, e.g. 'London', 'Tokyo', 'Istanbul', 'New York'."
                        ),
                    }
                },
                "required": ["city"],
            },
        }
