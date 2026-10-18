
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.data.patients import PATIENTS


async def get_current_patient_id(
    demo_patient_id: Annotated[
        str | None,
        Header(alias="X-Demo-Patient-Id"),
    ] = None,
) -> str:
    """Resolve a synthetic patient for local development only."""
    settings = get_settings()

    if (
        settings.environment.lower() != "development"
        or not settings.demo_auth_enabled
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hospital portal authentication is not configured.",
        )

    if not demo_patient_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing demo patient authentication.",
        )

    if demo_patient_id not in PATIENTS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo patient authentication.",
        )

    return demo_patient_id
