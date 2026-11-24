import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import type { ChatMessage, Language } from "../../types/chat";
import DoctorAvatar from "../Doctor/DoctorAvatar";


function careCaseStatusLabel(status: string, language: Language): string {
  if (language !== "am") return status;

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
      return status;
  }
}

function careCaseDataNotice(notice: string, language: Language): string {
  if (language !== "am") return notice;

  const normalized = notice.replace(/\s+/g, " ").trim();

  if (
    normalized.startsWith(
      "SYNTHETIC DEMONSTRATION DATA: This emergency concern is stored only"
    )
  ) {
    return "\u12e8\u1219\u12a8\u122b \u1218\u1228\u1303\u1366 \u12ed\u1205 \u12e8\u12a0\u1235\u1278\u1293\u12b3\u12ed \u12e8\u1324\u1293 \u1235\u130b\u1275 \u1260\u12a0\u12ab\u1263\u1262\u12eb\u12ca \u12e8\u1219\u12a8\u122b \u12f3\u1274\u1264\u12dd \u12cd\u1235\u1325 \u1265\u127b \u1270\u1240\u121d\u1327\u120d\u1362 \u12c8\u12f0 \u12a5\u12cd\u1290\u1270\u129b \u1206\u1235\u1352\u1273\u120d \u12a0\u120d\u1270\u120b\u12a8\u121d\u121d\u1363 \u1260\u1206\u1235\u1352\u1273\u120d \u1230\u122b\u1270\u129e\u127d \u12a0\u120d\u1270\u1308\u1218\u1308\u121d\u121d\u1363 \u1260\u1304\u1273 \u1263\u1208\u1219\u12eb \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u120d\u1270\u12f0\u1228\u1308\u121d\u121d\u1362 \u121d\u12dd\u1308\u1263\u12cd \u12e8\u1215\u12ad\u121d\u1293 \u12a5\u122d\u12f3\u1275 \u1218\u12d8\u130b\u1300\u1271\u1295 \u12a0\u12eb\u1228\u130b\u130d\u1325\u121d\u1362 \u12ed\u1205 \u12a0\u1235\u1278\u1293\u12b3\u12ed \u1201\u1294\u1273 \u120a\u1206\u1295 \u12a8\u127b\u1208 \u12c8\u12f2\u12eb\u12cd\u1291 \u12e8\u1215\u12ad\u121d\u1293 \u12a5\u122d\u12f3\u1275 \u12ed\u1348\u120d\u1309\u1362";
  }

  if (
    normalized.startsWith(
      "SYNTHETIC DEMONSTRATION DATA: This urgent follow-up concern is stored"
    )
  ) {
    return "\u12e8\u1219\u12a8\u122b \u1218\u1228\u1303\u1366 \u12ed\u1205 \u12e8\u12a0\u1235\u1278\u1293\u12b3\u12ed \u12ad\u1275\u1275\u120d \u1235\u130b\u1275 \u1260\u12a0\u12ab\u1263\u1262\u12eb\u12ca \u12e8\u1219\u12a8\u122b \u12f3\u1274\u1264\u12dd \u12cd\u1235\u1325 \u1265\u127b \u1270\u1240\u121d\u1327\u120d\u1362 \u12c8\u12f0 \u12a5\u12cd\u1290\u1270\u129b \u1206\u1235\u1352\u1273\u120d \u12a0\u120d\u1270\u120b\u12a8\u121d\u121d\u1363 \u1260\u1206\u1235\u1352\u1273\u120d \u1230\u122b\u1270\u129e\u127d \u12a0\u120d\u1270\u1308\u1218\u1308\u121d\u121d\u1363 \u1260\u1304\u1273 \u1263\u1208\u1219\u12eb \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u120d\u1270\u12f0\u1228\u1308\u121d\u121d\u1362 \u121d\u12dd\u1308\u1263\u12cd \u12e8\u1215\u12ad\u121d\u1293 \u12a5\u122d\u12f3\u1275 \u12c8\u12ed\u121d \u12ad\u1275\u1275\u120d \u1218\u12d8\u130b\u1300\u1271\u1295 \u12a0\u12eb\u1228\u130b\u130d\u1325\u121d\u1362 \u12a5\u1263\u12ad\u12ce \u1260\u1245\u122d\u1261 \u12e8\u1324\u1293 \u1261\u12f5\u1295\u12ce\u1295 \u12eb\u1290\u130b\u130d\u1229\u1362 \u12a8\u1263\u12f5 \u12c8\u12ed\u121d \u1260\u134d\u1325\u1290\u1275 \u12e8\u121a\u1263\u1231 \u121d\u120d\u12ad\u1276\u127d \u12a8\u1273\u12e9 \u12e8\u12a0\u1235\u1278\u1293\u12b3\u12ed \u12e8\u1215\u12ad\u121d\u1293 \u12a5\u122d\u12f3\u1275 \u12ed\u1348\u120d\u1309\u1362";
  }

  return notice;
}

function getAppointmentReview(content: string) {
  const normalized = content.replace(/\*\*/g, "");

  const match = normalized.match(
    /Please review your preferred\s+SYNTHETIC demo appointment option:\s*Doctor:\s*([\s\S]*?)\s+Department:\s*([\s\S]*?)\s+Date:\s*(\d{4}-\d{2}-\d{2})\s+Time:\s*(\d{2}:\d{2})\s+Location:\s*([\s\S]*?)(?=\n\s*\n|This is fictional|This is a fictional|$)/i
  );

  if (!match) return null;

  const doctor = match[1].trim();
  const department = match[2].trim();
  const date = match[3].trim();
  const time = match[4].trim();
  const location = match[5].trim();

  if (!doctor || !department || !date || !time || !location) {
    return null;
  }

  return { doctor, department, date, time, location };
}

interface MessageBubbleProps {
  message: ChatMessage;
  language: Language;
  onDoctorSelect?: (doctorId: string) => void;
  onSlotSelect?: (slotIndex: number) => void;
  disabled?: boolean;
}

export default function MessageBubble({
  message,
  language,
  onDoctorSelect,
  onSlotSelect,
  disabled = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const content =
    typeof message.content === "string" ? message.content : "";
  const appointmentReview = getAppointmentReview(content);

  const [speaking, setSpeaking] = useState(false);
  const [expandedDoctorId, setExpandedDoctorId] =
    useState<string | null>(null);

  const speechAvailable =
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  function stopSpeech() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }

  function speakMessage() {
    if (!speechAvailable || !content.trim()) return;

    window.speechSynthesis.cancel();

    const plainText = content
      .replace(/```[\s\S]*?```/g, " Code block omitted. ")
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[#*_>`~-]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    const utterance = new SpeechSynthesisUtterance(plainText);
    utterance.lang = language === "am" ? "am-ET" : "en-US";
    utterance.rate = 0.95;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }

  const doctors = message.doctorRecommendations ?? [];
  const appointmentSlots = message.appointmentSlots ?? [];
  const careCase = message.careCase ?? null;
  const emergency = message.emergency ?? null;

  const availableDates = Array.from(
    new Set(appointmentSlots.map((slot) => slot.date))
  ).sort();

  const [selectedDate, setSelectedDate] = useState(
    availableDates[0] ?? ""
  );

  const selectedDateSlots = appointmentSlots
    .map((slot, index) => ({ slot, index }))
    .filter(({ slot }) => slot.date === selectedDate);

  const selectedDateLabel = selectedDate
    ? new Date(`${selectedDate}T12:00:00`).toLocaleDateString(undefined, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "";

  return (
    <div
      className={`message-row ${
        isUser ? "message-row-user" : "message-row-assistant"
      }`}
    >
      <div
        className={`message-bubble ${
          isUser ? "message-user" : "message-assistant"
        }`}
      >
        <div className="message-role">
          {isUser
            ? language === "am"
              ? "እርስዎ"
              : "You"
            : language === "am"
              ? "የሆስፒታል AI ረዳት"
              : "Hospital AI Assistant"}
        </div>

        <div
          className={`message-content ${
            isUser
              ? "message-content-user"
              : "message-content-assistant"
          }`}
        >
          {isUser ? (
            content
          ) : appointmentReview ? (
            <section
              className="chat-appointment-review"
              aria-label="Appointment request review"
            >
              <div className="chat-appointment-review-heading">
                <strong>Review your preferred appointment</strong>
                <span className="chat-doctor-demo-label">SYNTHETIC DEMO</span>
              </div>

              <p className="chat-appointment-review-intro">
                Please verify these details before submitting your request.
              </p>

              <dl className="chat-appointment-review-details">
                <div>
                  <dt>Doctor</dt>
                  <dd>{appointmentReview.doctor}</dd>
                </div>
                <div>
                  <dt>Department</dt>
                  <dd>{appointmentReview.department}</dd>
                </div>
                <div>
                  <dt>Date</dt>
                  <dd>
                    {new Date(`${appointmentReview.date}T12:00:00`).toLocaleDateString(
                      undefined,
                      {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                        year: "numeric",
                      }
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Time</dt>
                  <dd>{appointmentReview.time}</dd>
                </div>
                <div>
                  <dt>Location</dt>
                  <dd>{appointmentReview.location}</dd>
                </div>
              </dl>

              <p className="chat-appointment-review-notice">
                This is a fictional demonstration option. Submitting it creates
                a request for staff review, not a confirmed or reserved
                appointment.
              </p>

              <div className="chat-appointment-review-confirmation">
                <strong>Awaiting your confirmation</strong>
                <span>Reply YES to submit your request, or NO to cancel.</span>
              </div>
            </section>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeSanitize]}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>

        {!isUser && emergency?.active && (
          <section
            className="chat-emergency-alert"
            role="alert"
            aria-label="Emergency safety instructions"
          >
            <div className="chat-emergency-alert-heading">
              <strong>Possible emergency - get help now</strong>
              <span>IMMEDIATE ACTION</span>
            </div>

            <p>
              Go to the nearest emergency department or contact local
              emergency services. Do not wait for this assistant.
            </p>

            <div className="chat-emergency-contact-details">
              <div className="chat-emergency-contact-row">
                <span>Sample hospital emergency line</span>
                <strong>+251 9XX XXX XXX</strong>
              </div>
              <div className="chat-emergency-contact-row">
                <span>Sample ambulance dispatch line</span>
                <strong>+251 9XX XXX XXX</strong>
              </div>
            </div>

            <p className="chat-emergency-demo-notice">
              DEMO ONLY: These are fictional placeholder numbers, not real
              telephone numbers. Do not call them. No emergency dispatch or
              hospital contact service is connected. Use locally available
              emergency services.
            </p>
          </section>
        )}

        {!isUser && emergency?.active && emergency.directory && (
          <section
            className="chat-emergency-directory"
            aria-label="Emergency department demonstration directory"
          >
            <div className="chat-emergency-directory-heading">
              <div>
                <strong>{emergency.directory.departmentName}</strong>
                <span>{emergency.directory.facilityName}</span>
              </div>
              <span className="chat-emergency-directory-label">
                FICTIONAL DEMO
              </span>
            </div>

            <div className="chat-emergency-directory-location">
              <strong>Sample department location</strong>
              <p>{emergency.directory.address}</p>
              <p>
                <strong>Floor:</strong> {emergency.directory.floor}
              </p>
              <p>
                <strong>Office:</strong> {emergency.directory.roomNumber}
              </p>
              <p>{emergency.directory.directions}</p>
              <p className="chat-emergency-directory-warning">
                Fictional example only. These directions, floor and room
                details are not verified hospital information. Do not use
                them for navigation.
              </p>
            </div>

            <div className="chat-emergency-doctors">
              <strong>Sample emergency department doctors</strong>
              {emergency.directory.doctors.map((doctor) => (
                <div className="chat-emergency-doctor" key={doctor.id}>
                  <div className="chat-emergency-doctor-initials">
                    {doctor.name
                      .split(" ")
                      .map((part) => part[0] ?? "")
                      .join("")
                      .slice(0, 2)}
                  </div>
                  <div className="chat-emergency-doctor-info">
                    <strong>{doctor.name}</strong>
                    <span>{doctor.specialty}</span>
                    <small>
                      Availability has not been provided.
                    </small>
                  </div>
                </div>
              ))}
            </div>

            <p className="chat-emergency-directory-warning">
              All facility and doctor entries above are fictional
              demonstration data, not a real hospital directory.
            </p>
          </section>
        )}

        {!isUser && careCase && (
          <section
            className="chat-care-case"
            aria-label={language === "am" ? "\u12e8\u1324\u1293 \u1235\u130b\u1275 \u1218\u12dd\u1308\u1262\u12eb" : "Emergency concern registration"}
          >
            <div className="chat-care-case-heading">
              <div>
                <strong>{language === "am" ? "\u12e8\u1324\u1293 \u1235\u130b\u1275 \u1270\u1218\u12dd\u130d\u1267\u120d" : "Emergency concern registered"}</strong>
                <span className="chat-care-case-status">
                  {language === "am" ? "\u12e8\u1218\u12dd\u1308\u1263 \u1201\u1294\u1273" : "Registration status"}: {careCaseStatusLabel(careCase.status, language)}
                </span>
              </div>
              <span className="chat-care-case-demo-label">
                {language === "am" ? "\u12e8\u1219\u12a8\u122b \u1218\u1228\u1303" : "SYNTHETIC DEMO"}
              </span>
            </div>

            <div className="chat-care-case-reference">
              <span>{language === "am" ? "\u12e8\u1219\u12a8\u122b \u1309\u12f3\u12ed \u1218\u1208\u12eb" : "Demonstration case reference"}</span>
              <strong>{careCase.caseId}</strong>
            </div>

            <div className="chat-care-case-details">
              <div>
                <span>{language === "am" ? "\u12e8\u1270\u1240\u1228\u1260\u12cd \u12e8\u1324\u1293 \u1235\u130b\u1275" : "Reported concern"}</span>
                <p>{careCase.reportedConcern}</p>
              </div>
              <div>
                <span>{language === "am" ? "\u12e8\u1270\u1218\u12dd\u1308\u1260\u1260\u1275 \u130a\u12dc" : "Registered"}</span>
                <time dateTime={careCase.createdAt}>
                  {Number.isNaN(Date.parse(careCase.createdAt))
                    ? careCase.createdAt
                    : new Date(careCase.createdAt).toLocaleString()}
                </time>
              </div>
            </div>

            <p className="chat-care-case-data-notice">
              {careCaseDataNotice(careCase.dataNotice, language)}
            </p>

            <div className="chat-care-case-safety-notice" role="note">
              <strong>{language === "am" ? "\u12a0\u1218\u12b3\u12ed\u1366 \u12ed\u1205 \u12e8\u12a5\u12cd\u1290\u1270\u129b \u12e8\u1206\u1235\u1352\u1273\u120d \u121b\u1233\u12c8\u1242\u12eb \u12a0\u12ed\u12f0\u1208\u121d\u1362" : "Important: this is not a real hospital notification."}</strong>
              <p>
                {language === "am"
                  ? "\u12ed\u1205 \u1218\u12dd\u1308\u1265 \u1260\u12da\u1205 \u12e8\u1219\u12a8\u122b \u1235\u122d\u12d3\u1275 \u12cd\u1235\u1325 \u1265\u127b \u1270\u1240\u121d\u1327\u120d\u1362 \u12c8\u12f0 \u1206\u1235\u1352\u1273\u120d \u1230\u122b\u1270\u129e\u127d \u12a0\u120d\u1270\u120b\u12a8\u121d\u121d\u1363 \u1260\u1230\u122b\u1270\u129e\u127d \u12a0\u12cd\u1295\u1273 \u12a0\u120d\u1270\u1228\u130b\u1308\u1320\u121d\u121d\u1363 \u1260\u1304\u1273 \u1263\u1208\u1219\u12eb \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u120d\u1270\u12f0\u1228\u1308\u1218\u1208\u1275\u121d\u1362 \u12ed\u1205 \u12e8\u12a0\u1235\u1278\u1293\u12b3\u12ed \u12a5\u122d\u12f3\u1275 \u12a0\u1308\u120d\u130d\u120e\u1275 \u12a0\u12ed\u12f0\u1208\u121d\u1362 \u12a0\u1235\u1278\u1293\u12b3\u12ed \u12a8\u1206\u1290 \u12c8\u12f2\u12eb\u12cd\u1291 \u12e8\u12a0\u12ab\u1263\u1262\u12eb\u12ce\u1295 \u12a0\u1235\u1278\u1293\u12b3\u12ed \u12a0\u1308\u120d\u130d\u120e\u1275 \u12eb\u130d\u1299 \u12c8\u12ed\u121d \u12c8\u12f0 \u12a0\u1245\u122b\u1262\u12eb\u12ce \u12a0\u1235\u1278\u1293\u12b3\u12ed \u12e8\u1215\u12ad\u121d\u1293 \u12ad\u134d\u120d \u12ed\u1202\u12f1\u1362"
                  : "This record is stored only in this demonstration. It has not been sent to hospital staff, has not been acknowledged by staff, and has not been clinically triaged. This is not an emergency response service. If this is an emergency, contact local emergency services or go to the nearest emergency department."}
              </p>
            </div>
          </section>
        )}

        {!isUser && doctors.length > 0 && (
          <section
            className="chat-doctor-results"
            aria-label="Doctor recommendations"
          >
            <div className="chat-doctor-results-heading">
              <div>
                <strong>Available doctors</strong>
                <span>
                  {doctors.length} {doctors.length === 1 ? "doctor" : "doctors"} in the demo directory
                </span>
              </div>
              <span className="chat-doctor-demo-label">
                DEMO DIRECTORY
              </span>
            </div>

            <div className="chat-doctor-list">
              {doctors.map((doctor, index) => {
                const isExpanded =
                  expandedDoctorId === doctor.id;

                return (
                  <article
                    className="chat-doctor-card"
                    key={doctor.id}
                  >
                    <div className="chat-doctor-card-main">
                      <DoctorAvatar
                        key={doctor.id}
                        doctorId={doctor.id}
                        doctorName={doctor.name}
                        className="chat-doctor-avatar"
                      />

                      <div className="chat-doctor-summary">
                        <div className="chat-doctor-name-line">
                          <strong>{doctor.name}</strong>
                          {doctor.isAssignedDoctor && (
                            <span className="chat-doctor-assigned">
                              Assigned doctor
                            </span>
                          )}
                        </div>

                        <span className="chat-doctor-department">
                          {doctor.department || "Department not specified"}
                        </span>

                        <span className="chat-doctor-location">
                          {doctor.location || "Location not specified"}
                        </span>

                        {doctor.specialties.length > 0 && (
                          <div className="chat-doctor-specialties">
                            {doctor.specialties.map((specialty) => (
                              <span key={specialty}>{specialty}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="chat-doctor-details">
                        <strong>Directory details</strong>
                        <dl>
                          <div>
                            <dt>Department</dt>
                            <dd>
                              {doctor.department || "Not specified"}
                            </dd>
                          </div>
                          <div>
                            <dt>Specialties</dt>
                            <dd>
                              {doctor.specialties.length > 0
                                ? doctor.specialties.join(", ")
                                : "Not specified"}
                            </dd>
                          </div>
                          <div>
                            <dt>Location</dt>
                            <dd>
                              {doctor.location || "Not specified"}
                            </dd>
                          </div>
                          <div>
                            <dt>Patient assignment</dt>
                            <dd>
                              {doctor.isAssignedDoctor
                                ? "Your assigned doctor"
                                : "Not listed as your assigned doctor"}
                            </dd>
                          </div>
                        </dl>
                        <p>
                          Additional profile information is not available
                          in this fictional demonstration directory.
                        </p>
                      </div>
                    )}

                    <div className="chat-doctor-actions">
                      <button
                        type="button"
                        className="chat-doctor-details-button"
                        aria-expanded={isExpanded}
                        onClick={() =>
                          setExpandedDoctorId(
                            isExpanded ? null : doctor.id
                          )
                        }
                      >
                        {isExpanded ? "Hide details" : "View details"}
                      </button>

                      <button
                        type="button"
                        className="chat-doctor-select-button"
                        disabled={disabled || !onDoctorSelect}
                        onClick={() => onDoctorSelect?.(doctor.id)}
                      >
                        Select this doctor
                      </button>
                    </div>

                    <span className="chat-doctor-number">
                      Option {index + 1}
                    </span>
                  </article>
                );
              })}
            </div>

            <p className="chat-doctor-disclaimer">
              Demonstration records only. Selecting a doctor does not
              submit or confirm an appointment request.
            </p>
          </section>
        )}

        {!isUser && appointmentSlots.length > 0 && (
          <section
            className="chat-slot-results"
            aria-label="Available appointment times"
          >
            <div className="chat-doctor-results-heading">
              <div>
                <strong>Available appointment times</strong>
                <span>
                  {appointmentSlots.length} demonstration{" "}
                  {appointmentSlots.length === 1 ? "time" : "times"} across{" "}
                  {availableDates.length} available{" "}
                  {availableDates.length === 1 ? "date" : "dates"}
                </span>
              </div>
              <span className="chat-doctor-demo-label">
                DEMO AVAILABILITY
              </span>
            </div>

            <div className="chat-slot-doctor-summary">
              <strong>{appointmentSlots[0].doctorName}</strong>
              <span>{appointmentSlots[0].department}</span>
              <span>
                {appointmentSlots[0].location || "Location not specified"}
              </span>
            </div>

            <div className="chat-slot-date-picker">
              <label
                className="chat-slot-date-heading"
                htmlFor={`appointment-date-${message.id}`}
              >
                <strong>Choose an available date</strong>
                <span>
                  {availableDates.length} available{" "}
                  {availableDates.length === 1 ? "date" : "dates"}
                </span>
              </label>

              <input
                id={`appointment-date-${message.id}`}
                className="chat-slot-native-date"
                type="date"
                value={selectedDate}
                min={availableDates[0]}
                max={availableDates[availableDates.length - 1]}
                onChange={(event) => setSelectedDate(event.target.value)}
                disabled={disabled}
                aria-label="Choose an available appointment date"
              />

              {selectedDateLabel && (
                <div className="chat-slot-selected-date">
                  <strong>{selectedDateLabel}</strong>
                  <span>
                    {selectedDateSlots.length} available{" "}
                    {selectedDateSlots.length === 1 ? "time" : "times"}
                  </span>
                </div>
              )}

              <strong className="chat-slot-available-times-heading">
                Available times
              </strong>
            </div>

            {selectedDateSlots.length > 0 ? (
              <div className="chat-slot-list">
                {selectedDateSlots.map(({ slot, index }) => (
                  <article
                    className="chat-slot-card"
                    key={`${slot.doctorId}-${slot.date}-${slot.time}`}
                  >
                    <div className="chat-slot-card-details">
                      <span className="chat-slot-time">{slot.time}</span>
                    </div>

                    <button
                      type="button"
                      className="chat-slot-select-button"
                      disabled={disabled || !onSlotSelect}
                      onClick={() => onSlotSelect?.(index)}
                    >
                      Select this time
                    </button>

                    <span className="chat-slot-number">
                      Option {index + 1}
                    </span>
                  </article>
                ))}
              </div>
            ) : (
              <p className="chat-slot-empty">
                No demonstration times are available on this date.
                Please choose another date.
              </p>
            )}

            <p className="chat-doctor-disclaimer">
              These are fictional demonstration times, not live hospital
              availability. Selecting a time only moves to the review step.
              It does not reserve a slot or submit an appointment request.
              You can also reply with an option number.
            </p>
          </section>
        )}

        <div className="message-footer">
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>

          {!isUser && content.trim() && speechAvailable && (
            <button
              type="button"
              className="message-speech-button"
              onClick={speaking ? stopSpeech : speakMessage}
              aria-label={
                speaking
                  ? language === "am"
                    ? "ንግግሩን አቁም"
                    : "Stop speaking"
                  : language === "am"
                    ? "ምላሹን ጮክ ብለው ያዳምጡ"
                    : "Read response aloud"
              }
              title={
                speaking
                  ? language === "am"
                    ? "ንግግሩን አቁም"
                    : "Stop speaking"
                  : language === "am"
                    ? "ምላሹን ጮክ ብለው ያዳምጡ"
                    : "Read response aloud"
              }
            >
              {speaking ? "■ Stop" : "▶ Listen"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
