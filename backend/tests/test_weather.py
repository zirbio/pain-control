from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.importers.weather import WeatherData, WeatherImporter


def test_parse_openweathermap_response():
    raw_response = {
        "main": {"temp": 14.5, "humidity": 78, "pressure": 1008},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "name": "London",
    }
    importer = WeatherImporter(api_key="test", lat=51.51, lon=-0.13)
    result = importer.parse_response(raw_response)
    assert isinstance(result, WeatherData)
    assert result.temperature_c == 14.5
    assert result.humidity_pct == 78
    assert result.pressure_hpa == 1008.0
    assert result.conditions == "Rain"
    assert result.location == "London"


def test_compute_pressure_change():
    importer = WeatherImporter(api_key="test", lat=51.51, lon=-0.13)
    change = importer.compute_pressure_change(
        current=1008.0,
        yesterday=1013.2,
    )
    assert abs(change - (-5.2)) < 0.01


def test_compute_pressure_change_no_yesterday():
    importer = WeatherImporter(api_key="test", lat=51.51, lon=-0.13)
    change = importer.compute_pressure_change(current=1008.0, yesterday=None)
    assert change is None


def test_fetch_current_success():
    """fetch_current returns WeatherData from mocked API response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 14.5, "humidity": 78, "pressure": 1008},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "name": "London",
    }
    mock_response.raise_for_status = MagicMock()

    importer = WeatherImporter(api_key="test-key", lat=51.51, lon=-0.13)
    with patch.object(httpx, "get", return_value=mock_response) as mock_get:
        result = importer.fetch_current()
        assert result.temperature_c == 14.5
        assert result.location == "London"
        mock_get.assert_called_once()


def test_fetch_current_http_error():
    """fetch_current raises on HTTP error."""
    importer = WeatherImporter(api_key="bad-key", lat=51.51, lon=-0.13)
    with (
        patch.object(
            httpx,
            "get",
            side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock()),
        ),
        pytest.raises(httpx.HTTPStatusError),
    ):
        importer.fetch_current()
