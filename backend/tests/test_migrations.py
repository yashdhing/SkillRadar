from __future__ import annotations

import os
from pathlib import Path
import subprocess

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_expected_tables(sqlite_url: str) -> None:
    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/alembic")
    os.environ["SKILLRADAR_DATABASE_URL"] = sqlite_url

    try:
        command.upgrade(config, "head")
    finally:
        os.environ.pop("SKILLRADAR_DATABASE_URL", None)

    engine = create_engine(sqlite_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "alembic_version",
        "generation_requests",
        "lesson_sources",
        "lessons",
        "user_profile",
    }

    lessons_columns = {column["name"] for column in inspector.get_columns("lessons")}
    assert {"slug", "status", "mode", "toc_json", "metadata_json", "is_active"} <= lessons_columns

    indexes = inspector.get_indexes("lessons")
    assert any(index["name"] == "ix_lessons_single_active" for index in indexes)


def test_alembic_offline_sql_targets_postgres_dialect(tmp_path: Path) -> None:
    sql_output = tmp_path / "offline.sql"
    env = os.environ.copy()
    env["SKILLRADAR_DATABASE_URL"] = (
        "postgresql+psycopg://skillradar:skillradar@localhost:5432/skillradar"
    )
    result = subprocess.run(
        [
            "../backend/.venv/bin/alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd="backend",
    )
    sql_output.write_text(result.stdout)

    sql_text = sql_output.read_text()
    assert "CREATE TABLE user_profile" in sql_text
    assert "CREATE TABLE lessons" in sql_text
    assert "CREATE UNIQUE INDEX ix_lessons_single_active" in sql_text
    assert sql_text.count("CREATE TYPE lesson_mode") == 1
    assert sql_text.count("CREATE TYPE lesson_status") == 1
    assert sql_text.count("CREATE TYPE generation_request_status") == 1
