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
  listStaffCareCases,
  updateStaffCareCaseStatus,
  type StaffCareCase,
  type StaffCareCaseStatus,
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
    careCasesTitle: "Patient care concerns",
    careCasesIntro: "Review patient-submitted concerns. These records have not been clinically triaged.",
    careCasesQueue: "CARE CONCERN QUEUE",
    careCasesLoading: "Loading care concerns...",
    careCasesEmpty: "No care concerns have been submitted.",
    careCasePatient: "Patient reference",
    careCaseConcern: "Reported concern",
    careCaseSubmitted: "Submitted",
    careCaseHistory: "Workflow history",
    careCaseInternalNote: "Internal staff note (not visible to the patient)",
    careCaseNotePlaceholder: "Add an internal review note (optional, max 300 characters)",
    careCaseAcknowledge: "Acknowledge receipt",
    careCaseStartReview: "Start review",
    careCaseResolve: "Mark workflow resolved",
    careCaseResolved: "Workflow resolved",
    careCaseUntriagedNotice: "Workflow status is not a clinical triage result. A qualified clinician must assess urgency.",
    careCasePriorityHeading: "Automated priority suggestion",
    careCasePriorityEmergency: "Emergency",
    careCasePriorityUrgent: "Urgent",
    careCasePriorityRoutine: "Routine review",
    careCasePriorityNotice: "Prototype rule-based suggestion only. This is not a clinical triage decision and must be verified by a qualified clinician.",
    careCaseConfirm: "Confirm this workflow update?",
    careCaseUpdated: "Care-case workflow updated.",
    careCaseCount: "cases in queue",
    demo: "Demo staff workspace — synthetic data only",
    demoText:
      "All requests and appointments shown here are fictional demonstration records. This workspace is not connected to a live hospital system. Do not enter real patient information.",
    requests: "Appointment requests",
    attendance: "Attendance",
    openRequests: "requests awaiting a decision",
    refresh: "Refresh",
    refreshing: "Refreshing…",
    open: "Open requests",
    all: "All requests",
    queue: "REQUEST QUEUE",
    incoming: "Incoming requests",
    loading: "Loading…",
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
    processing: "Processing…",
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
    loadingDoctors: "Loading doctors…",
    loadingSlots: "Loading available slots…",
    slotUnavailable: "This slot is no longer available. Refresh the slots and try again.",
    requestUnavailable: "This request is no longer available for review.",
  },
  am: {
    eyebrow: "የሰራተኞች የስራ ቦታ",
    title: "የቀጠሮ አስተዳደር",
    intro: "የቀጠሮ ጥያቄዎችን ይመልከቱ እና የታካሚዎችን መገኘት ያስተዳድሩ።",
    demo: "የሙከራ የሰራተኞች ቦታ — ሰው ሰራሽ መረጃ ብቻ",
    demoText:
      "እዚህ የሚታዩት ጥያቄዎችና ቀጠሮዎች ሁሉ ለሙከራ የተፈጠሩ ናቸው። ይህ ስርዓት ከእውነተኛ የሆስፒታል ስርዓት ጋር አልተገናኘም። እውነተኛ የታካሚ መረጃ አያስገቡ።",
    requests: "የቀጠሮ ጥያቄዎች",
    attendance: "የታካሚ መገኘት",
    openRequests: "ውሳኔ የሚጠብቁ ጥያቄዎች",
    refresh: "አድስ",
    refreshing: "በማደስ ላይ…",
    open: "ክፍት ጥያቄዎች",
    all: "ሁሉም ጥያቄዎች",
    queue: "የጥያቄ ዝርዝር",
    incoming: "የገቡ ጥያቄዎች",
    loading: "በመጫን ላይ…",
    noOpen: "ክፍት ጥያቄ የለም",
    noRequests: "ምንም ጥያቄ አልተገኘም",
    select: "ጥያቄ ይምረጡ",
    selectText: "ዝርዝሩን በመጠቀም የሚፈልጉትን ጥያቄ ይምረጡ።",
    details: "የጥያቄ ዝርዝር",
    patient: "የታካሚ መለያ",
    preferredDoctor: "የተመረጠ ሐኪም",
    noPreference: "ምርጫ የለም",
    preferredDates: "የተመረጡ ቀናት",
    submitted: "የቀረበበት ጊዜ",
    reason: "የጉብኝት ምክንያት",
    booking: "የሙከራ ቀጠሮ መለያ",
    assigned: "የተመደበ ሐኪም",
    date: "የቀጠሮ ቀን",
    time: "የቀጠሮ ሰዓት",
    declineExplanation: "የመከልከያ ምክንያት",
    history: "የሁኔታ ታሪክ",
    approveTitle: "ጥያቄውን ያጽድቁ እና ቀጠሮ ይመድቡ",
    doctor: "ሐኪም",
    chooseDoctor: "ሐኪም ይምረጡ",
    appointmentDate: "የቀጠሮ ጊዜ",
    appointmentTime: "የቀጠሮ ሰዓት",
    approve: "አጽድቅ እና የሙከራ ቀጠሮ መዝግብ",
    decline: "ጥያቄውን ከልክል",
    explanation: "ምክንያት (አስፈላጊ)",
    declinePlaceholder: "ጥያቄው ለምን መቀበል እንደማይቻል ያብራሩ።",
    declineButton: "የሙከራ ጥያቄን ከልክል",
    processing: "በሂደት ላይ…",
    decided: "ይህ ጥያቄ አስቀድሞ ውሳኔ ተሰጥቶታል።",
    notSpecified: "አልተገለጸም",
    submittedStatus: "ቀርቧል",
    underReview: "በግምገማ ላይ",
    needsInfo: "ተጨማሪ መረጃ ያስፈልጋል",
    offered: "ቀጠሮ ቀርቧል",
    confirmed: "ቀጠሮ ተረጋግጧል",
    declined: "ተከልክሏል",
    cancelled: "ተሰርዟል",
    attendanceTitle: "የቀጠሮ መገኘት መዝገብ",
    attendanceText: "የተረጋገጡ ቀጠሮዎችን ይመልከቱ እና ታካሚው መጥቶ እንደነበር ይመዝግቡ።",
    total: "ቀጠሮዎች",
    search: "ታካሚ፣ ሐኪም፣ ክፍል ወይም የቀጠሮ መለያ ይፈልጉ",
    filterAll: "ሁሉም ቀጠሮዎች",
    filterPending: "መገኘት የሚጠብቁ",
    filterAttended: "ተገኝቷል",
    filterMissed: "አልተገኘም",
    patientColumn: "ታካሚ",
    departmentColumn: "ክፍል",
    doctorColumn: "ሐኪም",
    schedule: "የቀጠሮ ጊዜ",
    statusColumn: "የመገኘት ሁኔታ",
    actions: "ተግባሮች",
    upcoming: "ወደፊት ያለ",
    pending: "በመጠባበቅ ላይ",
    attended: "ተገኝቷል",
    missed: "አልተገኘም",
    markAttended: "ተገኝቷል ብለህ መዝግብ",
    markMissed: "አልተገኘም ብለህ መዝግብ",
    noAppointments: "ቀጠሮ አልተገኘም",
    noAppointmentsText: "የተረጋገጡ የሙከራ ቀጠሮዎች እዚህ ይታያሉ።",
    futureNotice: "የመገኘት ሁኔታ መመዝገብ የሚቻለው ከቀጠሮው ጊዜ በኋላ ብቻ ነው።",
    confirmAttended: "ይህ ታካሚ በቀጠሮው ላይ እንደተገኘ ያረጋግጡ?",
    confirmMissed: "ይህ ታካሚ በቀጠሮው ላይ እንዳልተገኘ ያረጋግጡ?",
    attendanceSaved: "የመገኘት መረጃው በተሳካ ሁኔታ ተመዝግቧል።",
    patientReference: "የታካሚ መለያ",
    bookingReference: "የቀጠሮ መለያ",
    error: "ችግር ተፈጥሯል። እንደገና ይሞክሩ።",
    connection: "ከሙከራ ባክኤንድ ጋር መገናኘት አልተቻለም።",
    auth: "የሰራተኛ ሙከራ ማረጋገጫ አልተሳካም።",
    dismiss: "መልዕክቱን ዝጋ",
    minimum: "ቢያንስ 10 ቁምፊዎች",
    noDoctors: "ለዚህ ክፍል ሐኪም አልተገኘም።",
    noSlots: "በተመረጠው የቀን ክልል ውስጥ ክፍት ቀጠሮ አልተገኘም።",
    chooseSlot: "ክፍት ቀንና ሰዓት ይምረጡ",
    requestApproved: "ጥያቄው ጸድቋል እና የሙከራ ቀጠሮ ተመዝግቧል።",
    requestDeclined: "የቀጠሮ ጥያቄው ተከልክሏል።",
    noReason: "እባክዎ የመከልከያ ምክንያት ያስገቡ።",
    preferredRange: "የተመረጠ የቀን ክልል",
    status: "ሁኔታ",
    viewRequest: "ጥያቄውን ይመልከቱ",
    noDoctorPreference: "የተመረጠ ሐኪም አልተገለጸም።",
    noDatePreference: "የተመረጡ ቀናት አልተገለጹም።",
    loadingDoctors: "ሐኪሞችን በመጫን ላይ…",
    loadingSlots: "ክፍት ቀጠሮዎችን በመፈለግ ላይ…",
    slotUnavailable: "ይህ ቀጠሮ ከአሁን በኋላ ክፍት አይደለም። እንደገና ይፈልጉ።",
    requestUnavailable: "ይህ ጥያቄ ከአሁን በኋላ ለግምገማ አይገኝም።",
    overview: "የዳሽቦርድ አጠቃላይ እይታ",
    totalRequests: "ጠቅላላ ጥያቄዎች",
    pendingRequests: "ውሳኔ የሚጠብቁ ጥያቄዎች",
    bookedAppointments: "የተያዙ ቀጠሮዎች",
    attendanceRecorded: "\u12e8\u1270\u1218\u12d8\u1308\u1261 \u12e8\u1273\u12ab\u121a \u1218\u1308\u1298\u1276\u127d",
    analytics: "የቀጠሮ ትንተና",
    doctorBookings: "\u1265\u12d9 \u1240\u1320\u122e \u12e8\u1270\u1218\u12f0\u1260\u120b\u1278\u12cd \u1210\u12aa\u121e\u127d",
    departmentBookings: "በክፍል የተከፋፈሉ ቀጠሮዎች",
    monthlyBookings: "ወርሐዊ የቀጠሮ አዝማሚያ",
    noBookingData: "እስካሁን ምንም የቀጠሮ መረጃ የለም።",
    noRanking: "እስካሁን ለደረጃ ማውጣት የሚያስችሉ የቀጠሮ መዝገቦች የሉም።",
    aiActivityUnavailable: "የAI ረዳቱ እንቅስቃሴ ትንተና እስካሁን አይገኝም።",
    analyticsNote: "እነዚህ መለኪያዎች በሙከራ ስርዓት ውስጥ የተመዘገቡ የቀጠሮ መረጃዎችን ያሳያሉ። የAI ምክሮችን ወይም ከረዳቱ ጋር የተደረጉ ውይይቶችን አይለኩም።",
    careCasesTitle: "የታካሚዎች የጤና ስጋቶች",
    careCasesIntro: "ታካሚዎች ያቀረቡትን የጤና ስጋቶች ይገምግሙ። እነዚህ መዝገቦች በጤና ባለሙያ ገና አልተገመገሙም።",
    careCasesQueue: "የጤና ስጋት ወረፋ",
    careCasesLoading: "የጤና ስጋቶች በመጫን ላይ...",
    careCasesEmpty: "ምንም የጤና ስጋት አልቀረበም።",
    careCasePatient: "የታካሚ መለያ",
    careCaseConcern: "የቀረበው ስጋት",
    careCaseSubmitted: "የቀረበበት ጊዜ",
    careCaseHistory: "የሂደት ታሪክ",
    careCaseInternalNote: "የውስጥ ሰራተኞች ማስታወሻ (ለታካሚው አይታይም)",
    careCaseNotePlaceholder: "የውስጥ ግምገማ ማስታወሻ ያክሉ (አማራጭ፣ ከ300 ቁምፊዎች አይበልጥም)",
    careCaseAcknowledge: "መቀበሉን ያረጋጁ",
    careCaseStartReview: "ግምገማ ይጀምሩ",
    careCaseResolve: "ሂደቱን እንደተጠናቀቀ ምልክት ያድርጉ",
    careCaseResolved: "ሂደቱ ተጠናቋል",
    careCaseUntriagedNotice: "የስራ ስርዓቱ ሁኔታ የሕክምና አስቸኳይነት ደረጃን የሚወስን ግምገማ አይደለም። ብቃት ያለው የጤና ባለሙያ የሕክምና ሁኔታውን መገምገም አለበት።",
    careCasePriorityHeading: "በራስ-ሰር የቀረበ የማስተላለፊያ ጥቆማ",
    careCasePriorityEmergency: "የአስቸኳይ ምልክት ደንብ ተዛምዷል",
    careCasePriorityUrgent: "ፈጣን ክትትል ይመከራል",
    careCasePriorityRoutine: "መደበኛ የግምገማ ወረፋ",
    careCasePriorityNotice: "ይህ በሙከራ ላይ ያለ በደንቦች ላይ የተመሠረተ ጥቆማ ብቻ ነው። ይህ የሕክምና አስቸኳይነት ውሳኔ አይደለም፤ ብቃት ባለው የጤና ባለሙያ ማረጋገጥ አለበት።",
    careCaseConfirm: "ይህን የሂደት ማዘመኛ ያረጋጁ?",
    careCaseUpdated: "የጤና ስጋት ሂደት ተዘምኗል።",
    careCaseCount: "ጉዳዮች በወረፋ ላይ",

  },
} as const;

type StaffReviewCopy = { [Key in keyof typeof copy.en]: string };

function displayDepartment(value: string, language: Language): string {
  if (language !== "am") return value;

  const labels: Record<string, string> = {
    Cardiology: "\u12e8\u120d\u1265 \u1205\u12ad\u121d\u1293",
    Dental: "\u12e8\u1325\u122d\u1235 \u1205\u12ad\u121d\u1293",
    Dermatology: "\u12e8\u1246\u12f3 \u1205\u12ad\u121d\u1293",
    ENT: "\u12e8\u1306\u122e\u1363 \u12e8\u12a0\u134d\u1295\u132b\u1293 \u12e8\u1309\u122e\u122e \u1205\u12ad\u121d\u1293",
    Endocrinology: "\u12e8\u1206\u122d\u121e\u1295 \u1205\u12ad\u121d\u1293",
    Gastroenterology: "\u12e8\u121d\u130d\u1265 \u1218\u134d\u132b \u1235\u122d\u12d3\u1275 \u1205\u12ad\u121d\u1293",
    "General Medicine": "\u12a0\u1320\u1243\u120b\u12ed \u1205\u12ad\u121d\u1293",
    Gynecology: "\u12e8\u121b\u1205\u1340\u1295 \u1205\u12ad\u121d\u1293",
    Nephrology: "\u12e8\u12a9\u120b\u120a\u1275 \u1205\u12ad\u121d\u1293",
    Neurology: "\u12e8\u1290\u122d\u126d \u1205\u12ad\u121d\u1293",
    Ophthalmology: "\u12e8\u12d3\u12ed\u1295 \u1205\u12ad\u121d\u1293",
    Orthopedics: "\u12e8\u12a0\u1325\u1295\u1293 \u1218\u1308\u1303\u1300\u121a\u12eb \u1205\u12ad\u121d\u1293",
    Pediatrics: "\u12e8\u1205\u1343\u1293\u1275 \u1205\u12ad\u121d\u1293",
    Psychiatry: "\u12e8\u12a0\u12a5\u121d\u122e \u1304\u1293 \u1205\u12ad\u121d\u1293",
    "Respiratory Clinic": "\u12e8\u1218\u1270\u1295\u1348\u123b \u12a0\u12ab\u120b\u1275 \u1205\u12ad\u121d\u1293",
    Urology: "\u12e8\u123d\u1295\u1275 \u1235\u122d\u12d3\u1275 \u1205\u12ad\u121d\u1293",
  };

  return labels[value] ?? value;
}


function displaySpecialty(value: string, language: Language): string {
  if (language !== "am") return value;

  const departmentLabel = displayDepartment(value, language);
  if (departmentLabel !== value) return departmentLabel;

  const labels: Record<string, string> = {
    "Hypertension follow-up": "\u12e8\u12f0\u121d \u130d\u134a\u1275 \u12ad\u1275\u1275\u120d",
    "Chronic disease follow-up": "\u12e8\u1208\u1218\u12f5\u121d \u130a\u12dc \u1260\u122d\u1273\u12ce\u127d \u12ad\u1275\u1275\u120d",
    "Respiratory Medicine": "\u12e8\u1218\u1270\u1295\u1348\u123b \u12a0\u12ab\u120b\u1275 \u1205\u12ad\u121d\u1293",
    "Asthma follow-up": "\u12e8\u12a0\u1235\u121d \u12ad\u1275\u1275\u120d",
    "Blood pressure assessment": "\u12e8\u12f0\u121d \u130d\u134a\u1275 \u130d\u121d\u1308\u121b",
    "Heart health follow-up": "\u12e8\u120d\u1265 \u1304\u1293 \u12ad\u1275\u1275\u120d",
    "Skin conditions": "\u12e8\u1246\u12f3 \u127d\u130d\u122e\u127d",
    "Hair and nail conditions": "\u12e8\u1340\u1309\u122d\u1293 \u1325\u134d\u122d \u127d\u130d\u122e\u127d",
    "Headache assessment": "\u12e8\u122b\u1235 \u121d\u1273\u1275 \u130d\u121d\u1308\u121b",
    "Neurological follow-up": "\u12e8\u1290\u122d\u126d \u1205\u1218\u121d \u12ad\u1275\u1275\u120d",
    "Joint and bone conditions": "\u12e8\u1218\u1308\u1303\u1300\u121a\u12eb\u1293 \u12a0\u1325\u1295\u1275 \u127d\u130d\u122e\u127d",
    "Musculoskeletal follow-up": "\u12e8\u1301\u1295\u127b\u1293 \u12a0\u1325\u1295\u1275 \u12ad\u1275\u1275\u120d",
    "Child health": "\u12e8\u1205\u1343\u1293\u1275 \u1304\u1293",
    "Child wellness follow-up": "\u12e8\u1205\u1343\u1293\u1275 \u1304\u1293 \u12ad\u1275\u1275\u120d",
    "Women's health": "\u12e8\u1234\u1276\u127d \u1304\u1293",
    "Routine women's health visits": "\u1218\u12f0\u1260\u12db\u12ca \u12e8\u1234\u1276\u127d \u1304\u1293 \u121d\u122d\u1218\u122b",
    "Eye examinations": "\u12e8\u12d3\u12ed\u1295 \u121d\u122d\u1218\u122b",
    "Vision follow-up": "\u12e8\u12d3\u12ed\u1295 \u12a5\u12ed\u1273 \u12ad\u1275\u1275\u120d",
    "Oral health": "\u12e8\u12a0\u134d \u1304\u1293",
    "Dental check-ups": "\u12e8\u1325\u122d\u1235 \u121d\u122d\u1218\u122b",
    "Ear, Nose and Throat": "\u12e8\u1306\u122e\u1363 \u12e8\u12a0\u134d\u1295\u132b\u1293 \u12e8\u1309\u122e\u122e \u1205\u12ad\u121d\u1293",
    "ENT assessment": "\u12e8\u1306\u122e\u1363 \u12a0\u134d\u1295\u132b\u1293 \u1309\u122e\u122e \u130d\u121d\u1308\u121b",
    "Hearing and sinus concerns": "\u12e8\u1218\u1235\u121b\u1275\u1293 \u12e8\u1233\u12ed\u1290\u1235 \u127d\u130d\u122e\u127d",
    "Digestive health": "\u12e8\u121d\u130d\u1265 \u1218\u134d\u132b \u1235\u122d\u12d3\u1275 \u1304\u1293",
    "Digestive health follow-up": "\u12e8\u121d\u130d\u1265 \u1218\u134d\u132b \u1235\u122d\u12d3\u1275 \u12ad\u1275\u1275\u120d",
    "Urinary health": "\u12e8\u123d\u1295\u1275 \u1235\u122d\u12d3\u1275 \u1304\u1293",
    "Urological follow-up": "\u12e8\u123d\u1295\u1275 \u1235\u122d\u12d3\u1275 \u12ad\u1275\u1275\u120d",
    "Mental wellness consultations": "\u12e8\u12a0\u12a5\u121d\u122e \u1304\u1293 \u121d\u12ad\u12ad\u122d",
    "Follow-up consultations": "\u12e8\u12ad\u1275\u1275\u120d \u121d\u12ad\u12ad\u122d",
    "Diabetes follow-up": "\u12e8\u1235\u12b3\u122d \u1260\u122d\u1273 \u12ad\u1275\u1275\u120d",
    "Hormonal health": "\u12e8\u1206\u122d\u121e\u1295 \u1304\u1293",
    "Kidney health follow-up": "\u12e8\u12a9\u120b\u120a\u1275 \u1304\u1293 \u12ad\u1275\u1275\u120d",
    "Kidney health": "\u12e8\u12a9\u120b\u120a\u1275 \u1304\u1293",
  };

  return labels[value] ?? value;
}

function displayClinicLocation(value: string, language: Language): string {
  if (language !== "am") return value;

  const labels: Record<string, string> = {
    "Synthetic Demo Clinic A": "\u12e8\u1219\u12a8\u122b \u12ad\u120a\u1292\u12ad A",
    "Synthetic Demo Clinic B": "\u12e8\u1219\u12a8\u122b \u12ad\u120a\u1292\u12ad B",
  };

  return labels[value] ?? value;
}

function displayAppointmentRequestHistoryNote(
  note: string,
  language: Language,
): string {
  if (language !== "am") return note;

  const labels: Record<string, string> = {
    "Request submitted in the synthetic demo.":
      "\u1325\u12eb\u1244\u12cd \u1260\u1219\u12a8\u122b \u1235\u122d\u12d3\u1271 \u12cd\u1235\u1325 \u1270\u1218\u12dd\u130d\u1267\u120d\u1362",
    "Cancelled by the patient in the synthetic demo.":
      "\u1325\u12eb\u1244\u12cd \u1260\u1219\u12a8\u122b \u1235\u122d\u12d3\u1271 \u12cd\u1235\u1325 \u1260\u1273\u12ab\u121a\u12cd \u1270\u1220\u122d\u129f\u120d\u1362",
    "A synthetic demo appointment was assigned by authorized demo staff.":
      "\u1260\u1219\u12a8\u122b \u1235\u122d\u12d3\u1271 \u12cd\u1235\u1325 \u1260\u1270\u1348\u1270\u12f1 \u1230\u122b\u1270\u129e\u127d \u12e8\u1219\u12a8\u122b \u1240\u1320\u122e \u1270\u1218\u12f5\u1267\u120d\u1362",
  };

  return labels[note] ?? note;
}

function careCasePriorityLabel(
  priority: "emergency" | "urgent" | "routine_review",
  t: StaffReviewCopy,
): string {
  switch (priority) {
    case "emergency":
      return t.careCasePriorityEmergency;
    case "urgent":
      return t.careCasePriorityUrgent;
    default:
      return t.careCasePriorityRoutine;
  }
}


function careCaseStatusLabel(status: string, language: Language): string {
  if (language !== "am") return status.replaceAll("_", " ");

  switch (status) {
    case "registered":
      return "\u1270\u1218\u12dd\u130d\u1267\u12a0\u120d";
    case "acknowledged":
      return "\u1218\u1240\u1260\u1209 \u1270\u1228\u130b\u130d\u1277\u120d";
    case "in_review":
      return "\u1260\u130d\u121d\u1308\u121b \u120b\u12ed";
    case "resolved":
      return "\u1202\u12f0\u1271 \u1270\u1320\u1293\u124b\u120d";
    default:
      return status.replaceAll("_", " ");
  }
}

function careCaseHistoryNote(note: string, language: Language): string {
  const registrationNote =
    "Synthetic demonstration registration only. " +
    "This case has not been clinically triaged.";

  if (language === "am" && note === registrationNote) {
    return "\u12ed\u1205 \u1260\u1219\u12a8\u122b \u120b\u12ed \u12eb\u1208 \u121d\u12dd\u1308\u1263 \u1265\u127b \u1290\u12cd\u1362 " +
      "\u12ed\u1205 \u1309\u12f3\u12ed \u1308\u1293 \u1260\u1304\u1273 \u1263\u1208\u1219\u12eb \u12a0\u120d\u1270\u1308\u1218\u1308\u121d\u121d\u1362";
  }

  return note;
}

function errorMessage(error: unknown, t: StaffReviewCopy): string {
  if (!(error instanceof Error)) return t.error;
  if (error.message.includes("Could not connect")) return t.connection;
  if (error.message.includes("authentication failed")) return t.auth;
  return error.message;
}

function formatDate(value?: string | null, language: Language = "en"): string {
  if (!value) return language === "am" ? "አልተገለጸም" : "Not specified";

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

  const [careCases, setCareCases] = useState<StaffCareCase[]>([]);
  const [careCasesLoading, setCareCasesLoading] = useState(true);
  const [selectedCareCaseId, setSelectedCareCaseId] = useState("");
  const [careCaseNote, setCareCaseNote] = useState("");
  const [careCaseWorking, setCareCaseWorking] = useState(false);

  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedCareCase = useMemo(
    () => careCases.find((item) => item.caseId === selectedCareCaseId) ?? null,
    [careCases, selectedCareCaseId],
  );

  const visibleRequests = useMemo(() => {
    const filtered =
      requestFilter === "open" ? requests.filter(isOpenRequest) : requests;

    return [...filtered].sort((a, b) =>
      b.submittedAt.localeCompare(a.submittedAt),
    );
  }, [requests, requestFilter]);

  const selectedRequest = useMemo(
    () =>
      visibleRequests.find((item) => item.requestId === selectedRequestId) ??
      visibleRequests[0] ??
      null,
    [visibleRequests, selectedRequestId],
  );

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

  const loadCareCases = useCallback(async () => {
    setCareCasesLoading(true);
    try {
      const result = await listStaffCareCases();
      setCareCases(result);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setCareCasesLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRequests();
      void loadAppointments();
      void loadAnalytics();
      void loadCareCases();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadRequests, loadAppointments, loadAnalytics, loadCareCases]);

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

  async function handleCareCaseStatus(
    status: Exclude<StaffCareCaseStatus, "registered">,
  ) {
    if (!selectedCareCase || careCaseWorking) return;
    if (!window.confirm(t.careCaseConfirm)) return;

    setCareCaseWorking(true);
    setError("");
    setSuccess("");

    try {
      const updated = await updateStaffCareCaseStatus(
        selectedCareCase.caseId,
        status,
        careCaseNote.trim() || undefined,
      );

      setCareCases((current) =>
        current.map((item) =>
          item.caseId === updated.caseId ? updated : item,
        ),
      );
      setCareCaseNote("");
      setSuccess(t.careCaseUpdated);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setCareCaseWorking(false);
    }
  }

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
    void Promise.all([
      loadRequests(),
      loadAppointments(),
      loadAnalytics(),
      loadCareCases(),
    ]);
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
          ✓
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
            ×
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
            ×
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
            disabled={requestsLoading || attendanceLoading || analyticsLoading || careCasesLoading}
          >
            {requestsLoading || attendanceLoading || analyticsLoading || careCasesLoading
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

      <section className="staff-care-cases-panel" aria-labelledby="staff-care-cases-title">
        <div className="staff-care-cases-heading">
          <div>
            <span className="appointment-section-label">{t.careCasesQueue}</span>
            <h2 id="staff-care-cases-title">{t.careCasesTitle}</h2>
            <p>{t.careCasesIntro}</p>
          </div>
          <span className="staff-care-cases-count">
            {careCases.length} {t.careCaseCount}
          </span>
        </div>

        <p className="staff-care-cases-safety-note">{t.careCaseUntriagedNotice}</p>

        {careCasesLoading ? (
          <p className="appointment-empty-state">{t.careCasesLoading}</p>
        ) : careCases.length === 0 ? (
          <p className="appointment-empty-state">{t.careCasesEmpty}</p>
        ) : (
          <div className="staff-care-cases-layout">
            <div className="staff-care-cases-list" aria-label={t.careCasesQueue}>
              {careCases.map((item) => (
                <button
                  type="button"
                  key={item.caseId}
                  className={`staff-care-case-item ${
                    selectedCareCaseId === item.caseId
                      ? "staff-care-case-item--selected"
                      : ""
                  }`}
                  onClick={() => {
                    setSelectedCareCaseId(item.caseId);
                    setCareCaseNote("");
                  }}
                  aria-pressed={selectedCareCaseId === item.caseId}
                >
                  <span className="staff-care-case-item-top">
                    <strong>{item.patientId}</strong>
                    <span className={`staff-care-case-status staff-care-case-status--${item.status}`}>
                      {careCaseStatusLabel(item.status, language)}
                    </span>
                  </span>
                  <span
                    className={`staff-care-case-priority staff-care-case-priority--${item.prioritySuggestion}`}
                  >
                    {careCasePriorityLabel(item.prioritySuggestion, t)}
                  </span>
                  <span className="staff-care-case-item-date">
                    {formatTimestamp(item.createdAt, language)}
                  </span>
                  <span className="staff-care-case-item-summary">
                    {item.reportedConcern}
                  </span>
                </button>
              ))}
            </div>

            {selectedCareCase && (
              <article className="staff-care-case-detail">
                <div className="staff-care-case-detail-heading">
                  <div>
                    <span className="appointment-section-label">{t.careCasePatient}</span>
                    <h3>{selectedCareCase.patientId}</h3>
                  </div>
                  <span className={`staff-care-case-status staff-care-case-status--${selectedCareCase.status}`}>
                    {careCaseStatusLabel(selectedCareCase.status, language)}
                  </span>
                </div>

                <div className="staff-care-case-detail-grid">
                  <div>
                    <span>{t.careCaseSubmitted}</span>
                    <strong>{formatTimestamp(selectedCareCase.createdAt, language)}</strong>
                  </div>
                  <div>
                    <span>{t.status}</span>
                    <strong>{careCaseStatusLabel(selectedCareCase.status, language)}</strong>
                  </div>
                </div>

                <section className="staff-care-case-priority-detail">
                  <span className="appointment-section-label">
                    {t.careCasePriorityHeading}
                  </span>
                  <span
                    className={`staff-care-case-priority staff-care-case-priority--${selectedCareCase.prioritySuggestion}`}
                  >
                    {careCasePriorityLabel(selectedCareCase.prioritySuggestion, t)}
                  </span>
                  <p>{selectedCareCase.priorityReason}</p>
                  <small>{t.careCasePriorityNotice}</small>
                </section>

                <div className="staff-care-case-concern">
                  <h4>{t.careCaseConcern}</h4>
                  <p>{selectedCareCase.reportedConcern}</p>
                </div>

                <div className="staff-care-case-history">
                  <h4>{t.careCaseHistory}</h4>
                  <ol>
                    {selectedCareCase.statusHistory.map((entry, index) => (
                      <li key={`${entry.timestamp}-${entry.status}-${index}`}>
                        <strong>{careCaseStatusLabel(entry.status, language)}</strong>
                        <span>{formatTimestamp(entry.timestamp, language)}</span>
                        <p>{careCaseHistoryNote(entry.note, language)}</p>
                      </li>
                    ))}
                  </ol>
                </div>

                {selectedCareCase.status !== "resolved" && (
                  <div className="staff-care-case-actions">
                    <label htmlFor="staff-care-case-note">
                      {t.careCaseInternalNote}
                    </label>
                    <textarea
                      id="staff-care-case-note"
                      value={careCaseNote}
                      onChange={(event) =>
                        setCareCaseNote(event.target.value.slice(0, 300))
                      }
                      placeholder={t.careCaseNotePlaceholder}
                      maxLength={300}
                      rows={3}
                      disabled={careCaseWorking}
                    />
                    <div className="staff-care-case-action-row">
                      {selectedCareCase.status === "registered" && (
                        <button
                          type="button"
                          className="appointment-primary-button"
                          onClick={() => void handleCareCaseStatus("acknowledged")}
                          disabled={careCaseWorking}
                        >
                          {careCaseWorking ? t.processing : t.careCaseAcknowledge}
                        </button>
                      )}
                      {selectedCareCase.status === "acknowledged" && (
                        <button
                          type="button"
                          className="appointment-primary-button"
                          onClick={() => void handleCareCaseStatus("in_review")}
                          disabled={careCaseWorking}
                        >
                          {careCaseWorking ? t.processing : t.careCaseStartReview}
                        </button>
                      )}
                      {selectedCareCase.status === "in_review" && (
                        <button
                          type="button"
                          className="appointment-primary-button"
                          onClick={() => void handleCareCaseStatus("resolved")}
                          disabled={careCaseWorking}
                        >
                          {careCaseWorking ? t.processing : t.careCaseResolve}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {selectedCareCase.status === "resolved" && (
                  <p className="staff-care-case-resolved">{t.careCaseResolved}</p>
                )}
              </article>
            )}
          </div>
        )}
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
                      selectedRequest?.requestId === request.requestId ? "active" : ""
                    }`}
                    onClick={() => {
                      setSelectedRequestId(request.requestId);
                      setDeclineReason("");
                      setError("");
                      setSuccess("");
                    }}
                  >
                    <span className="staff-request-card-top">
                      <strong>{displayDepartment(request.department || t.notSpecified, language)}</strong>
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
                        <h2>{displayDepartment(selectedRequest.department || t.notSpecified, language)}</h2>
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
                              )} – ${formatDate(
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
                            {item.note && <p>{displayAppointmentRequestHistoryNote(item.note, language)}</p>}
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
                                {doctor.name} — {displayDepartment(doctor.department, language)}
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
                                  <span>{displayDepartment(doctor.department, language)}</span>
                                  <span>{doctor.specialties.map((specialty) => displaySpecialty(specialty, language)).join(" " + String.fromCharCode(183) + " ")}</span>
                                  <small>{displayClinicLocation(doctor.location, language)}</small>
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
                                    {formatDate(slot.date, language)} —{" "}
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

                        <td>{displayDepartment(appointment.department, language)}</td>
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
                            <span className="staff-attendance-recorded">—</span>
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
                        <small>{displayDepartment(doctor.department, language)}</small>
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
                      <strong>{displayDepartment(department.department, language)}</strong>
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

