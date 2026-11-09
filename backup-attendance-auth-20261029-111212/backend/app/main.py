from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.appointments import router as appointments_router
from app.api.chat import router as chat_router
from app.api.appointment_requests import router as appointment_requests_router
from app.api.patients import router as patients_router
from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the hospital patient-portal AI assistant.",
    version=settings.app_version,
)

# Only permit localhost origins during development.
# In production, configure frontend_origin to the exact deployed frontend origin.
configured_origin = settings.frontend_origin.strip().rstrip("/")
allowed_origins = [configured_origin] if configured_origin else []

if settings.environment.strip().lower() == "development":
    allowed_origins.extend(
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )

# Remove duplicate origins while preserving their order.
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Demo-Patient-Id",
    ],
)

# Apply rate limiting to requests handled by the application.
# The middleware excludes /health so health checks remain available.
app.add_middleware(RateLimitMiddleware)

# Register API routes.
app.include_router(patients_router)
app.include_router(appointment_requests_router)
app.include_router(appointments_router)
app.include_router(chat_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Check whether the Python backend is running."""
    return {
        "status": "ok",
        "service": "hospital-ai-agent",
        "environment": settings.environment,
    }
