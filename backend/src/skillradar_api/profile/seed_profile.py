from __future__ import annotations

from skillradar_api.db.session import session_scope
from skillradar_api.profile.service import seed_default_user_profile


def main() -> None:
    with session_scope() as session:
        seed_default_user_profile(session)


if __name__ == "__main__":
    main()
