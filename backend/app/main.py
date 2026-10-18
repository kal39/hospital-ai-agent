
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.patients import router as patients_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the hospital patient-portal AI assistant.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Demo-Patient-Id",
    ],
)

# Register API routes
app.include_router(patients_router)
app.include_router(chat_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Check whether the Python backend is running."""
    return {
        "status": "ok",
        "service": "hospital-ai-agent",
        "environment": settings.environment,
    }
