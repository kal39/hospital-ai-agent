
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
