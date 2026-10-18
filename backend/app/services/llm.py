
"""Gemini LLM integration with approved hospital tool calling."""

import asyncio
import re
from typing import Any, Literal

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.services.tool_definitions import HOSPITAL_TOOL_DEFINITIONS
from app.services.tool_executor import execute_hospital_tool

MAX_TOOL_ROUNDS = 5
MAX_ATTEMPTS = 2

DetailLevel = Literal["short", "normal", "detailed"]
DETAIL_OUTPUT_TOKENS: dict[str, int] = {
    "short": 500,
    "normal": 2800,
    "detailed": 4500,
}

ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


def _is_retryable_error(error: Exception) -> bool:
    """Identify errors that may succeed on retry or fallback."""
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "503",
            "unavailable",
            "high demand",
            "fetch failed",
            "connect timeout",
            "timeout",
            "429",
            "resource_exhausted",
        )
    )


def _safe_error_summary(error: Exception) -> str:
    """Return a short diagnostic summary without obvious secret values."""
    message = str(error)

    message = re.sub(
        r"AIza[0-9A-Za-z_-]{20,}",
        "[REDACTED_API_KEY]",
        message,
    )
    message = re.sub(
        r"(?i)(api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        message,
    )

    message = " ".join(message.split())
    return message[:300] if message else "(no error message)"


def _response_object(value: Any) -> dict[str, Any]:
    """Wrap non-object tool results in an object."""
    if isinstance(value, dict):
        return value
    return {"data": value}


def _build_tool_declarations() -> list[types.FunctionDeclaration]:
    """Build Gemini declarations from the approved tool schemas."""
    declarations: list[types.FunctionDeclaration] = []

    for tool in HOSPITAL_TOOL_DEFINITIONS:
        parameters = tool.get(
            "parameters",
            {"type": "OBJECT", "properties": {}},
        )

        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=parameters,
            )
        )

    return declarations


class GeminiLLMService:
    """Generate responses and execute approved tools for one patient."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = (
            genai.Client(api_key=self.settings.llm_api_key)
            if self.settings.llm_api_key.strip()
            else None
        )
        self.tool_names = {
            tool["name"] for tool in HOSPITAL_TOOL_DEFINITIONS
        }
        self.tool_declarations = _build_tool_declarations()

    def _require_client(self) -> genai.Client:
        if self.client is None:
            raise RuntimeError(
                "The hospital AI service is not configured. "
                "Check the backend environment configuration."
            )
        return self.client

    async def _generate_with_retry(
        self,
        *,
        system_instruction: str,
        contents: list[types.Content],
        max_output_tokens: int,
    ) -> Any:
        """Try configured Gemini models with bounded retries."""
        client = self._require_client()

        models = list(
            dict.fromkeys(
                model.strip()
                for model in (
                    self.settings.llm_model,
                    self.settings.llm_fallback_model,
                )
                if model.strip()
            )
        )

        last_error: Exception | None = None

        for model in models:
            for attempt in range(MAX_ATTEMPTS):
                try:
                    return await client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=[
                                types.Tool(
                                    function_declarations=(
                                        self.tool_declarations
                                    )
                                )
                            ],
                            max_output_tokens=max_output_tokens,
                            temperature=0.2,
                        ),
                    )
                except Exception as error:  # noqa: BLE001
                    last_error = error
                    status = getattr(error, "code", None)
                    status_text = (
                        f", status={status}" if status is not None else ""
                    )

                    print(
                        "[LLM] Gemini request failed: "
                        f"model={model!r}, "
                        f"error_type={type(error).__name__}"
                        f"{status_text}, "
                        f"attempt={attempt + 1}/{MAX_ATTEMPTS}, "
                        f"detail={_safe_error_summary(error)}"
                    )

                    if not _is_retryable_error(error):
                        break

                    if attempt + 1 < MAX_ATTEMPTS:
                        await asyncio.sleep(1)

        if last_error is not None and _is_retryable_error(last_error):
            raise RuntimeError(
                "The AI service is temporarily unavailable. "
                "Please try again in a moment."
            ) from last_error

        raise RuntimeError("Gemini request failed.") from last_error

    async def generate_with_tools(
        self,
        *,
        system_instruction: str,
        user_message: str,
        conversation_history: list[dict[str, str]],
        patient_id: str,
        detail: DetailLevel = "normal",
        image: dict[str, str] | None = None,
        allow_appointment_discovery: bool = False,
    ) -> dict[str, Any]:
        """Generate a response and execute approved tools for one patient."""
        self._require_client()

        if not patient_id or not patient_id.strip():
            raise ValueError(
                "Authenticated patient identity is required."
            )

        if detail not in DETAIL_OUTPUT_TOKENS:
            raise ValueError("Unsupported response detail level.")

        output_token_budget = DETAIL_OUTPUT_TOKENS[detail]
        contents: list[types.Content] = []

        for item in conversation_history:
            role = item.get("role")
            content = item.get("content", "")

            if role not in {"user", "assistant"} or not content:
                continue

            contents.append(
                types.Content(
                    role="model" if role == "assistant" else "user",
                    parts=[types.Part(text=content)],
                )
            )

        current_parts = [types.Part(text=user_message)]

        if image is not None:
            data_url = image.get("dataUrl", "")
            mime_type = image.get("mimeType", "")

            if mime_type not in ALLOWED_ATTACHMENT_TYPES:
                raise ValueError("Unsupported attachment type.")

            if "," not in data_url:
                raise ValueError("Invalid attachment data.")

            base64_data = data_url.split(",", 1)[1].strip()
            if not base64_data:
                raise ValueError("Invalid attachment data.")

            current_parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=base64_data,
                    )
                )
            )

        contents.append(
            types.Content(role="user", parts=current_parts)
        )

        tools_used: list[str] = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._generate_with_retry(
                system_instruction=system_instruction,
                contents=contents,
                max_output_tokens=output_token_budget,
            )

            candidate = (
                response.candidates[0]
                if response.candidates
                else None
            )
            model_content = candidate.content if candidate else None

            # Log response completion metadata only; never log patient content.
            finish_reason = (
                getattr(candidate, "finish_reason", None)
                if candidate is not None
                else None
            )
            usage = getattr(response, "usage_metadata", None)
            candidate_tokens = (
                getattr(usage, "candidates_token_count", None)
                if usage is not None
                else None
            )
            print(
                "[LLM] Response diagnostics: "
                f"finish_reason={finish_reason}, "
                f"candidate_tokens={candidate_tokens}"
            )

            function_calls = response.function_calls or []

            if not function_calls:
                message = response.text
                if not message:
                    raise RuntimeError(
                        "Gemini returned no text response."
                    )

                return {
                    "message": message,
                    "toolsUsed": tools_used,
                }

            if model_content is None:
                raise RuntimeError(
                    "Gemini requested a tool but returned no model content."
                )

            contents.append(model_content)
            function_responses: list[types.Part] = []

            for call in function_calls:
                tool_name = call.name

                if not tool_name:
                    raise RuntimeError(
                        "Gemini returned a function call without a name."
                    )

                if tool_name not in self.tool_names:
                    raise ValueError(
                        "Unauthorized or unknown hospital tool: "
                        f"{tool_name}"
                    )

                arguments = call.args or {}

                if not isinstance(arguments, dict):
                    raise ValueError(
                        f"Invalid arguments for hospital tool: {tool_name}"
                    )

                # The patient identity and appointment permission come
                # from trusted backend context, never Gemini arguments.
                try:
                    result = execute_hospital_tool(
                        tool_name=tool_name,
                        patient_id=patient_id,
                        arguments=arguments,
                        allow_appointment_discovery=(
                            allow_appointment_discovery
                        ),
                    )
                except PermissionError:
                    # Do not execute or report a denied tool as used.
                    result = {
                        "error": (
                            "Appointment discovery is not authorized for "
                            "this request. Do not retry the appointment tool. "
                            "Ask the patient for explicit consent first."
                        )
                    }
                else:
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)

                function_responses.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response=_response_object(result),
                    )
                )

            contents.append(
                types.Content(
                    role="user",
                    parts=function_responses,
                )
            )

        raise RuntimeError(
            f"Gemini exceeded the maximum of {MAX_TOOL_ROUNDS} "
            "tool-calling rounds."
        )


gemini_llm_service = GeminiLLMService()
