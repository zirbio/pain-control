from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_engine(settings.DATABASE_URL, echo=False)


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine)
