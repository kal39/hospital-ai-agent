import { useCallback, useEffect, useMemo, useState } from "react";
import {
  approveStaffAppointmentRequest,
  declineStaffAppointmentRequest,
  getStaffAvailability,
  listStaffAppointmentRequests,
  listStaffAppointments,
  listStaffDoctors,
  recordStaffAttendance,
  getStaffAnalytics,
  type StaffAnalytics,
  type StaffAppointmentRequest,
  type StaffAttendanceAppointment,
} from "../../services/staffAppointmentRequests";
import type { AppointmentSlot, Doctor } from "../../services/appointments";
import { getLocalDateString } from "../../services/appointments";
import type { Language } from "../../types/chat";
import DoctorAvatar from "../Doctor/DoctorAvatar";

type Props = {
  language: Language;
};

const copy = {
  en: {
    eyebrow: "STAFF WORKSPACE",
    title: "Appointment management",
    intro: "Review appointment requests, manage attendance, and monitor appointment trends.",
    overview: "Dashboard overview",
    totalRequests: "Total requests",
    pendingRequests: "Awaiting decision",
    bookedAppointments: "Appointments booked",
    attendanceRecorded: "Attendance recorded",
    analytics: "Appointment analytics",
    doctorBookings: "Most booked doctors",
    departmentBookings: "Bookings by department",
    monthlyBookings: "Monthly booking trend",
    noBookingData: "No booking data is available yet.",
    noRanking: "No booking records to rank yet.",
    aiActivityUnavailable: "AI assistant activity analytics are not available yet.",
    analyticsNote: "These metrics describe recorded demo appointment data. They do not measure AI recommendations or assistant conversations.",
    demo: "Demo staff workspace â€” synthetic data only",
    demoText:
      "All requests and appointments shown here are fictional demonstration records. This workspace is not connected to a live hospital system. Do not enter real patient information.",
    requests: "Appointment requests",
    attendance: "Attendance",
    openRequests: "requests awaiting a decision",
    refresh: "Refresh",
    refreshing: "Refreshingâ€¦",
    open: "Open requests",
    all: "All requests",
    queue: "REQUEST QUEUE",
    incoming: "Incoming requests",
    loading: "Loadingâ€¦",
    noOpen: "No open requests",
    noRequests: "No requests found",
    select: "Select a request",
    selectText: "Choose a request from the list to review its details.",
    details: "REQUEST DETAILS",
    patient: "Patient reference",
    preferredDoctor: "Preferred doctor",
    noPreference: "No preference",
    preferredDates: "Preferred dates",
    submitted: "Submitted",
    reason: "Reason for visit",
    booking: "Demo booking reference",
    assigned: "Assigned doctor",
    date: "Appointment date",
    time: "Appointment time",
    declineExplanation: "Decline explanation",
    history: "Status history",
    approveTitle: "Approve and assign appointment",
    doctor: "Doctor",
    chooseDoctor: "Select a doctor",
    appointmentDate: "Available appointment slot",
    appointmentTime: "Appointment time",
    approve: "Approve and book demo appointment",
    decline: "Decline request",
    explanation: "Explanation (required)",
    declinePlaceholder: "Explain why this request cannot be accepted.",
    declineButton: "Decline demo request",
    processing: "Processingâ€¦",
    decided: "This request has already been decided and cannot be acted on again.",
    notSpecified: "Not specified",
    submittedStatus: "Submitted",
    underReview: "Under review",
    needsInfo: "Needs information",
    offered: "Appointment offered",
    confirmed: "Appointment confirmed",
    declined: "Declined",
    cancelled: "Cancelled",
    attendanceTitle: "Appointment attendance",
    attendanceText:
      "Review confirmed appointments and record whether each patient attended.",
    total: "appointments",
    search: "Search patient, doctor, department or booking reference",
    filterAll: "All appointments",
    filterPending: "Awaiting attendance",
    filterAttended: "Attended",
    filterMissed: "Missed",
    patientColumn: "Patient",
    departmentColumn: "Department",
    doctorColumn: "Doctor",
    schedule: "Scheduled",
    statusColumn: "Attendance",
    actions: "Actions",
    upcoming: "Upcoming",
    pending: "Pending",
    attended: "Attended",
    missed: "Missed",
    markAttended: "Mark attended",
    markMissed: "Mark missed",
    noAppointments: "No appointments found",
    noAppointmentsText: "Confirmed demo appointments will appear here.",
    futureNotice:
      "Attendance can only be recorded after the scheduled appointment time.",
    confirmAttended: "Confirm that this patient attended the appointment?",
    confirmMissed: "Confirm that this patient missed the appointment?",
    attendanceSaved: "Attendance record saved successfully.",
    patientReference: "Patient reference",
    bookingReference: "Booking reference",
    error: "Something went wrong. Please try again.",
    connection:
      "Could not connect to the demo backend. Check that the backend is running.",
    auth:
      "Staff demo authentication failed. Check the staff token and restart the frontend.",
    dismiss: "Dismiss message",
    minimum: "Minimum 10 characters",
    noDoctors: "No doctors are available for this department.",
    noSlots: "No available appointment slots were found in the requested date range.",
    chooseSlot: "Choose an available date and time",
    requestApproved: "Request approved and demo appointment created.",
    requestDeclined: "Appointment request declined.",
    noReason: "Please provide a decline explanation.",
    preferredRange: "Preferred date range",
    status: "Status",
    viewRequest: "Review request",
    noDoctorPreference: "No preferred doctor was specified.",
    noDatePreference: "No preferred dates were specified.",
    loadingDoctors: "Loading doctorsâ€¦",
    loadingSlots: "Loading available slotsâ€¦",
    slotUnavailable: "This slot is no longer available. Refresh the slots and try again.",
    requestUnavailable: "This request is no longer available for review.",
  },
  am: {
    eyebrow: "á‹¨áˆ°áˆ«á‰°áŠžá‰½ á‹¨áˆµáˆ« á‰¦á‰³",
    title: "á‹¨á‰€áŒ áˆ® áŠ áˆµá‰°á‹³á‹°áˆ­",
    intro: "á‹¨á‰€áŒ áˆ® áŒ¥á‹«á‰„á‹Žá‰½áŠ• á‹­áˆ˜áˆáŠ¨á‰± áŠ¥áŠ“ á‹¨á‰³áŠ«áˆšá‹Žá‰½áŠ• áˆ˜áŒˆáŠ˜á‰µ á‹«áˆµá‰°á‹³á‹µáˆ©á¢",
    demo: "á‹¨áˆ™áŠ¨áˆ« á‹¨áˆ°áˆ«á‰°áŠžá‰½ á‰¦á‰³ â€” áˆ°á‹ áˆ°áˆ«áˆ½ áˆ˜áˆ¨áŒƒ á‰¥á‰»",
    demoText:
      "áŠ¥á‹šáˆ… á‹¨áˆšá‰³á‹©á‰µ áŒ¥á‹«á‰„á‹Žá‰½áŠ“ á‰€áŒ áˆ®á‹Žá‰½ áˆáˆ‰ áˆˆáˆ™áŠ¨áˆ« á‹¨á‰°áˆáŒ áˆ© áŠ“á‰¸á‹á¢ á‹­áˆ… áˆµáˆ­á‹“á‰µ áŠ¨áŠ¥á‹áŠá‰°áŠ› á‹¨áˆ†áˆµá’á‰³áˆ áˆµáˆ­á‹“á‰µ áŒ‹áˆ­ áŠ áˆá‰°áŒˆáŠ“áŠ˜áˆá¢ áŠ¥á‹áŠá‰°áŠ› á‹¨á‰³áŠ«áˆš áˆ˜áˆ¨áŒƒ áŠ á‹«áˆµáŒˆá‰¡á¢",
    requests: "á‹¨á‰€áŒ áˆ® áŒ¥á‹«á‰„á‹Žá‰½",
    attendance: "á‹¨á‰³áŠ«áˆš áˆ˜áŒˆáŠ˜á‰µ",
    openRequests: "á‹áˆ³áŠ” á‹¨áˆšáŒ á‰¥á‰ áŒ¥á‹«á‰„á‹Žá‰½",
    refresh: "áŠ á‹µáˆµ",
    refreshing: "á‰ áˆ›á‹°áˆµ áˆ‹á‹­â€¦",
    open: "áŠ­áá‰µ áŒ¥á‹«á‰„á‹Žá‰½",
    all: "áˆáˆ‰áˆ áŒ¥á‹«á‰„á‹Žá‰½",
    queue: "á‹¨áŒ¥á‹«á‰„ á‹áˆ­á‹áˆ­",
    incoming: "á‹¨áŒˆá‰¡ áŒ¥á‹«á‰„á‹Žá‰½",
    loading: "á‰ áˆ˜áŒ«áŠ• áˆ‹á‹­â€¦",
    noOpen: "áŠ­áá‰µ áŒ¥á‹«á‰„ á‹¨áˆˆáˆ",
    noRequests: "áˆáŠ•áˆ áŒ¥á‹«á‰„ áŠ áˆá‰°áŒˆáŠ˜áˆ",
    select: "áŒ¥á‹«á‰„ á‹­áˆáˆ¨áŒ¡",
    selectText: "á‹áˆ­á‹áˆ©áŠ• á‰ áˆ˜áŒ á‰€áˆ á‹¨áˆšáˆáˆáŒ‰á‰µáŠ• áŒ¥á‹«á‰„ á‹­áˆáˆ¨áŒ¡á¢",
    details: "á‹¨áŒ¥á‹«á‰„ á‹áˆ­á‹áˆ­",
    patient: "á‹¨á‰³áŠ«áˆš áˆ˜áˆˆá‹«",
    preferredDoctor: "á‹¨á‰°áˆ˜áˆ¨áŒ  áˆáŠªáˆ",
    noPreference: "áˆáˆ­áŒ« á‹¨áˆˆáˆ",
    preferredDates: "á‹¨á‰°áˆ˜áˆ¨áŒ¡ á‰€áŠ“á‰µ",
    submitted: "á‹¨á‰€áˆ¨á‰ á‰ á‰µ áŒŠá‹œ",
    reason: "á‹¨áŒ‰á‰¥áŠá‰µ áˆáŠ­áŠ•á‹«á‰µ",
    booking: "á‹¨áˆ™áŠ¨áˆ« á‰€áŒ áˆ® áˆ˜áˆˆá‹«",
    assigned: "á‹¨á‰°áˆ˜á‹°á‰  áˆáŠªáˆ",
    date: "á‹¨á‰€áŒ áˆ® á‰€áŠ•",
    time: "á‹¨á‰€áŒ áˆ® áˆ°á‹“á‰µ",
    declineExplanation: "á‹¨áˆ˜áŠ¨áˆáŠ¨á‹« áˆáŠ­áŠ•á‹«á‰µ",
    history: "á‹¨áˆáŠ”á‰³ á‰³áˆªáŠ­",
    approveTitle: "áŒ¥á‹«á‰„á‹áŠ• á‹«áŒ½á‹µá‰ áŠ¥áŠ“ á‰€áŒ áˆ® á‹­áˆ˜á‹µá‰¡",
    doctor: "áˆáŠªáˆ",
    chooseDoctor: "áˆáŠªáˆ á‹­áˆáˆ¨áŒ¡",
    appointmentDate: "á‹¨á‰€áŒ áˆ® áŒŠá‹œ",
    appointmentTime: "á‹¨á‰€áŒ áˆ® áˆ°á‹“á‰µ",
    approve: "áŠ áŒ½á‹µá‰… áŠ¥áŠ“ á‹¨áˆ™áŠ¨áˆ« á‰€áŒ áˆ® áˆ˜á‹áŒá‰¥",
    decline: "áŒ¥á‹«á‰„á‹áŠ• áŠ¨áˆáŠ­áˆ",
    explanation: "áˆáŠ­áŠ•á‹«á‰µ (áŠ áˆµáˆáˆ‹áŒŠ)",
    declinePlaceholder: "áŒ¥á‹«á‰„á‹ áˆˆáˆáŠ• áˆ˜á‰€á‰ áˆ áŠ¥áŠ•á‹°áˆ›á‹­á‰»áˆ á‹«á‰¥áˆ«áˆ©á¢",
    declineButton: "á‹¨áˆ™áŠ¨áˆ« áŒ¥á‹«á‰„áŠ• áŠ¨áˆáŠ­áˆ",
    processing: "á‰ áˆ‚á‹°á‰µ áˆ‹á‹­â€¦",
    decided: "á‹­áˆ… áŒ¥á‹«á‰„ áŠ áˆµá‰€á‹µáˆž á‹áˆ³áŠ” á‰°áˆ°áŒ¥á‰¶á‰³áˆá¢",
    notSpecified: "áŠ áˆá‰°áŒˆáˆˆáŒ¸áˆ",
    submittedStatus: "á‰€áˆ­á‰§áˆ",
    underReview: "á‰ áŒáˆáŒˆáˆ› áˆ‹á‹­",
    needsInfo: "á‰°áŒ¨áˆ›áˆª áˆ˜áˆ¨áŒƒ á‹«áˆµáˆáˆáŒ‹áˆ",
    offered: "á‰€áŒ áˆ® á‰€áˆ­á‰§áˆ",
    confirmed: "á‰€áŒ áˆ® á‰°áˆ¨áŒ‹áŒáŒ§áˆ",
    declined: "á‰°áŠ¨áˆáŠ­áˆáˆ",
    cancelled: "á‰°áˆ°áˆ­á‹Ÿáˆ",
    attendanceTitle: "á‹¨á‰€áŒ áˆ® áˆ˜áŒˆáŠ˜á‰µ áˆ˜á‹áŒˆá‰¥",
    attendanceText: "á‹¨á‰°áˆ¨áŒ‹áŒˆáŒ¡ á‰€áŒ áˆ®á‹Žá‰½áŠ• á‹­áˆ˜áˆáŠ¨á‰± áŠ¥áŠ“ á‰³áŠ«áˆšá‹ áˆ˜áŒ¥á‰¶ áŠ¥áŠ•á‹°áŠá‰ áˆ­ á‹­áˆ˜á‹áŒá‰¡á¢",
    total: "á‰€áŒ áˆ®á‹Žá‰½",
    search: "á‰³áŠ«áˆšá£ áˆáŠªáˆá£ áŠ­ááˆ á‹ˆá‹­áˆ á‹¨á‰€áŒ áˆ® áˆ˜áˆˆá‹« á‹­áˆáˆáŒ‰",
    filterAll: "áˆáˆ‰áˆ á‰€áŒ áˆ®á‹Žá‰½",
    filterPending: "áˆ˜áŒˆáŠ˜á‰µ á‹¨áˆšáŒ á‰¥á‰",
    filterAttended: "á‰°áŒˆáŠá‰·áˆ",
    filterMissed: "áŠ áˆá‰°áŒˆáŠ˜áˆ",
    patientColumn: "á‰³áŠ«áˆš",
    departmentColumn: "áŠ­ááˆ",
    doctorColumn: "áˆáŠªáˆ",
    schedule: "á‹¨á‰€áŒ áˆ® áŒŠá‹œ",
    statusColumn: "á‹¨áˆ˜áŒˆáŠ˜á‰µ áˆáŠ”á‰³",
    actions: "á‰°áŒá‰£áˆ®á‰½",
    upcoming: "á‹ˆá‹°áŠá‰µ á‹«áˆˆ",
    pending: "á‰ áˆ˜áŒ á‰£á‰ á‰… áˆ‹á‹­",
    attended: "á‰°áŒˆáŠá‰·áˆ",
    missed: "áŠ áˆá‰°áŒˆáŠ˜áˆ",
    markAttended: "á‰°áŒˆáŠá‰·áˆ á‰¥áˆˆáˆ… áˆ˜á‹áŒá‰¥",
    markMissed: "áŠ áˆá‰°áŒˆáŠ˜áˆ á‰¥áˆˆáˆ… áˆ˜á‹áŒá‰¥",
    noAppointments: "á‰€áŒ áˆ® áŠ áˆá‰°áŒˆáŠ˜áˆ",
    noAppointmentsText: "á‹¨á‰°áˆ¨áŒ‹áŒˆáŒ¡ á‹¨áˆ™áŠ¨áˆ« á‰€áŒ áˆ®á‹Žá‰½ áŠ¥á‹šáˆ… á‹­á‰³á‹«áˆ‰á¢",
    futureNotice: "á‹¨áˆ˜áŒˆáŠ˜á‰µ áˆáŠ”á‰³ áˆ˜áˆ˜á‹áŒˆá‰¥ á‹¨áˆšá‰»áˆˆá‹ áŠ¨á‰€áŒ áˆ®á‹ áŒŠá‹œ á‰ áŠ‹áˆ‹ á‰¥á‰» áŠá‹á¢",
    confirmAttended: "á‹­áˆ… á‰³áŠ«áˆš á‰ á‰€áŒ áˆ®á‹ áˆ‹á‹­ áŠ¥áŠ•á‹°á‰°áŒˆáŠ˜ á‹«áˆ¨áŒ‹áŒáŒ¡?",
    confirmMissed: "á‹­áˆ… á‰³áŠ«áˆš á‰ á‰€áŒ áˆ®á‹ áˆ‹á‹­ áŠ¥áŠ•á‹³áˆá‰°áŒˆáŠ˜ á‹«áˆ¨áŒ‹áŒáŒ¡?",
    attendanceSaved: "á‹¨áˆ˜áŒˆáŠ˜á‰µ áˆ˜áˆ¨áŒƒá‹ á‰ á‰°áˆ³áŠ« áˆáŠ”á‰³ á‰°áˆ˜á‹áŒá‰§áˆá¢",
    patientReference: "á‹¨á‰³áŠ«áˆš áˆ˜áˆˆá‹«",
    bookingReference: "á‹¨á‰€áŒ áˆ® áˆ˜áˆˆá‹«",
    error: "á‰½áŒáˆ­ á‰°áˆáŒ¥áˆ¯áˆá¢ áŠ¥áŠ•á‹°áŒˆáŠ“ á‹­áˆžáŠ­áˆ©á¢",
    connection: "áŠ¨áˆ™áŠ¨áˆ« á‰£áŠ­áŠ¤áŠ•á‹µ áŒ‹áˆ­ áˆ˜áŒˆáŠ“áŠ˜á‰µ áŠ áˆá‰°á‰»áˆˆáˆá¢",
    auth: "á‹¨áˆ°áˆ«á‰°áŠ› áˆ™áŠ¨áˆ« áˆ›áˆ¨áŒ‹áŒˆáŒ« áŠ áˆá‰°áˆ³áŠ«áˆá¢",
    dismiss: "áˆ˜áˆá‹•áŠ­á‰±áŠ• á‹áŒ‹",
    minimum: "á‰¢á‹«áŠ•áˆµ 10 á‰áˆáŠá‹Žá‰½",
    noDoctors: "áˆˆá‹šáˆ… áŠ­ááˆ áˆáŠªáˆ áŠ áˆá‰°áŒˆáŠ˜áˆá¢",
    noSlots: "á‰ á‰°áˆ˜áˆ¨áŒ á‹ á‹¨á‰€áŠ• áŠ­áˆáˆ á‹áˆµáŒ¥ áŠ­áá‰µ á‰€áŒ áˆ® áŠ áˆá‰°áŒˆáŠ˜áˆá¢",
    chooseSlot: "áŠ­áá‰µ á‰€áŠ•áŠ“ áˆ°á‹“á‰µ á‹­áˆáˆ¨áŒ¡",
    requestApproved: "áŒ¥á‹«á‰„á‹ áŒ¸á‹µá‰‹áˆ áŠ¥áŠ“ á‹¨áˆ™áŠ¨áˆ« á‰€áŒ áˆ® á‰°áˆ˜á‹áŒá‰§áˆá¢",
    requestDeclined: "á‹¨á‰€áŒ áˆ® áŒ¥á‹«á‰„á‹ á‰°áŠ¨áˆáŠ­áˆáˆá¢",
    noReason: "áŠ¥á‰£áŠ­á‹Ž á‹¨áˆ˜áŠ¨áˆáŠ¨á‹« áˆáŠ­áŠ•á‹«á‰µ á‹«áˆµáŒˆá‰¡á¢",
    preferredRange: "á‹¨á‰°áˆ˜áˆ¨áŒ  á‹¨á‰€áŠ• áŠ­áˆáˆ",
    status: "áˆáŠ”á‰³",
    viewRequest: "áŒ¥á‹«á‰„á‹áŠ• á‹­áˆ˜áˆáŠ¨á‰±",
    noDoctorPreference: "á‹¨á‰°áˆ˜áˆ¨áŒ  áˆáŠªáˆ áŠ áˆá‰°áŒˆáˆˆáŒ¸áˆá¢",
    noDatePreference: "á‹¨á‰°áˆ˜áˆ¨áŒ¡ á‰€áŠ“á‰µ áŠ áˆá‰°áŒˆáˆˆáŒ¹áˆá¢",
    loadingDoctors: "áˆáŠªáˆžá‰½áŠ• á‰ áˆ˜áŒ«áŠ• áˆ‹á‹­â€¦",
    loadingSlots: "áŠ­áá‰µ á‰€áŒ áˆ®á‹Žá‰½áŠ• á‰ áˆ˜áˆáˆˆáŒ áˆ‹á‹­â€¦",
    slotUnavailable: "á‹­áˆ… á‰€áŒ áˆ® áŠ¨áŠ áˆáŠ• á‰ áŠ‹áˆ‹ áŠ­áá‰µ áŠ á‹­á‹°áˆˆáˆá¢ áŠ¥áŠ•á‹°áŒˆáŠ“ á‹­áˆáˆáŒ‰á¢",
    requestUnavailable: "á‹­áˆ… áŒ¥á‹«á‰„ áŠ¨áŠ áˆáŠ• á‰ áŠ‹áˆ‹ áˆˆáŒáˆáŒˆáˆ› áŠ á‹­áŒˆáŠáˆá¢",
    overview: "Dashboard overview",
    totalRequests: "Total requests",
    pendingRequests: "Awaiting decision",
    bookedAppointments: "Appointments booked",
    attendanceRecorded: "Attendance recorded",
    analytics: "Appointment analytics",
    doctorBookings: "Most booked doctors",
    departmentBookings: "Bookings by department",
    monthlyBookings: "Monthly booking trend",
    noBookingData: "No booking data is available yet.",
    noRanking: "No booking records to rank yet.",
    aiActivityUnavailable: "AI assistant activity analytics are not available yet.",
    analyticsNote: "These metrics describe recorded demo appointment data. They do not measure AI recommendations or assistant conversations.",

  },
} as const;

type StaffReviewCopy = { [Key in keyof typeof copy.en]: string };

function errorMessage(error: unknown, t: StaffReviewCopy): string {
  if (!(error instanceof Error)) return t.error;
  if (error.message.includes("Could not connect")) return t.connection;
  if (error.message.includes("authentication failed")) return t.auth;
  return error.message;
}

function formatDate(value?: string | null, language: Language = "en"): string {
  if (!value) return language === "am" ? "áŠ áˆá‰°áŒˆáˆˆáŒ¸áˆ" : "Not specified";

  const date = new Date(`${value}T00:00:00`);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(language === "am" ? "am-ET" : "en-ET", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
}

function formatTimestamp(value: string, language: Language): string {
  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString(language === "am" ? "am-ET" : "en-ET", {
        dateStyle: "medium",
        timeStyle: "short",
      });
}

function statusLabel(status: string, t: StaffReviewCopy): string {
  switch (status) {
    case "submitted":
      return t.submittedStatus;
    case "under_review":
      return t.underReview;
    case "needs_information":
      return t.needsInfo;
    case "appointment_offered":
      return t.offered;
    case "appointment_confirmed":
      return t.confirmed;
    case "declined":
      return t.declined;
    case "cancelled":
      return t.cancelled;
    default:
      return status.replaceAll("_", " ");
  }
}

function isOpenRequest(request: StaffAppointmentRequest): boolean {
  return !["appointment_confirmed", "declined", "cancelled"].includes(
    request.status,
  );
}

function attendanceStatus(
  appointment: StaffAttendanceAppointment,
  t: StaffReviewCopy,
) {
  if (appointment.status === "attended_demo") {
    return { label: t.attended, kind: "attended" };
  }

  if (appointment.status === "missed_demo") {
    return { label: t.missed, kind: "missed" };
  }

  if (appointment.status !== "confirmed_demo") {
    return { label: t.upcoming, kind: "upcoming" };
  }

  return { label: t.pending, kind: "pending" };
}

function appointmentHasPassed(
  appointment: StaffAttendanceAppointment,
): boolean {
  const scheduled = new Date(`${appointment.date}T${appointment.time}:00`);

  return !Number.isNaN(scheduled.getTime()) && scheduled.getTime() <= Date.now();
}

function isAttendanceEligible(
  appointment: StaffAttendanceAppointment,
): boolean {
  return (
    appointment.status === "confirmed_demo" &&
    appointmentHasPassed(appointment)
  );
}

function getRequestStartDate(request: StaffAppointmentRequest): string {
  const today = getLocalDateString();
  const preferredStart = request.preferredDateStart;

  if (!preferredStart || preferredStart < today) return today;
  return preferredStart;
}

function slotKey(slot: AppointmentSlot): string {
  return `${slot.date}|${slot.time}`;
}

export default function StaffReview({ language }: Props) {
  const t = copy[language];

  const [requests, setRequests] = useState<StaffAppointmentRequest[]>([]);
  const [requestFilter, setRequestFilter] = useState<"open" | "all">("open");
  const [selectedRequestId, setSelectedRequestId] = useState("");
  const [requestsLoading, setRequestsLoading] = useState(true);

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState("");
  const [doctorsLoading, setDoctorsLoading] = useState(false);

  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selectedSlotKey, setSelectedSlotKey] = useState("");
  const [slotsLoading, setSlotsLoading] = useState(false);

  const [declineReason, setDeclineReason] = useState("");

  const [appointments, setAppointments] = useState<
    StaffAttendanceAppointment[]
  >([]);
  const [attendanceFilter, setAttendanceFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [attendanceLoading, setAttendanceLoading] = useState(true);

  const [analytics, setAnalytics] = useState<StaffAnalytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedRequest = useMemo(
    () => requests.find((item) => item.requestId === selectedRequestId) ?? null,
    [requests, selectedRequestId],
  );

  const visibleRequests = useMemo(() => {
    const filtered =
      requestFilter === "open" ? requests.filter(isOpenRequest) : requests;

    return [...filtered].sort((a, b) =>
      b.submittedAt.localeCompare(a.submittedAt),
    );
  }, [requests, requestFilter]);

  const availableSlots = useMemo(() => {
    if (!selectedRequest) return [];

    return slots.filter((slot) => {
      if (!slot.available) return false;

      if (
        selectedRequest.preferredDateEnd &&
        slot.date > selectedRequest.preferredDateEnd
      ) {
        return false;
      }

      return true;
    });
  }, [slots, selectedRequest]);

  const selectedSlot = useMemo(
    () => availableSlots.find((slot) => slotKey(slot) === selectedSlotKey) ?? null,
    [availableSlots, selectedSlotKey],
  );

  const loadRequests = useCallback(async () => {
    setRequestsLoading(true);
    setError("");

    try {
      const result = await listStaffAppointmentRequests();
      setRequests(result);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setRequestsLoading(false);
    }
  }, [t]);

  const loadAppointments = useCallback(async () => {
    setAttendanceLoading(true);
    setError("");

    try {
      const result = await listStaffAppointments();
      setAppointments(result);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setAttendanceLoading(false);
    }
  }, [t]);

  const loadAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);

    try {
      const result = await getStaffAnalytics();
      setAnalytics(result);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setAnalyticsLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRequests();
      void loadAppointments();
      void loadAnalytics();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadRequests, loadAppointments, loadAnalytics]);

  useEffect(() => {
    if (visibleRequests.length === 0) {
      if (selectedRequestId) setSelectedRequestId("");
      return;
    }

    const selectedStillVisible = visibleRequests.some(
      (item) => item.requestId === selectedRequestId,
    );

    if (!selectedStillVisible) {
      setSelectedRequestId(visibleRequests[0].requestId);
    }
  }, [visibleRequests, selectedRequestId]);

  useEffect(() => {
    let active = true;

    async function loadDoctors() {
      if (!selectedRequest || !isOpenRequest(selectedRequest)) {
        setDoctors([]);
        setSelectedDoctorId("");
        setSlots([]);
        setSelectedSlotKey("");
        return;
      }

      setDoctorsLoading(true);
      setDoctors([]);
      setSelectedDoctorId("");
      setSlots([]);
      setSelectedSlotKey("");

      try {
        const result = await listStaffDoctors(
          selectedRequest.department || undefined,
        );

        if (!active) return;

        setDoctors(result);

        const preferred = selectedRequest.preferredDoctor?.trim().toLowerCase();
        const preferredDoctor = preferred
          ? result.find(
              (doctor) =>
                doctor.name.trim().toLowerCase() === preferred ||
                doctor.id.trim().toLowerCase() === preferred,
            )
          : undefined;

        setSelectedDoctorId(preferredDoctor?.id ?? result[0]?.id ?? "");
      } catch (err) {
        if (active) setError(errorMessage(err, t));
      } finally {
        if (active) setDoctorsLoading(false);
      }
    }

    void loadDoctors();

    return () => {
      active = false;
    };
  }, [selectedRequest, t]);

  useEffect(() => {
    let active = true;

    async function loadSlots() {
      if (!selectedRequest || !selectedDoctorId) {
        setSlots([]);
        setSelectedSlotKey("");
        return;
      }

      setSlotsLoading(true);
      setSlots([]);
      setSelectedSlotKey("");

      try {
        const result = await getStaffAvailability(
          selectedDoctorId,
          getRequestStartDate(selectedRequest),
          30,
        );

        if (!active) return;

        const filtered = result.filter((slot) => {
          if (!slot.available) return false;

          if (
            selectedRequest.preferredDateEnd &&
            slot.date > selectedRequest.preferredDateEnd
          ) {
            return false;
          }

          return true;
        });

        setSlots(filtered);
        setSelectedSlotKey(filtered[0] ? slotKey(filtered[0]) : "");
      } catch (err) {
        if (active) setError(errorMessage(err, t));
      } finally {
        if (active) setSlotsLoading(false);
      }
    }

    void loadSlots();

    return () => {
      active = false;
    };
  }, [selectedRequest, selectedDoctorId, t]);

  const visibleAppointments = useMemo(() => {
    const query = search.trim().toLowerCase();

    return appointments
      .filter((item) =>
        ["confirmed_demo", "attended_demo", "missed_demo"].includes(
          item.status,
        ),
      )
      .filter((item) => {
        if (attendanceFilter === "pending") {
          return item.status === "confirmed_demo";
        }

        if (attendanceFilter === "attended") {
          return item.status === "attended_demo";
        }

        if (attendanceFilter === "missed") {
          return item.status === "missed_demo";
        }

        return true;
      })
      .filter(
        (item) =>
          !query ||
          [
            item.patientId,
            item.doctorName,
            item.department,
            item.bookingId,
          ].some((value) => value?.toLowerCase().includes(query)),
      )
      .sort((a, b) =>
        `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`),
      );
  }, [appointments, attendanceFilter, search]);

  async function handleApprove() {
    if (!selectedRequest || !selectedSlot || !selectedDoctorId) return;
    if (!isOpenRequest(selectedRequest)) {
      setError(t.requestUnavailable);
      return;
    }

    setWorking(true);
    setError("");
    setSuccess("");

    try {
      await approveStaffAppointmentRequest(selectedRequest.requestId, {
        doctorId: selectedDoctorId,
        date: selectedSlot.date,
        time: selectedSlot.time,
      });

      setSuccess(t.requestApproved);
      setDeclineReason("");

      await Promise.all([loadRequests(), loadAppointments(), loadAnalytics()]);
    } catch (err) {
      setError(errorMessage(err, t));
      if (err instanceof Error && err.message.includes("available")) {
        setError(t.slotUnavailable);
      }
    } finally {
      setWorking(false);
    }
  }

  async function handleDecline() {
    if (!selectedRequest || !isOpenRequest(selectedRequest)) {
      setError(t.requestUnavailable);
      return;
    }

    const reason = declineReason.trim();

    if (reason.length < 10) {
      setError(t.noReason);
      return;
    }

    setWorking(true);
    setError("");
    setSuccess("");

    try {
      await declineStaffAppointmentRequest(selectedRequest.requestId, reason);

      setSuccess(t.requestDeclined);
      setDeclineReason("");

      await Promise.all([loadRequests(), loadAnalytics()]);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setWorking(false);
    }
  }

  async function handleAttendance(
    appointment: StaffAttendanceAppointment,
    outcome: "attended" | "missed",
  ) {
    if (!isAttendanceEligible(appointment)) return;

    const confirmed = window.confirm(
      outcome === "attended" ? t.confirmAttended : t.confirmMissed,
    );

    if (!confirmed) return;

    setWorking(true);
    setError("");
    setSuccess("");

    try {
      const updated = await recordStaffAttendance(
        appointment.bookingId,
        outcome,
      );

      setAppointments((current) =>
        current.map((item) =>
          item.bookingId === updated.bookingId ? updated : item,
        ),
      );

      setSuccess(t.attendanceSaved);
      await loadAnalytics();
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setWorking(false);
    }
  }

  const refreshDashboard = () => {
    void Promise.all([loadRequests(), loadAppointments(), loadAnalytics()]);
  };

  return (
    <section className="appointment-page staff-review-page">
      <header className="appointment-intro">
        <div>
          <span className="appointment-eyebrow">{t.eyebrow}</span>
          <h1>{t.title}</h1>
          <p>{t.intro}</p>
        </div>
        <div className="appointment-intro-icon" aria-hidden="true">
          âœ“
        </div>
      </header>

      <aside className="appointment-demo-notice" role="note">
        <strong>{t.demo}</strong>
        <p>{t.demoText}</p>
      </aside>

      {error && (
        <div
          className="appointment-alert appointment-alert--error"
          role="alert"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError("")}
            aria-label={t.dismiss}
          >
            Ã—
          </button>
        </div>
      )}

      {success && (
        <div
          className="appointment-alert appointment-alert--success"
          role="status"
        >
          <span>{success}</span>
          <button
            type="button"
            onClick={() => setSuccess("")}
            aria-label={t.dismiss}
          >
            Ã—
          </button>
        </div>
      )}

      <section className="staff-dashboard-overview" aria-labelledby="staff-overview-title">
        <div className="staff-dashboard-section-heading">
          <div>
            <span className="appointment-section-label">{t.overview}</span>
            <h2 id="staff-overview-title">{t.overview}</h2>
          </div>
          <button
            type="button"
            className="appointment-refresh-button"
            onClick={refreshDashboard}
            disabled={requestsLoading || attendanceLoading || analyticsLoading}
          >
            {requestsLoading || attendanceLoading || analyticsLoading
              ? t.refreshing
              : t.refresh}
          </button>
        </div>

        <div className="staff-overview-grid">
          <article className="staff-overview-card">
            <span>{t.totalRequests}</span>
            <strong>{analyticsLoading ? "?" : analytics?.appointmentRequests.total ?? 0}</strong>
          </article>
          <article className="staff-overview-card">
            <span>{t.pendingRequests}</span>
            <strong>{analyticsLoading ? "?" : analytics?.appointmentRequests.pending ?? 0}</strong>
          </article>
          <article className="staff-overview-card">
            <span>{t.bookedAppointments}</span>
            <strong>{analyticsLoading ? "?" : analytics?.appointments.totalBooked ?? 0}</strong>
          </article>
          <article className="staff-overview-card">
            <span>{t.attendanceRecorded}</span>
            <strong>
              {analyticsLoading
                ? "?"
                : (analytics?.appointments.attended ?? 0) +
                  (analytics?.appointments.missed ?? 0)}
            </strong>
          </article>
        </div>
      </section>

      <section className="staff-requests-workspace">
          <div className="staff-review-toolbar">
            <div>
              <span className="appointment-section-label">{t.queue}</span>
              <h2>{t.incoming}</h2>
            </div>

            <select
              value={requestFilter}
              onChange={(event) =>
                setRequestFilter(event.target.value as "open" | "all")
              }
              aria-label={t.status}
            >
              <option value="open">{t.open}</option>
              <option value="all">{t.all}</option>
            </select>
          </div>

          {requestsLoading ? (
            <div className="appointment-empty-state">
              <p>{t.loading}</p>
            </div>
          ) : visibleRequests.length === 0 ? (
            <div className="appointment-empty-state">
              <h3>
                {requestFilter === "open" ? t.noOpen : t.noRequests}
              </h3>
            </div>
          ) : (
            <div className="staff-review-layout">
              <div className="staff-request-list" aria-label={t.incoming}>
                {visibleRequests.map((request) => (
                  <button
                    type="button"
                    key={request.requestId}
                    className={`staff-request-card ${
                      selectedRequestId === request.requestId ? "active" : ""
                    }`}
                    onClick={() => {
                      setSelectedRequestId(request.requestId);
                      setDeclineReason("");
                      setError("");
                      setSuccess("");
                    }}
                  >
                    <span className="staff-request-card-top">
                      <strong>{request.department || t.notSpecified}</strong>
                      <span
                        className={`staff-request-status staff-request-status--${request.status}`}
                      >
                        {statusLabel(request.status, t)}
                      </span>
                    </span>

                    <span className="staff-request-card-patient">
                      {request.patientId}
                    </span>

                    <span className="staff-request-card-reason">
                      {request.reason}
                    </span>

                    <span className="staff-request-card-date">
                      {formatTimestamp(request.submittedAt, language)}
                    </span>
                  </button>
                ))}
              </div>

              <div className="staff-review-detail">
                {!selectedRequest ? (
                  <div className="appointment-empty-state">
                    <h3>{t.select}</h3>
                    <p>{t.selectText}</p>
                  </div>
                ) : (
                  <article className="appointment-panel staff-request-detail">
                    <div className="appointment-panel-heading">
                      <div>
                        <span className="appointment-section-label">
                          {t.details}
                        </span>
                        <h2>{selectedRequest.department || t.notSpecified}</h2>
                      </div>

                      <span
                        className={`staff-request-status staff-request-status--${selectedRequest.status}`}
                      >
                        {statusLabel(selectedRequest.status, t)}
                      </span>
                    </div>

                    <div className="staff-request-information">
                      <div>
                        <span>{t.patient}</span>
                        <strong>{selectedRequest.patientId}</strong>
                      </div>

                      <div>
                        <span>{t.preferredDoctor}</span>
                        <strong>
                          {selectedRequest.preferredDoctor || t.noPreference}
                        </strong>
                      </div>

                      <div>
                        <span>{t.preferredDates}</span>
                        <strong>
                          {selectedRequest.preferredDateStart ||
                          selectedRequest.preferredDateEnd
                            ? `${formatDate(
                                selectedRequest.preferredDateStart,
                                language,
                              )} â€“ ${formatDate(
                                selectedRequest.preferredDateEnd,
                                language,
                              )}`
                            : t.noDatePreference}
                        </strong>
                      </div>

                      <div>
                        <span>{t.submitted}</span>
                        <strong>
                          {formatTimestamp(
                            selectedRequest.submittedAt,
                            language,
                          )}
                        </strong>
                      </div>
                    </div>

                    <div className="staff-request-reason">
                      <h3>{t.reason}</h3>
                      <p>{selectedRequest.reason}</p>
                    </div>

                    {selectedRequest.bookingId && (
                      <div className="staff-request-information">
                        <div>
                          <span>{t.booking}</span>
                          <strong>{selectedRequest.bookingId}</strong>
                        </div>
                        <div>
                          <span>{t.assigned}</span>
                          <strong>
                            {selectedRequest.assignedDoctorName ||
                              t.notSpecified}
                          </strong>
                        </div>
                        <div>
                          <span>{t.date}</span>
                          <strong>
                            {formatDate(
                              selectedRequest.appointmentDate,
                              language,
                            )}
                          </strong>
                        </div>
                        <div>
                          <span>{t.time}</span>
                          <strong>
                            {selectedRequest.appointmentTime ||
                              t.notSpecified}
                          </strong>
                        </div>
                      </div>
                    )}

                    {selectedRequest.declineReason && (
                      <div className="staff-request-reason staff-decline-form">
                        <h3>{t.declineExplanation}</h3>
                        <p>{selectedRequest.declineReason}</p>
                      </div>
                    )}

                    <div className="staff-request-history">
                      <h3>{t.history}</h3>
                      {selectedRequest.statusHistory.map((item, index) => (
                        <div
                          className="staff-request-history-item"
                          key={`${item.timestamp}-${index}`}
                        >
                          <span
                            className={`staff-request-history-marker staff-request-status--${item.status}`}
                          />
                          <div>
                            <strong>{statusLabel(item.status, t)}</strong>
                            <small>
                              {formatTimestamp(item.timestamp, language)}
                            </small>
                            {item.note && <p>{item.note}</p>}
                          </div>
                        </div>
                      ))}
                    </div>

                    {isOpenRequest(selectedRequest) ? (
                      <div className="staff-request-decision">
                        <div className="staff-request-approval">
                          <h3>{t.approveTitle}</h3>

                          <label htmlFor="staff-doctor-select">
                            {t.doctor}
                          </label>
                          <select
                            id="staff-doctor-select"
                            value={selectedDoctorId}
                            onChange={(event) =>
                              setSelectedDoctorId(event.target.value)
                            }
                            disabled={doctorsLoading || working}
                          >
                            <option value="">{t.chooseDoctor}</option>
                            {doctors.map((doctor) => (
                              <option key={doctor.id} value={doctor.id}>
                                {doctor.name} â€” {doctor.department}
                              </option>
                            ))}
                          </select>

                          {doctors
                            .filter((doctor) => doctor.id === selectedDoctorId)
                            .map((doctor) => (
                              <div className="staff-selected-doctor" key={doctor.id}>
                                <DoctorAvatar
                                  doctorId={doctor.id}
                                  doctorName={doctor.name}
                                  className="staff-selected-doctor-avatar"
                                />
                                <div className="staff-selected-doctor-info">
                                  <strong>{doctor.name}</strong>
                                  <span>{doctor.department}</span>
                                  <span>{doctor.specialties.join(" · ")}</span>
                                  <small>{doctor.location}</small>
                                </div>
                              </div>
                            ))}

                          
                          {doctorsLoading && (
                            <p className="staff-form-help">{t.loadingDoctors}</p>
                          )}

                          {!doctorsLoading && doctors.length === 0 && (
                            <p className="staff-form-help">{t.noDoctors}</p>
                          )}

                          {selectedDoctorId && (
                            <>
                              <label htmlFor="staff-slot-select">
                                {t.appointmentDate}
                              </label>
                              <select
                                id="staff-slot-select"
                                value={selectedSlotKey}
                                onChange={(event) =>
                                  setSelectedSlotKey(event.target.value)
                                }
                                disabled={slotsLoading || working}
                              >
                                <option value="">{t.chooseSlot}</option>
                                {availableSlots.map((slot) => (
                                  <option
                                    key={slotKey(slot)}
                                    value={slotKey(slot)}
                                  >
                                    {formatDate(slot.date, language)} â€”{" "}
                                    {slot.time}
                                  </option>
                                ))}
                              </select>
                            </>
                          )}

                          {slotsLoading && (
                            <p className="staff-form-help">{t.loadingSlots}</p>
                          )}

                          {!slotsLoading &&
                            selectedDoctorId &&
                            availableSlots.length === 0 && (
                              <p className="staff-form-help">{t.noSlots}</p>
                            )}

                          <button
                            type="button"
                            className="appointment-primary-button"
                            onClick={() => void handleApprove()}
                            disabled={
                              working ||
                              doctorsLoading ||
                              slotsLoading ||
                              !selectedDoctorId ||
                              !selectedSlot
                            }
                          >
                            {working ? t.processing : t.approve}
                          </button>
                        </div>

                        <div className="staff-decline-form">
                          <h3>{t.decline}</h3>

                          <label htmlFor="staff-decline-reason">
                            {t.explanation}
                          </label>
                          <textarea
                            id="staff-decline-reason"
                            value={declineReason}
                            onChange={(event) =>
                              setDeclineReason(event.target.value)
                            }
                            placeholder={t.declinePlaceholder}
                            minLength={10}
                            maxLength={500}
                            rows={4}
                            disabled={working}
                          />

                          <small className="staff-form-help">
                            {t.minimum}
                          </small>

                          <button
                            type="button"
                            className="staff-decline-button"
                            onClick={() => void handleDecline()}
                            disabled={working || declineReason.trim().length < 10}
                          >
                            {working ? t.processing : t.declineButton}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="staff-request-decided">{t.decided}</p>
                    )}
                  </article>
                )}
              </div>
            </div>
          )}
      </section>

      <section className="appointment-panel staff-attendance-panel">
          <div className="appointment-panel-heading">
            <div>
              <span className="appointment-section-label">
                {t.attendance}
              </span>
              <h2>{t.attendanceTitle}</h2>
              <p className="appointment-panel-description">
                {t.attendanceText}
              </p>
            </div>
          </div>

          <div className="staff-attendance-controls">
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t.search}
              aria-label={t.search}
            />

            <select
              value={attendanceFilter}
              onChange={(event) => setAttendanceFilter(event.target.value)}
              aria-label={t.statusColumn}
            >
              <option value="all">{t.filterAll}</option>
              <option value="pending">{t.filterPending}</option>
              <option value="attended">{t.filterAttended}</option>
              <option value="missed">{t.filterMissed}</option>
            </select>
          </div>

          {attendanceLoading ? (
            <div className="appointment-empty-state">
              <p>{t.loading}</p>
            </div>
          ) : visibleAppointments.length === 0 ? (
            <div className="appointment-empty-state">
              <h3>{t.noAppointments}</h3>
              <p>{t.noAppointmentsText}</p>
            </div>
          ) : (
            <div className="staff-attendance-table-wrap">
              <table className="staff-attendance-table">
                <thead>
                  <tr>
                    <th>{t.patientColumn}</th>
                    <th>{t.departmentColumn}</th>
                    <th>{t.doctorColumn}</th>
                    <th>{t.schedule}</th>
                    <th>{t.statusColumn}</th>
                    <th>{t.actions}</th>
                  </tr>
                </thead>

                <tbody>
                  {visibleAppointments.map((appointment) => {
                    const status = attendanceStatus(appointment, t);
                    const eligible = isAttendanceEligible(appointment);

                    return (
                      <tr key={appointment.bookingId}>
                        <td>
                          <strong>{appointment.patientId}</strong>
                          <small>{appointment.bookingId}</small>
                        </td>

                        <td>{appointment.department}</td>
                        <td>{appointment.doctorName}</td>

                        <td>
                          <strong>
                            {formatDate(appointment.date, language)}
                          </strong>
                          <small>{appointment.time}</small>
                        </td>

                        <td>
                          <span
                            className={`staff-attendance-status staff-attendance-status--${status.kind}`}
                          >
                            {status.label}
                          </span>
                        </td>

                        <td>
                          {eligible ? (
                            <div className="staff-attendance-actions">
                              <button
                                type="button"
                                disabled={working}
                                onClick={() =>
                                  void handleAttendance(appointment, "attended")
                                }
                              >
                                {t.markAttended}
                              </button>

                              <button
                                type="button"
                                disabled={working}
                                onClick={() =>
                                  void handleAttendance(appointment, "missed")
                                }
                              >
                                {t.markMissed}
                              </button>
                            </div>
                          ) : appointment.status === "confirmed_demo" ? (
                            <span className="staff-attendance-upcoming">
                              {t.futureNotice}
                            </span>
                          ) : (
                            <span className="staff-attendance-recorded">â€”</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
      </section>

      <section className="staff-analytics-panel" aria-labelledby="staff-analytics-title">
        <div className="appointment-panel-heading">
          <div>
            <span className="appointment-section-label">{t.analytics}</span>
            <h2 id="staff-analytics-title">{t.analytics}</h2>
          </div>
        </div>

        <p className="staff-analytics-note">{t.analyticsNote}</p>

        {analyticsLoading ? (
          <div className="appointment-empty-state">
            <p>{t.loading}</p>
          </div>
        ) : !analytics ? (
          <div className="appointment-empty-state">
            <p>{t.noBookingData}</p>
          </div>
        ) : (
          <div className="staff-analytics-grid">
            <article className="staff-analytics-card">
              <h3>{t.doctorBookings}</h3>
              {analytics.appointments.doctorRankings.length === 0 ? (
                <p>{t.noRanking}</p>
              ) : (
                <ol className="staff-analytics-ranking">
                  {analytics.appointments.doctorRankings.map((doctor) => (
                    <li key={doctor.doctorId}>
                      <div>
                        <strong>{doctor.doctorName}</strong>
                        <small>{doctor.department}</small>
                      </div>
                      <span>{doctor.totalBooked}</span>
                    </li>
                  ))}
                </ol>
              )}
            </article>

            <article className="staff-analytics-card">
              <h3>{t.departmentBookings}</h3>
              {analytics.appointments.departmentRankings.length === 0 ? (
                <p>{t.noRanking}</p>
              ) : (
                <ol className="staff-analytics-ranking">
                  {analytics.appointments.departmentRankings.map((department) => (
                    <li key={department.department}>
                      <strong>{department.department}</strong>
                      <span>{department.totalBooked}</span>
                    </li>
                  ))}
                </ol>
              )}
            </article>

            <article className="staff-analytics-card staff-analytics-card--trend">
              <h3>{t.monthlyBookings}</h3>
              {analytics.appointments.monthlyTrend.length === 0 ? (
                <p>{t.noBookingData}</p>
              ) : (
                <div className="staff-monthly-trend">
                  {analytics.appointments.monthlyTrend.map((month) => {
                    const maximum = Math.max(
                      ...analytics.appointments.monthlyTrend.map(
                        (item) => item.totalBooked,
                      ),
                      1,
                    );

                    return (
                      <div className="staff-monthly-trend-item" key={month.month}>
                        <div className="staff-monthly-trend-label">
                          <span>{month.month}</span>
                          <strong>{month.totalBooked}</strong>
                        </div>
                        <div
                          className="staff-monthly-trend-track"
                          role="meter"
                          aria-label={`${month.month}: ${month.totalBooked}`}
                          aria-valuemin={0}
                          aria-valuemax={maximum}
                          aria-valuenow={month.totalBooked}
                        >
                          <span
                            style={{
                              width: `${(month.totalBooked / maximum) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </article>
          </div>
        )}

        <div className="staff-ai-analytics-notice">
          <strong>{t.aiActivityUnavailable}</strong>
        </div>
      </section>
    </section>
  );
}

