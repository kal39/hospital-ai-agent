
"""Approved Gemini tool definitions for the hospital assistant."""

EMPTY_PARAMETERS = {
    "type": "OBJECT",
    "properties": {},
}

HOSPITAL_TOOL_DEFINITIONS = [
    {
        "name": "getLatestLabResults",
        "description": "Get the authenticated patient's latest laboratory results.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "compareLabResults",
        "description": "Compare the authenticated patient's recorded laboratory results.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "getMedications",
        "description": "Get the authenticated patient's recorded medications and instructions.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "getMedicalHistory",
        "description": "Get the authenticated patient's recorded medical history.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "getPatientProfile",
        "description": "Get the authenticated patient's profile, including available demographic details, blood type, allergies, and other recorded profile fields. Use this tool to answer profile questions; report only fields returned and say when a field is missing.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "getUpcomingAppointments",
        "description": "Get the authenticated patient's upcoming scheduled appointments.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "getAppointmentPreparationContext",
        "description": "Get the authenticated patient's records relevant to preparing for an appointment.",
        "parameters": EMPTY_PARAMETERS,
    },
    {
        "name": "findAppropriateDoctors",
        "description": (
            "Find doctors in a requested department in the synthetic demo directory. "
            "The assigned doctor is prioritized when relevant, but this is not a clinical suitability decision."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "department": {
                    "type": "STRING",
                    "description": (
                        "Optional department, such as General Medicine "
                        "or Respiratory Clinic."
                    ),
                },
            },
        },
    },
    {
        "name": "getAvailableAppointmentSlots",
        "description": (
            "List generated synthetic appointment slots. These are demo slots, "
            "not real hospital availability, and no appointment is booked."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "doctorId": {
                    "type": "STRING",
                    "description": "Optional doctor ID from the demo directory.",
                },
                "department": {
                    "type": "STRING",
                    "description": "Optional department filter.",
                },
                "startDate": {
                    "type": "STRING",
                    "description": "Optional start date in YYYY-MM-DD format.",
                },
                "days": {
                    "type": "INTEGER",
                    "description": "Number of days to search, from 1 to 30. Defaults to 14.",
                },
            },
        },
    },
    {
        "name": "getQueueEstimate",
        "description": (
            "Return an illustrative synthetic queue estimate for a demo doctor "
            "and date. It is not live queue data."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "doctorId": {
                    "type": "STRING",
                    "description": "Doctor ID from the demo directory.",
                },
                "appointmentDate": {
                    "type": "STRING",
                    "description": "Optional date in YYYY-MM-DD format.",
                },
            },
            "required": ["doctorId"],
        },
    },
]
