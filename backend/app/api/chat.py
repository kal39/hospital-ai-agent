
"""Chat endpoint for the Hospital AI Assistant."""

import base64
import binascii
import re
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import get_current_patient_id
from app.core.config import get_settings
from app.services.agent import hospital_agent_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


class ChatAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fileName: str = Field(min_length=1, max_length=255)
    mimeType: Literal[
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    ]
    dataUrl: str = Field(max_length=7_100_000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(default="", max_length=10_000)
    conversationId: str | None = Field(default=None, max_length=128)
    language: Literal["en", "am"] = "en"
    detail: Literal["short", "normal", "detailed"] = "normal"
    image: ChatAttachment | None = None


def validate_attachment(attachment: ChatAttachment) -> None:
    """Validate the uploaded file before sending it to the AI provider."""
    if not attachment.fileName.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The attachment filename is invalid.",
        )

    prefix = f"data:{attachment.mimeType};base64,"

    if not attachment.dataUrl.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The attachment data does not match its declared file type.",
        )

    encoded = attachment.dataUrl[len(prefix):]

    if (
        not encoded
        or len(encoded) % 4 != 0
        or not re.fullmatch(
            r"(?:[A-Za-z0-9+/]{4})*"
            r"(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?",
            encoded,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The attachment data is not valid Base64.",
        )

    try:
        file_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The attachment data is not valid Base64.",
        ) from None

    if not file_bytes or len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file must be greater than 0 bytes and no larger than 5 MB.",
        )

    # Verify file signatures; do not trust the supplied MIME type alone.
    if attachment.mimeType == "image/jpeg":
        valid_signature = file_bytes.startswith(b"\xff\xd8\xff")
    elif attachment.mimeType == "image/png":
        valid_signature = file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    elif attachment.mimeType == "image/webp":
        valid_signature = (
            len(file_bytes) >= 12
            and file_bytes[:4] == b"RIFF"
            and file_bytes[8:12] == b"WEBP"
        )
    else:
        valid_signature = file_bytes.startswith(b"%PDF-")

    if not valid_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file content does not match the declared file type.",
        )


@router.post("")
async def chat(
    body: ChatRequest,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict:
    """Process a message using the authenticated patient's records."""
    message = body.message.strip()

    if len(message) > get_settings().max_message_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Message cannot exceed "
                f"{get_settings().max_message_length} characters."
            ),
        )

    if not message and body.image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a message or attach a file.",
        )

    attachment = None

    if body.image is not None:
        validate_attachment(body.image)
        attachment = body.image.model_dump()

    conversation_id = body.conversationId or str(uuid4())

    try:
        result = await hospital_agent_service.run(
            user_message=message,
            patient_id=patient_id,
            conversation_id=conversation_id,
            language=body.language,
            detail=body.detail,
            image=attachment,
        )
    except RuntimeError as exc:
        if "temporarily unavailable" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable. Please try again.",
            ) from None

        print("[CHAT] AI request failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant could not process your request.",
        ) from None
    except Exception:
        print("[CHAT] Unexpected chat processing failure.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI assistant could not process your request.",
        ) from None

    safety_flag = result.get("safetyFlag", False)

    return {
        "conversationId": conversation_id,
        "message": result["message"],
        "language": body.language,
        "detail": body.detail,
        "toolsUsed": result.get("toolsUsed", []),
        "safetyFlag": safety_flag,
        "safety": {"requiresAttention": safety_flag},
    }
