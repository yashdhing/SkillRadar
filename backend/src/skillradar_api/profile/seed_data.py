from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_USER_PROFILE_ID = "2d0f4bfe-9e8f-4c5d-97f2-4b1f53f5231d"

DEFAULT_USER_PROFILE: dict[str, Any] = {
    "id": DEFAULT_USER_PROFILE_ID,
    "name": "Yash Dhing",
    "role_title": "SDE3",
    "bio": (
        "SDE3 at Flipkart focused on backend systems, distributed architecture, "
        "reliability, platform modernization, and practical AI-assisted engineering."
    ),
    "skills_json": [
        "Java",
        "Groovy",
        "Python",
        "SQL",
        "Dropwizard",
        "Kafka",
        "Aerospike",
        "HBase",
        "MySQL",
        "Qdrant",
        "Spark",
        "Elastic Search",
        "Kubernetes",
        "Docker",
        "CI/CD",
        "System design",
        "Microservices",
        "Async workflows",
        "Reliability engineering",
        "Incident response",
        "Infrastructure modernization",
        "Fraud detection",
        "Platform tooling",
    ],
    "experience_json": [
        {
            "theme": "Large-scale backend systems",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Returns, incident management, workflow redesign",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Reporting pipelines and near-real-time processing",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Fraud detection using embeddings and similarity search",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Trust and safety platforms",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Big-sale readiness and reliability engineering",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Infrastructure modernization and platform migrations",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "On-call ownership and RCA leadership",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
        {
            "theme": "Mentorship and engineering leadership",
            "category": "current_career_theme",
            "evidence": "Confirmed in current and recent career themes.",
        },
    ],
    "topic_preferences_json": [
        {
            "topic": "Java/JVM performance and modern backend practices",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Distributed systems design and failure handling",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Kafka/event-driven architecture",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Datastores and storage tradeoffs",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Reliability engineering, incident response, observability",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Kubernetes/platform engineering",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "AI-assisted engineering workflows",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Production ML/embeddings/vector-search use cases",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
        {
            "topic": "Architecture and leadership topics relevant to an SDE3+",
            "category": "rank_higher",
            "evidence": "Confirmed under topics that should likely rank higher.",
        },
    ],
}


def get_default_user_profile() -> dict[str, Any]:
    return deepcopy(DEFAULT_USER_PROFILE)

