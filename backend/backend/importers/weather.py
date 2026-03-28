from dataclasses import dataclass

import httpx


@dataclass
class WeatherData:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    pressure_change_hpa: float | None
    conditions: str
    location: str


class WeatherImporter:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, lat: float, lon: float):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon

    def parse_response(self, data: dict) -> WeatherData:
        return WeatherData(
            temperature_c=data["main"]["temp"],
            humidity_pct=data["main"]["humidity"],
            pressure_hpa=float(data["main"]["pressure"]),
            pressure_change_hpa=None,
            conditions=data["weather"][0]["main"] if data.get("weather") else "Unknown",
            location=data.get("name", "Unknown"),
        )

    def compute_pressure_change(self, current: float, yesterday: float | None) -> float | None:
        if yesterday is None:
            return None
        return round(current - yesterday, 2)

    def fetch_current(self) -> WeatherData:
        """Fetch current weather from OpenWeatherMap API."""
        response = httpx.get(
            self.BASE_URL,
            params={
                "lat": self.lat,
                "lon": self.lon,
                "appid": self.api_key,
                "units": "metric",
            },
            timeout=10,
        )
        response.raise_for_status()
        return self.parse_response(response.json())
