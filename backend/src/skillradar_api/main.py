from fastapi import FastAPI

from skillradar_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend service for grounded study lesson generation.",
)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get(settings.api_prefix, tags=["system"])
def api_root() -> dict[str, str]:
    return {"message": "SkillRadar backend is ready."}
