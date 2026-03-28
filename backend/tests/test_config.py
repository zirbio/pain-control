from backend.core.config import Settings


def test_default_settings():
    settings = Settings(
        OPENWEATHERMAP_API_KEY="test-key",
    )
    assert settings.DATABASE_URL.startswith("sqlite:///")
    assert settings.WEATHER_LOCATION == "London"
    assert settings.DATA_DIR.endswith("data")
    assert settings.IMPORTS_DIR.endswith("imports")


def test_pain_scale_bounds():
    settings = Settings(OPENWEATHERMAP_API_KEY="test-key")
    assert settings.PAIN_SCALE_MIN == 0
    assert settings.PAIN_SCALE_MAX == 10
