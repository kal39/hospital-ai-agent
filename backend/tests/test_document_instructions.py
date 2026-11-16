
"""Regression tests for uploaded-document explanation instructions."""

from app.services.agent import _system_instruction


def test_document_instructions_require_natural_amharic():
    instruction = _system_instruction("am", "normal")

    assert "Amharic" in instruction
    assert "grammatically correct" in instruction
    assert "word-for-word translation" in instruction
    assert "official English names" in instruction


def test_document_instructions_avoid_irrelevant_medical_explanations():
    instruction = _system_instruction("en", "normal")

    assert "Match the document's subject" in instruction
    assert "Do not invent" in instruction
    assert "untrusted data" in instruction


def test_combined_medical_summary_instructions_select_relevant_tools():
    instruction = _system_instruction("en", "normal")

    assert "COMBINED MEDICAL RECORD SUMMARIES" in instruction
    assert "getMedicalHistory" in instruction
    assert "getLatestLabResults" in instruction
    assert "compareLabResults" in instruction
    assert "getMedications" in instruction
    assert "getPatientProfile" in instruction
    assert "getUpcomingAppointments" in instruction


def test_combined_medical_summary_instructions_preserve_record_accuracy():
    instruction = " ".join(_system_instruction("en", "normal").split())

    assert "chronological order" in instruction
    assert "date is not available" in instruction
    assert "Do not call unrelated tools" in instruction
    assert "not a diagnosis" in instruction