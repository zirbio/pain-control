import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.importers.weather import WMO_CODES, WeatherData, WeatherImporter


def test_wmo_codes_mapping():
    assert WMO_CODES[0] == "Despejado"
    assert WMO_CODES[61] == "Lluvia ligera"
    assert WMO_CODES[95] == "Tormenta"


def test_compute_pressure_change():
    importer = WeatherImporter(lat=36.83, lon=-2.46, location="Almería")
    change = importer.compute_pressure_change(current=1008.0, yesterday=1013.2)
    assert abs(change - (-5.2)) < 0.01


def test_compute_pressure_change_no_yesterday():
    importer = WeatherImporter(lat=36.83, lon=-2.46, location="Almería")
    change = importer.compute_pressure_change(current=1008.0, yesterday=None)
    assert change is None


def test_fetch_date_parses_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "daily": {
            "time": ["2026-03-27"],
            "temperature_2m_mean": [18.5],
            "relative_humidity_2m_mean": [65.0],
            "surface_pressure_mean": [1015.3],
            "weather_code": [3],
        }
    }
    mock_response.raise_for_status = MagicMock()

    importer = WeatherImporter(lat=36.83, lon=-2.46, location="Almería")
    with patch.object(httpx, "get", return_value=mock_response):
        result = importer.fetch_date(datetime.date(2026, 3, 27))

    assert isinstance(result, WeatherData)
    assert result.temperature_c == 18.5
    assert result.humidity_pct == 65.0
    assert result.pressure_hpa == 1015.3
    assert result.conditions == "Nublado"
    assert result.location == "Almería"


def test_fetch_date_http_error():
    importer = WeatherImporter(lat=36.83, lon=-2.46, location="Almería")
    err = httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())
    with (
        patch.object(httpx, "get", side_effect=err),
        pytest.raises(httpx.HTTPStatusError),
    ):
        importer.fetch_date(datetime.date(2026, 3, 27))
