"""Staff-only aggregate analytics for the synthetic hospital demo."""

from collections import defaultdict

from fastapi import APIRouter, Depends

from app.core.auth import get_current_demo_staff
from app.data.scheduling import DATA_SOURCE, DOCTORS
from app.services.appointment_requests import get_appointment_request_service
from app.services.demo_scheduler import DEMO_NOTICE, demo_scheduler


router = APIRouter(
    prefix="/api/staff/analytics",
    tags=["Staff Analytics"],
    dependencies=[Depends(get_current_demo_staff)],
)

BOOKED_STATUSES = (
    "confirmed_demo",
    "attended_demo",
    "missed_demo",
)

ATTENDANCE_STATUSES = (
    "attended_demo",
    "missed_demo",
)

PENDING_REQUEST_STATUSES = (
    "submitted",
    "under_review",
    "needs_information",
    "appointment_offered",
)


@router.get("")
def get_staff_analytics() -> dict:
    """Return aggregate demo metrics without exposing patient-level records."""

    scheduler = demo_scheduler
    request_service = get_appointment_request_service(scheduler)

    doctor_directory = {
        doctor["id"]: doctor
        for doctor in DOCTORS
    }

    with scheduler._lock:
        connection = scheduler._connection

        request_rows = connection.execute(
            """
            SELECT status, COUNT(*) AS total
            FROM demo_appointment_requests
            GROUP BY status
            """
        ).fetchall()

        booking_rows = connection.execute(
            """
            SELECT doctor_id, status, COUNT(*) AS total
            FROM demo_bookings
            GROUP BY doctor_id, status
            """
        ).fetchall()

        trend_rows = connection.execute(
            """
            SELECT substr(created_at, 1, 7) AS month,
                   COUNT(*) AS total
            FROM demo_bookings
            WHERE status IN (?, ?, ?)
            GROUP BY substr(created_at, 1, 7)
            ORDER BY month
            """,
            BOOKED_STATUSES,
        ).fetchall()

    # Keep the service reference alive; its initialization ensures that
    # the request table exists on this scheduler's shared SQLite connection.
    del request_service

    request_counts = {
        status: 0
        for status in (
            "submitted",
            "under_review",
            "needs_information",
            "appointment_offered",
            "appointment_confirmed",
            "declined",
            "cancelled",
        )
    }

    for row in request_rows:
        if row["status"] in request_counts:
            request_counts[row["status"]] = row["total"]

    pending_requests = sum(
        request_counts[status]
        for status in PENDING_REQUEST_STATUSES
    )

    booked_by_doctor = defaultdict(int)
    booked_by_department = defaultdict(int)

    total_booked = 0
    active_bookings = 0
    attended = 0
    missed = 0

    for row in booking_rows:
        status = row["status"]
        count = row["total"]

        if status == "confirmed_demo":
            active_bookings += count

        if status == "attended_demo":
            attended += count

        if status == "missed_demo":
            missed += count

        if status not in BOOKED_STATUSES:
            continue

        doctor = doctor_directory.get(row["doctor_id"])

        # Do not expose unknown IDs or invent doctor profile information.
        if doctor is None:
            continue

        total_booked += count
        booked_by_doctor[doctor["id"]] += count
        booked_by_department[doctor["department"]] += count

    doctor_rankings = []

    for doctor_id, count in booked_by_doctor.items():
        doctor = doctor_directory[doctor_id]

        doctor_rankings.append(
            {
                "doctorId": doctor_id,
                "doctorName": doctor["name"],
                "department": doctor["department"],
                "totalBooked": count,
            }
        )

    doctor_rankings.sort(
        key=lambda item: (-item["totalBooked"], item["doctorName"])
    )

    department_rankings = [
        {
            "department": department,
            "totalBooked": count,
        }
        for department, count in booked_by_department.items()
    ]

    department_rankings.sort(
        key=lambda item: (-item["totalBooked"], item["department"])
    )

    return {
        "dataSource": DATA_SOURCE,
        "dataNotice": (
            f"{DEMO_NOTICE} These analytics describe only local "
            "synthetic demonstration records."
        ),
        "appointmentRequests": {
            "total": sum(request_counts.values()),
            "pending": pending_requests,
            "confirmed": request_counts["appointment_confirmed"],
            "declined": request_counts["declined"],
            "cancelled": request_counts["cancelled"],
            "byStatus": request_counts,
        },
        "appointments": {
            "totalBooked": total_booked,
            "active": active_bookings,
            "attended": attended,
            "missed": missed,
            "doctorRankings": doctor_rankings,
            "departmentRankings": department_rankings,
            "monthlyTrend": [
                {
                    "month": row["month"],
                    "totalBooked": row["total"],
                }
                for row in trend_rows
            ],
        },
    }
