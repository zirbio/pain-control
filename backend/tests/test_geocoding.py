from unittest.mock import MagicMock, patch

import httpx

from backend.importers.geocoding import geocode_city


def test_geocode_city_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"latitude": 41.39, "longitude": 2.17, "name": "Barcelona"}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx, "get", return_value=mock_response):
        result = geocode_city("Barcelona")

    assert result is not None
    lat, lon, name = result
    assert abs(lat - 41.39) < 0.01
    assert abs(lon - 2.17) < 0.01
    assert name == "Barcelona"


def test_geocode_city_not_found():
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx, "get", return_value=mock_response):
        result = geocode_city("xyznonexistent")

    assert result is None


def test_geocode_city_http_error():
    with patch.object(httpx, "get", side_effect=httpx.HTTPError("timeout")):
        result = geocode_city("Barcelona")
    assert result is None
