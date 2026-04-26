from skillradar_api.db.repositories import UserProfileRepository
from skillradar_api.profile.seed_data import DEFAULT_USER_PROFILE_ID
from skillradar_api.profile.service import seed_default_user_profile


def test_seed_default_user_profile_persists_confirmed_profile(session) -> None:
    seeded_profile = seed_default_user_profile(session)
    session.commit()

    stored_profile = UserProfileRepository(session).get_by_id(DEFAULT_USER_PROFILE_ID)

    assert stored_profile is not None
    assert stored_profile.id == DEFAULT_USER_PROFILE_ID
    assert stored_profile.name == "Yash Dhing"
    assert stored_profile.role_title == "SDE3"
    assert "Flipkart" in (stored_profile.bio or "")
    assert "Kafka" in stored_profile.skills_json
    assert any(
        entry["theme"] == "Trust and safety platforms"
        for entry in stored_profile.experience_json
    )
    assert any(
        entry["topic"] == "AI-assisted engineering workflows"
        for entry in stored_profile.topic_preferences_json
    )
    assert len(stored_profile.topic_preferences_json) == 9
    assert seeded_profile.id == DEFAULT_USER_PROFILE_ID


def test_seed_default_user_profile_is_idempotent_and_refreshes_data(session) -> None:
    first_profile = seed_default_user_profile(session)
    session.commit()

    first_profile.bio = "outdated bio"
    first_profile.skills_json = ["Legacy Skill"]
    session.commit()

    refreshed_profile = seed_default_user_profile(session)
    session.commit()

    stored_profile = UserProfileRepository(session).get_by_id(DEFAULT_USER_PROFILE_ID)

    assert refreshed_profile.id == DEFAULT_USER_PROFILE_ID
    assert stored_profile is not None
    assert stored_profile.bio != "outdated bio"
    assert "Legacy Skill" not in stored_profile.skills_json
    assert "Java" in stored_profile.skills_json
