import httpx


def geocode_city(name: str) -> tuple[float, float, str] | None:
    """Return (lat, lon, display_name) for a city name using Open-Meteo geocoding."""
    try:
        response = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": name, "count": 1, "language": "es"},
            timeout=5,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            r = results[0]
            return r["latitude"], r["longitude"], r.get("name", name)
    except httpx.HTTPError:
        pass
    return None
