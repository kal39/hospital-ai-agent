from app.services.agent import _add_synthetic_data_disclosure


def test_synthetic_notice_preserves_blood_type_answer():
    response = "Your recorded blood type is O+."

    result = _add_synthetic_data_disclosure(response, "en")

    assert "Your recorded blood type is O+." in result
    assert "Synthetic-data notice:" in result
    assert "fictional demonstration records" in result


def test_synthetic_notice_is_not_duplicated():
    response = (
        "Your recorded blood type is O+.\n\n"
        "Synthetic-data notice: The following information comes from "
        "fictional demonstration records, not verified records from "
        "a live hospital system. Verify it with your healthcare "
        "professional before relying on it for clinical decisions."
    )

    result = _add_synthetic_data_disclosure(response, "en")

    assert "Your recorded blood type is O+." in result
    assert result.count("Synthetic-data notice:") == 1


def test_synthetic_notice_preserves_numbered_appointment_options():
    response = (
        "These are fictional local demonstration slots, not live "
        "hospital availability.\n"
        "No appointment has been booked. Reply with an option number "
        "to select a slot:\n\n"
        "1. Dr. Hana Tesfaye - General Medicine - 2026-10-20 "
        "at 09:00 - Synthetic Demo Clinic A - "
        "2 places remaining in this demo slot\n"
        "2. Dr. Hana Tesfaye - General Medicine - 2026-10-20 "
        "at 10:30 - Synthetic Demo Clinic A - "
        "2 places remaining in this demo slot\n\n"
        "Choose a number. I will ask you to confirm the exact "
        "selection before creating a demo booking.\n"
        "This is a fictional demonstration only, not a real "
        "hospital appointment."
    )

    result = _add_synthetic_data_disclosure(response, "en")

    assert "Synthetic-data notice:" in result
    assert "1. Dr. Hana Tesfaye" in result
    assert "2. Dr. Hana Tesfaye" in result
    assert "Synthetic Demo Clinic A" in result
    assert "Choose a number." in result
    assert result.count("Synthetic-data notice:") == 1
