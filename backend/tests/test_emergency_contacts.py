from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import emergency_contacts as emergency_api
from app.main import app
from app.services import emergency_contacts as contact_service
from app.services import emergency_directory as directory_service
from app.services.agent import _emergency_response_metadata


client = TestClient(app)


def make_settings(**overrides):
    values = {
        "hospital_name": "",
        "hospital_emergency_phone": None,
        "ambulance_dispatch_phone": None,
        "alternative_emergency_phone": None,
        "hospital_address": "",
        "emergency_directions": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_contacts_are_not_configured_when_no_numbers_exist(monkeypatch):
    monkeypatch.setattr(
        contact_service,
        "get_settings",
        lambda: make_settings(
            hospital_name="Example Hospital",
            hospital_address="Example Address",
        ),
    )

    result = contact_service.get_emergency_contacts()

    assert result["active"] is True
    assert result["contactAvailability"] == "not_configured"
    assert result["hospitalName"] == "Example Hospital"
    assert result["hospitalAddress"] == "Example Address"
    assert result["hospitalEmergencyPhone"] is None
    assert result["ambulanceDispatchPhone"] is None


def test_contacts_are_partially_configured_with_one_primary_number(monkeypatch):
    monkeypatch.setattr(
        contact_service,
        "get_settings",
        lambda: make_settings(
            hospital_emergency_phone="+251 11 123 4567",
        ),
    )

    result = contact_service.get_emergency_contacts()

    assert result["contactAvailability"] == "partially_configured"
    assert result["hospitalEmergencyPhone"] == "+251 11 123 4567"
    assert result["ambulanceDispatchPhone"] is None


def test_alternative_number_alone_is_partial_configuration(monkeypatch):
    monkeypatch.setattr(
        contact_service,
        "get_settings",
        lambda: make_settings(
            alternative_emergency_phone="+251 91 123 4567",
        ),
    )

    result = contact_service.get_emergency_contacts()

    assert result["contactAvailability"] == "partially_configured"
    assert result["alternativeEmergencyPhone"] == "+251 91 123 4567"


def test_both_primary_numbers_mean_fully_configured(monkeypatch):
    monkeypatch.setattr(
        contact_service,
        "get_settings",
        lambda: make_settings(
            hospital_emergency_phone="+251 11 123 4567",
            ambulance_dispatch_phone="+251 91 123 4567",
        ),
    )

    result = contact_service.get_emergency_contacts()

    assert result["contactAvailability"] == "configured"
    assert result["hospitalEmergencyPhone"] == "+251 11 123 4567"
    assert result["ambulanceDispatchPhone"] == "+251 91 123 4567"


def test_contact_values_are_trimmed_and_empty_values_become_none(monkeypatch):
    monkeypatch.setattr(
        contact_service,
        "get_settings",
        lambda: make_settings(
            hospital_name="  Example Hospital  ",
            hospital_address="   ",
            emergency_directions="  Main entrance  ",
        ),
    )

    result = contact_service.get_emergency_contacts()

    assert result["hospitalName"] == "Example Hospital"
    assert result["hospitalAddress"] is None
    assert result["emergencyDirections"] == "Main entrance"


def test_public_emergency_contacts_endpoint_returns_contact_data(monkeypatch):
    expected = {
        "active": True,
        "contactAvailability": "not_configured",
        "hospitalName": None,
        "hospitalEmergencyPhone": None,
        "ambulanceDispatchPhone": None,
        "alternativeEmergencyPhone": None,
        "hospitalAddress": None,
        "emergencyDirections": None,
    }

    monkeypatch.setattr(
        emergency_api,
        "get_emergency_contacts",
        lambda: expected,
    )

    response = client.get("/api/emergency-contacts")

    assert response.status_code == 200
    assert response.json() == expected


def test_emergency_metadata_falls_back_if_contact_service_fails(monkeypatch):
    def fail_to_load_contacts():
        raise RuntimeError("Contact configuration unavailable")

    monkeypatch.setattr(
        contact_service,
        "get_emergency_contacts",
        fail_to_load_contacts,
    )

    result = _emergency_response_metadata()

    assert result["active"] is True
    assert result["contactAvailability"] == "not_configured"
    assert result["hospitalEmergencyPhone"] is None
    assert result["ambulanceDispatchPhone"] is None


def test_emergency_directory_contains_only_fictional_profiles():
    result = directory_service.get_emergency_directory()

    assert result["dataType"] == "fictional_demo"
    assert result["facilityName"] == "Demo General Hospital"
    assert result["departmentName"] == "Emergency Department"
    assert len(result["doctors"]) == 3

    for doctor in result["doctors"]:
        assert doctor["profileType"] == "fictional_demo"
        assert doctor["availability"] == "not_provided"


def test_public_emergency_directory_endpoint_returns_directory(monkeypatch):
    expected = directory_service.get_emergency_directory()

    monkeypatch.setattr(
        emergency_api,
        "get_emergency_directory",
        lambda: expected,
    )

    response = client.get("/api/emergency-directory")

    assert response.status_code == 200
    assert response.json() == expected


def test_emergency_metadata_includes_directory_when_contacts_fail(monkeypatch):
    def fail_to_load_contacts():
        raise RuntimeError("Contact configuration unavailable")

    monkeypatch.setattr(
        contact_service,
        "get_emergency_contacts",
        fail_to_load_contacts,
    )

    result = _emergency_response_metadata()

    assert result["active"] is True
    assert result["contactAvailability"] == "not_configured"
    assert result["directory"] == directory_service.get_emergency_directory()


def test_emergency_metadata_survives_directory_failure(monkeypatch):
    def fail_to_load_directory():
        raise RuntimeError("Directory unavailable")

    monkeypatch.setattr(
        directory_service,
        "get_emergency_directory",
        fail_to_load_directory,
    )

    result = _emergency_response_metadata()

    assert result["active"] is True
    assert result["contactAvailability"] in {
        "not_configured",
        "partially_configured",
        "configured",
    }
    assert result["directory"] is None
