from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.db.database import get_session_factory


def get_db() -> Generator[Session, None, None]:
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
