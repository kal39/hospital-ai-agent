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



def test_amharic_synthetic_notice_is_readable():
    response = (
        "\u12e8\u1240\u1320\u122e \u1218\u1228\u1303\u12ce "
        "\u12a5\u12da\u1205 \u12a0\u1208\u1362"
    )

    result = _add_synthetic_data_disclosure(response, "am")

    assert response in result
    assert "\u12e8\u121b\u1233\u12eb \u1218\u12dd\u1308\u1266\u127d" in result
    assert "\u12e8\u1206\u1235\u1352\u1273\u120d \u1235\u122d\u12d3\u1275" in result
    assert "\u003f" not in result
    assert result.count(
        "\u12e8\u121b\u1235\u1273\u12c8\u123b \u121b\u1233\u1230\u1262\u12eb\u1366"
    ) == 1


def test_amharic_synthetic_notice_is_not_duplicated():
    response = (
        "\u12e8\u1240\u1320\u122e \u1218\u1228\u1303\u12ce "
        "\u12a5\u12da\u1205 \u12a0\u1208\u1362\n\n"
        "\u12e8\u121b\u1235\u1273\u12c8\u123b \u121b\u1233\u1230\u1262\u12eb\u1366 "
        "\u12e8\u121a\u12a8\u1270\u1208\u12cd \u1218\u1228\u1303 "
        "\u1208\u1219\u12a8\u122b \u12a8\u1270\u1348\u1320\u1229 "
        "\u12e8\u121b\u1233\u12eb \u1218\u12dd\u1308\u1266\u127d "
        "\u12e8\u1270\u1308\u1298 \u1290\u12cd\u1364"
    )

    result = _add_synthetic_data_disclosure(response, "am")

    assert "\u12e8\u1240\u1320\u122e" in result
    assert result.count(
        "\u12e8\u121b\u1235\u1273\u12c8\u123b \u121b\u1233\u1230\u1262\u12eb\u1366"
    ) == 1
