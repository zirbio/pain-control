from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    PROJECT_ROOT: str = str(Path(__file__).resolve().parents[3])
    DATABASE_URL: str = ""
    DATA_DIR: str = ""
    IMPORTS_DIR: str = ""

    # Weather
    WEATHER_LOCATION: str = "Almería"
    WEATHER_LAT: float = 36.8340
    WEATHER_LON: float = -2.4637

    # Pain tracking
    PAIN_SCALE_MIN: int = 0
    PAIN_SCALE_MAX: int = 10

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Schema evolution
    EXTRAS_PROMOTION_THRESHOLD: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context) -> None:
        if not self.DATA_DIR:
            self.DATA_DIR = str(Path(self.PROJECT_ROOT) / "data")
        if not self.IMPORTS_DIR:
            self.IMPORTS_DIR = str(Path(self.DATA_DIR) / "imports")
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite:///{Path(self.DATA_DIR) / 'pain-control.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
