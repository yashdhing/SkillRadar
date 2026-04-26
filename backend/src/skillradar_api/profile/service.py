from __future__ import annotations

from sqlalchemy.orm import Session

from skillradar_api.db.models import UserProfile
from skillradar_api.db.repositories import UserProfileRepository
from skillradar_api.profile.seed_data import get_default_user_profile


def seed_default_user_profile(session: Session) -> UserProfile:
    repository = UserProfileRepository(session)
    profile_data = get_default_user_profile()
    existing = repository.get_by_id(profile_data["id"])

    if existing is None:
        profile = UserProfile(**profile_data)
        repository.add(profile)
        session.flush()
        return profile

    existing.name = profile_data["name"]
    existing.role_title = profile_data["role_title"]
    existing.bio = profile_data["bio"]
    existing.skills_json = profile_data["skills_json"]
    existing.experience_json = profile_data["experience_json"]
    existing.topic_preferences_json = profile_data["topic_preferences_json"]
    session.flush()
    return existing
