"""seed default user profile

Revision ID: 20260426_000002
Revises: 20260426_000001
Create Date: 2026-04-26 00:00:02
"""

from __future__ import annotations

import json

from alembic import context, op
import sqlalchemy as sa

from skillradar_api.profile.seed_data import get_default_user_profile


revision = "20260426_000002"
down_revision = "20260426_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    profile = get_default_user_profile()
    dialect_name = context.get_context().dialect.name

    def quoted(value: str) -> str:
        return value.replace("'", "''")

    def json_sql(value: object) -> str:
        payload = quoted(json.dumps(value))
        if dialect_name == "postgresql":
            return f"CAST('{payload}' AS JSON)"
        return f"'{payload}'"

    op.execute(
        sa.text(
            f"""
            INSERT INTO user_profile (
                id,
                name,
                role_title,
                bio,
                skills_json,
                experience_json,
                topic_preferences_json
            ) VALUES (
                '{quoted(profile["id"])}',
                '{quoted(profile["name"])}',
                '{quoted(profile["role_title"])}',
                '{quoted(profile["bio"])}',
                {json_sql(profile["skills_json"])},
                {json_sql(profile["experience_json"])},
                {json_sql(profile["topic_preferences_json"])}
            )
            """
        )
    )


def downgrade() -> None:
    profile = get_default_user_profile()
    profile_id = profile["id"].replace("'", "''")
    op.execute(sa.text(f"DELETE FROM user_profile WHERE id = '{profile_id}'"))
