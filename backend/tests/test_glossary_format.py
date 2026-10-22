from app.services.glossary import get_glossary_context


def test_glossary_entries_use_real_line_breaks():
    context = get_glossary_context()

    assert "\\n" not in context
    assert "\n" in context
    assert "Hemoglobin:" in context
    assert "Fasting Blood Glucose:" in context


def test_glossary_does_not_claim_unapproved_amharic_translations():
    context = get_glossary_context()

    assert "Do not invent medical translations." in context
    assert "unavailable until reviewed" in context
