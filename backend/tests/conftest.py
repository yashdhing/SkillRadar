from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from skillradar_api.db.base import Base
from skillradar_api.db.session import get_db_session
from skillradar_api.main import app
from skillradar_api.profile.service import seed_default_user_profile


@pytest.fixture()
def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite+pysqlite:///{tmp_path / 'skillradar.db'}"


@pytest.fixture()
def session(sqlite_url: str) -> Iterator[Session]:
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with testing_session() as db_session:
        yield db_session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(session: Session) -> Iterator[TestClient]:
    seed_default_user_profile(session)
    session.commit()

    def override_db_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
