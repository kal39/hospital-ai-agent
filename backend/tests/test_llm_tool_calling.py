from types import SimpleNamespace

import pytest
from google.genai import types

import app.services.llm as llm_module
from app.services.llm import GeminiLLMService


@pytest.mark.asyncio
async def test_profile_tool_result_reaches_gemini_and_final_answer():
    service = GeminiLLMService()

    # This test mocks Gemini's responses but uses the real profile tool.
    service._require_client = lambda: object()

    tool_call = types.FunctionCall(
        name="getPatientProfile",
        args={},
    )
    first_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=types.Content(
                    role="model",
                    parts=[types.Part(function_call=tool_call)],
                ),
                finish_reason=None,
            )
        ],
        function_calls=[tool_call],
        usage_metadata=None,
        text=None,
    )

    final_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="Your recorded blood type is O+."
                        )
                    ],
                ),
                finish_reason=None,
            )
        ],
        function_calls=[],
        usage_metadata=None,
        text="Your recorded blood type is O+.",
    )

    responses = iter([first_response, final_response])
    captured_requests = []

    async def fake_generate_with_retry(**kwargs):
        captured_requests.append(kwargs)
        return next(responses)

    service._generate_with_retry = fake_generate_with_retry

    result = await service.generate_with_tools(
        system_instruction="Answer using authorized patient records.",
        user_message=(
            "What is my blood type? If it is missing, tell me."
        ),
        conversation_history=[],
        patient_id="patient-001",
        detail="normal",
    )

    assert len(captured_requests) == 2
    assert "getPatientProfile" in result["toolsUsed"]
    assert "O+" in result["message"]

    # Confirm the tool response was appended before Gemini's second call.
    second_call_contents = captured_requests[1]["contents"]
    assert any(
        getattr(part, "function_response", None) is not None
        for content in second_call_contents
        for part in (content.parts or [])
    )



@pytest.mark.asyncio
async def test_consented_discovery_hides_discovery_tools_from_gemini():
    service = GeminiLLMService()
    service._require_client = lambda: object()

    final_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="I can help explore options.")],
                ),
                finish_reason=None,
            )
        ],
        function_calls=[],
        usage_metadata=None,
        text="I can help explore options.",
    )

    captured_requests = []

    async def fake_generate_with_retry(**kwargs):
        captured_requests.append(kwargs)
        return final_response

    service._generate_with_retry = fake_generate_with_retry

    result = await service.generate_with_tools(
        system_instruction="Explore appointment options after consent.",
        user_message="Find appointment options.",
        conversation_history=[],
        patient_id="patient-001",
        detail="normal",
        allow_appointment_discovery=True,
    )

    assert result["message"] == "I can help explore options."
    assert len(captured_requests) == 1

    exposed_names = {
        declaration.name
        for declaration in captured_requests[0]["tool_declarations"]
    }

    assert "getPatientProfile" in exposed_names
    assert "getUpcomingAppointments" in exposed_names
    assert "findAppropriateDoctors" not in exposed_names
    assert "getAvailableAppointmentSlots" not in exposed_names
    assert "getQueueEstimate" not in exposed_names
