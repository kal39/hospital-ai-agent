
"""Hospital service for the local synthetic-data prototype.

Every patient-facing record returned by this service is explicitly labeled
as synthetic demonstration data. Replace these fixtures with authorized
hospital API calls before any production use.
"""

from datetime import date
from typing import Any

from app.data.patients import (
    APPOINTMENTS,
    LAB_RESULTS,
    MEDICAL_HISTORY,
    MEDICATIONS,
    PATIENTS,
)
from app.data.scheduling import (
    DATA_SOURCE,
    DOCTORS,
    PATIENT_CARE_TEAMS,
    generate_synthetic_slots,
)
from app.services.demo_scheduler import demo_scheduler


DATA_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This information comes from fictional "
    "local development records, not a live hospital system. Do not treat "
    "it as a verified real patient record. Verify information against an "
    "authorized hospital system before making clinical or scheduling decisions."
)


class HospitalService:
    """Access clearly labeled synthetic hospital records."""

    @staticmethod
    def _tag_record(record: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of a record with its demo source clearly labeled."""
        tagged = dict(record)
        tagged["dataSource"] = DATA_SOURCE
        tagged["dataNotice"] = DATA_NOTICE
        return tagged

    @classmethod
    def _tag_records(
        cls, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Label records without mutating the shared fixture dictionaries."""
        return [cls._tag_record(record) for record in records]

    def _require_patient(self, patient_id: str) -> dict[str, Any]:
        patient = PATIENTS.get(patient_id)
        if patient is None:
            raise ValueError("Patient record not found.")
        return patient

    def get_patient_profile(
        self, patient_id: str
    ) -> dict[str, Any] | None:
        patient = PATIENTS.get(patient_id)
        if patient is None:
            return None
        return self._tag_record(patient)

    def get_latest_lab_results(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        results = self.get_all_lab_results(patient_id)

        if not results:
            return []

        latest_date = max(result["date"] for result in results)
        return [
            result for result in results
            if result["date"] == latest_date
        ]

    def get_all_lab_results(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        return self._tag_records(LAB_RESULTS.get(patient_id, []))

    def get_medications(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        return self._tag_records(MEDICATIONS.get(patient_id, []))

    def get_medical_history(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        return self._tag_records(MEDICAL_HISTORY.get(patient_id, []))

    def get_upcoming_appointments(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        """Return this demo patient's future scheduled/confirmed visits."""
        self._require_patient(patient_id)
        today = date.today().isoformat()
        allowed_statuses = {"scheduled", "confirmed"}

        appointments = [
            appointment
            for appointment in APPOINTMENTS.get(patient_id, [])
            if appointment.get("date", "") >= today
            and appointment.get("status", "").lower()
            in allowed_statuses
        ]

        appointments.sort(
            key=lambda appointment: (
                appointment.get("date", ""),
                appointment.get("time", ""),
            )
        )
        return self._tag_records(appointments)

    def get_appointment_preparation_context(
        self, patient_id: str
    ) -> dict[str, Any]:
        """Return labeled demo records for appointment preparation."""
        patient = self._require_patient(patient_id)
        appointments = self.get_upcoming_appointments(patient_id)

        history = sorted(
            self.get_medical_history(patient_id),
            key=lambda item: item.get("date", ""),
            reverse=True,
        )

        return {
            "appointments": appointments,
            "profile": {
                "allergies": patient.get("allergies", []),
                "recordedDiagnoses": patient.get("diagnoses", []),
                "dataSource": DATA_SOURCE,
                "dataNotice": DATA_NOTICE,
            },
            "latestLabResults": self.get_latest_lab_results(patient_id),
            "medications": self.get_medications(patient_id),
            "recentMedicalHistory": history[:5],
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
            "notice": DATA_NOTICE,
        }

    def compare_lab_results(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        """Compare each test's two most recent synthetic results."""
        grouped: dict[str, list[dict[str, Any]]] = {}

        for result in self.get_all_lab_results(patient_id):
            grouped.setdefault(result["testName"], []).append(result)

        comparisons: list[dict[str, Any]] = []

        for test_name, results in grouped.items():
            results.sort(key=lambda result: result["date"])
            previous = results[-2] if len(results) >= 2 else None
            latest = results[-1] if results else None

            change = (
                round(latest["value"] - previous["value"], 2)
                if previous is not None and latest is not None
                else None
            )

            comparisons.append(
                {
                    "testName": test_name,
                    "previous": previous,
                    "latest": latest,
                    "change": change,
                    "dataSource": DATA_SOURCE,
                    "dataNotice": DATA_NOTICE,
                }
            )

        return comparisons

    def get_patient_care_team(
        self, patient_id: str
    ) -> dict[str, Any]:
        """Return the fictional assigned doctor for this demo patient."""
        self._require_patient(patient_id)
        assignment = PATIENT_CARE_TEAMS.get(patient_id)

        if assignment is None:
            return {
                "assignedDoctor": None,
                "department": None,
                "dataSource": DATA_SOURCE,
                "dataNotice": DATA_NOTICE,
            }

        doctor = next(
            (
                item for item in DOCTORS
                if item["id"] == assignment["doctorId"]
            ),
            None,
        )

        return {
            "assignedDoctor": dict(doctor) if doctor else None,
            "department": assignment["department"],
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
        }

    def find_appropriate_doctors(
        self,
        patient_id: str,
        department: str = "",
    ) -> dict[str, Any]:
        """List fictional doctors, placing the assigned demo doctor first."""
        self._require_patient(patient_id)
        assignment = PATIENT_CARE_TEAMS.get(patient_id, {})
        assigned_id = assignment.get("doctorId")
        requested_department = department.strip().casefold()

        matching = [
            dict(doctor)
            for doctor in DOCTORS
            if (
                not requested_department
                or doctor["department"].casefold()
                == requested_department
            )
        ]

        matching.sort(
            key=lambda doctor: (
                doctor["id"] != assigned_id,
                doctor["name"],
            )
        )

        for doctor in matching:
            doctor["isAssignedDoctor"] = (
                doctor["id"] == assigned_id
            )
            doctor["dataSource"] = DATA_SOURCE
            doctor["dataNotice"] = DATA_NOTICE

        return {
            "doctors": matching,
            "preferredDoctorId": assigned_id,
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
            "notice": (
                "Fictional demo doctor directory. Department matching "
                "does not determine clinical suitability."
            ),
        }

    def get_available_appointment_slots(
        self,
        patient_id: str,
        doctor_id: str = "",
        department: str = "",
        start_date: str = "",
        days: int = 14,
    ) -> dict[str, Any]:
        """Return generated demo slots, never live availability."""
        self._require_patient(patient_id)

        if not 1 <= days <= 30:
            raise ValueError("Days must be between 1 and 30.")

        start = date.today()

        if start_date:
            try:
                start = date.fromisoformat(start_date)
            except ValueError as error:
                raise ValueError(
                    "start_date must use YYYY-MM-DD format."
                ) from error

        if start < date.today():
            raise ValueError("start_date cannot be in the past.")

        if doctor_id and not any(
            doctor["id"] == doctor_id for doctor in DOCTORS
        ):
            raise ValueError("Doctor not found.")

        requested_department = department.strip().casefold()

        selected_doctors = [
            doctor for doctor in DOCTORS
            if (
                not doctor_id
                or doctor["id"] == doctor_id
            )
            and (
                not requested_department
                or doctor["department"].casefold()
                == requested_department
            )
        ]

        slots: list[dict[str, Any]] = []

        for doctor in selected_doctors:
            doctor_slots = generate_synthetic_slots(
                doctor["id"],
                start,
                days,
            )

            for slot in doctor_slots:
                slot["doctorName"] = doctor["name"]
                slot["location"] = doctor["location"]
                slot["dataNotice"] = DATA_NOTICE

                # Report capacity from the same state used by demo bookings.
                capacity = demo_scheduler.get_slot_status(
                    doctor["id"],
                    slot["date"],
                    slot["time"],
                )
                slot.update({
                    "slotCapacity": capacity["slotCapacity"],
                    "slotBookedCount": capacity["slotBookedCount"],
                    "slotRemainingCapacity": capacity["slotRemainingCapacity"],
                    "dailyCapacity": capacity["dailyCapacity"],
                    "dailyBookedCount": capacity["dailyBookedCount"],
                    "dailyRemainingCapacity": capacity["dailyRemainingCapacity"],
                    "available": capacity["available"],
                })

            slots.extend(doctor_slots)

        slots.sort(
            key=lambda slot: (slot["date"], slot["time"])
        )

        return {
            "slots": slots,
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
            "notice": (
                "These are generated demonstration slots, not real "
                "hospital availability. No slot has been reserved."
            ),
        }

    def book_demo_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
        purpose: str = "",
    ) -> dict[str, Any]:
        """Create a fictional booking after trusted code checks confirmation."""
        self._require_patient(patient_id)
        booking = demo_scheduler.book_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            purpose=purpose,
        )
        return booking

    def get_patient_demo_bookings(
        self,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        """Return only the authenticated patient's demo bookings."""
        self._require_patient(patient_id)
        return demo_scheduler.get_patient_bookings(patient_id)

    def get_doctor_day_summary(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_date: str,
    ) -> dict[str, Any]:
        """Return aggregate booking capacity and a clearly fictional queue."""
        self._require_patient(patient_id)
        return demo_scheduler.get_day_summary(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
        )

    def get_queue_estimate(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_date: str = "",
    ) -> dict[str, Any]:
        """Return an illustrative queue estimate, never a live claim."""
        self._require_patient(patient_id)

        doctor = next(
            (
                item for item in DOCTORS
                if item["id"] == doctor_id
            ),
            None,
        )

        if doctor is None:
            raise ValueError("Doctor not found.")

        selected_date = date.today()

        if appointment_date:
            try:
                selected_date = date.fromisoformat(appointment_date)
            except ValueError as error:
                raise ValueError(
                    "appointment_date must use YYYY-MM-DD format."
                ) from error

        if selected_date < date.today():
            raise ValueError(
                "appointment_date cannot be in the past."
            )

        demo_people_ahead = (
            3 if selected_date.weekday() < 5 else 0
        )

        return {
            "doctorId": doctor["id"],
            "doctorName": doctor["name"],
            "date": selected_date.isoformat(),
            "peopleAhead": demo_people_ahead,
            "estimatedWaitMinutes": demo_people_ahead * 15,
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
            "notice": (
                "Illustrative synthetic estimate only. This is not a "
                "live queue position or a reliable prediction of wait time."
            ),
        }


hospital_service = HospitalService()
