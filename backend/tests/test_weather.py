from backend.importers.weather import WeatherData, WeatherImporter


def test_parse_openweathermap_response():
    raw_response = {
        "main": {"temp": 14.5, "humidity": 78, "pressure": 1008},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "name": "Madrid",
    }
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    result = importer.parse_response(raw_response)
    assert isinstance(result, WeatherData)
    assert result.temperature_c == 14.5
    assert result.humidity_pct == 78
    assert result.pressure_hpa == 1008.0
    assert result.conditions == "Rain"
    assert result.location == "Madrid"


def test_compute_pressure_change():
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    change = importer.compute_pressure_change(
        current=1008.0,
        yesterday=1013.2,
    )
    assert abs(change - (-5.2)) < 0.01


def test_compute_pressure_change_no_yesterday():
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    change = importer.compute_pressure_change(current=1008.0, yesterday=None)
    assert change is None
