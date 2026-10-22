"""Regression tests for chat attachment validation."""

import base64

import pytest
from fastapi import HTTPException

import app.api.chat as chat_module
from app.api.chat import ChatAttachment, validate_attachment


def make_attachment(
    mime_type: str,
    file_name: str,
    payload: bytes,
) -> ChatAttachment:
    """Build a data URL from test bytes."""
    encoded = base64.b64encode(payload).decode("ascii")
    return ChatAttachment(
        fileName=file_name,
        mimeType=mime_type,
        dataUrl=f"data:{mime_type};base64,{encoded}",
    )


@pytest.mark.parametrize(
    "mime_type,file_name,payload",
    [
        ("image/jpeg", "sample.jpg", b"\xff\xd8\xff\xe0"),
        ("image/png", "sample.png", b"\x89PNG\r\n\x1a\n"),
        ("image/webp", "sample.webp", b"RIFF\x00\x00\x00\x00WEBP"),
        ("application/pdf", "sample.pdf", b"%PDF-1.7\n"),
    ],
)
def test_allowed_file_signatures_pass_validation(
    mime_type,
    file_name,
    payload,
):
    """Recognized signatures pass the current file-type checks."""
    attachment = make_attachment(mime_type, file_name, payload)

    validate_attachment(attachment)


def test_mismatched_data_url_mime_type_is_rejected():
    attachment = ChatAttachment(
        fileName="sample.png",
        mimeType="image/png",
        dataUrl="data:image/jpeg;base64,/9j/",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400


def test_invalid_base64_is_rejected():
    attachment = ChatAttachment(
        fileName="sample.png",
        mimeType="image/png",
        dataUrl="data:image/png;base64,not base64!",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400
    assert "Base64" in exc_info.value.detail


def test_empty_file_is_rejected():
    attachment = ChatAttachment(
        fileName="empty.png",
        mimeType="image/png",
        dataUrl="data:image/png;base64,",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400


def test_wrong_file_signature_is_rejected():
    attachment = make_attachment(
        "image/png",
        "not-really-a-png.png",
        b"This is not a PNG file.",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400
    assert "content does not match" in exc_info.value.detail


def test_blank_filename_is_rejected():
    attachment = make_attachment(
        "image/png",
        " ",
        b"\x89PNG\r\n\x1a\n",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400


def test_file_exceeding_configured_size_limit_is_rejected(monkeypatch):
    """Exercise the size limit without allocating a 5 MB test file."""
    monkeypatch.setattr(chat_module, "MAX_FILE_SIZE_BYTES", 16)

    attachment = make_attachment(
        "image/png",
        "oversized.png",
        b"\x89PNG\r\n\x1a\n" + b"x" * 9,
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_attachment(attachment)

    assert exc_info.value.status_code == 400
    assert "5 MB" in exc_info.value.detail
