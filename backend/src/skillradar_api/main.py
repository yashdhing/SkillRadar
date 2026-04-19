from fastapi import FastAPI

app = FastAPI(
    title="SkillRadar API",
    version="0.1.0",
    description="Backend service for grounded study lesson generation.",
)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1", tags=["system"])
def api_root() -> dict[str, str]:
    return {"message": "SkillRadar backend is ready."}

