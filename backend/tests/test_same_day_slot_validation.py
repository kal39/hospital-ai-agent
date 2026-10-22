from datetime import date, datetime, timedelta

import pytest

from app.data.scheduling import generate_synthetic_slots
from app.services.demo_scheduler import _validate_not_in_past


FIXED_NOW = datetime(2026, 10, 21, 12, 0)


def test_rejects_same_day_slot_in_the_past():
    with pytest.raises(ValueError, match="time has already passed"):
        _validate_not_in_past(date(2026, 10, 21), "09:00", FIXED_NOW)


def test_rejects_same_day_slot_at_current_minute():
    with pytest.raises(ValueError, match="time has already passed"):
        _validate_not_in_past(date(2026, 10, 21), "12:00", FIXED_NOW)


def test_allows_same_day_future_slot():
    _validate_not_in_past(date(2026, 10, 21), "13:00", FIXED_NOW)


def test_rejects_previous_date():
    with pytest.raises(ValueError, match="past"):
        _validate_not_in_past(date(2026, 10, 20), "14:30", FIXED_NOW)


def test_generator_hides_expired_slots_and_keeps_future_slots():
    slots = generate_synthetic_slots(
        doctor_id="doctor-001",
        start_date=date(2026, 10, 21),
        days=1,
        now=FIXED_NOW,
    )

    times = [slot["time"] for slot in slots]
    assert times == ["13:00", "14:30"]


def test_generator_keeps_all_slots_on_a_future_weekday():
    future_weekday = date(2026, 10, 21) + timedelta(days=7)

    while future_weekday.weekday() >= 5:
        future_weekday += timedelta(days=1)

    slots = generate_synthetic_slots(
        doctor_id="doctor-001",
        start_date=future_weekday,
        days=1,
        now=FIXED_NOW,
    )

    assert [slot["time"] for slot in slots] == [
        "09:00", "10:30", "13:00", "14:30"
    ]
