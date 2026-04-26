from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from skillradar_api.db.base import Base
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
