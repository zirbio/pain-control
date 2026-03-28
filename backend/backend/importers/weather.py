import datetime
from dataclasses import dataclass

import httpx

WMO_CODES = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla helada",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    56: "Llovizna helada ligera",
    57: "Llovizna helada densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    66: "Lluvia helada ligera",
    67: "Lluvia helada fuerte",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada fuerte",
    77: "Granizo fino",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve fuertes",
    95: "Tormenta",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo fuerte",
}


@dataclass
class WeatherData:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    pressure_change_hpa: float | None
    conditions: str
    location: str


class WeatherImporter:
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, lat: float, lon: float, location: str = ""):
        self.lat = lat
        self.lon = lon
        self.location = location

    def fetch_date(self, date: datetime.date) -> WeatherData:
        """Fetch weather for a specific date (past or today)."""
        today = datetime.date.today()
        # Open-Meteo archive has ~5 day delay; use forecast API with past_days for recent dates
        days_ago = (today - date).days
        daily_fields = (
            "temperature_2m_mean,relative_humidity_2m_mean,surface_pressure_mean,weather_code"
        )
        if days_ago <= 5:
            url = self.FORECAST_URL
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "daily": daily_fields,
                "past_days": min(days_ago + 1, 7),
                "forecast_days": 1,
                "timezone": "Europe/Madrid",
            }
        else:
            url = self.ARCHIVE_URL
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "daily": daily_fields,
                "start_date": date.isoformat(),
                "end_date": date.isoformat(),
                "timezone": "Europe/Madrid",
            }

        response = httpx.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])

        # Find the index for the requested date
        date_str = date.isoformat()
        if date_str in dates:
            idx = dates.index(date_str)
        elif dates:
            idx = 0
        else:
            raise ValueError(f"No weather data available for {date}")

        temp = daily.get("temperature_2m_mean", [None])[idx]
        humidity = daily.get("relative_humidity_2m_mean", [None])[idx]
        pressure = daily.get("surface_pressure_mean", [None])[idx]
        weather_code = daily.get("weather_code", [0])[idx]

        return WeatherData(
            temperature_c=temp if temp is not None else 0.0,
            humidity_pct=humidity if humidity is not None else 0.0,
            pressure_hpa=pressure if pressure is not None else 0.0,
            pressure_change_hpa=None,
            conditions=WMO_CODES.get(weather_code, f"Code {weather_code}"),
            location=self.location,
        )

    def compute_pressure_change(self, current: float, yesterday: float | None) -> float | None:
        if yesterday is None:
            return None
        return round(current - yesterday, 2)
