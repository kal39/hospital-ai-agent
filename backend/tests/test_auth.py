
import asyncio

import pytest
from fastapi import HTTPException

from app.core.auth import get_current_patient_id


def test_valid_first_synthetic_patient() -> None:
    patient_id = asyncio.run(
        get_current_patient_id(demo_patient_id="patient-001")
    )
    assert patient_id == "patient-001"


def test_valid_second_synthetic_patient() -> None:
    patient_id = asyncio.run(
        get_current_patient_id(demo_patient_id="patient-002")
    )
    assert patient_id == "patient-002"


@pytest.mark.parametrize(
    "patient_id",
    [None, "patient-999", ""],
)
def test_missing_or_unknown_patient_is_rejected(
    patient_id: str | None,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            get_current_patient_id(demo_patient_id=patient_id)
        )

    assert exc_info.value.status_code == 401
