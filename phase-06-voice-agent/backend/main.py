"""Phase 06 FastAPI app — Voice Agent API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings
from backend.routers.voice_router import router as voice_router

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app = FastAPI(title="Phase 06 Voice Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(voice_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "06-voice-agent"}
