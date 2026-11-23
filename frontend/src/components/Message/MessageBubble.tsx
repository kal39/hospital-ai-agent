import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import type { ChatMessage, Language } from "../../types/chat";
import DoctorAvatar from "../Doctor/DoctorAvatar";

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

function toTelephoneHref(phone: string): string {
  return `tel:${phone.replace(/[^\\d+]/g, "")}`;
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
              <strong>Possible emergency ? get help now</strong>
              <span>IMMEDIATE ACTION</span>
            </div>

            <p>
              Go to the nearest emergency department or contact local
              emergency services. Do not wait for this assistant.
            </p>

            <div className="chat-emergency-contact-details">
              {emergency.hospitalName && (
                <div className="chat-emergency-contact-row">
                  <span>Hospital</span>
                  <strong>{emergency.hospitalName}</strong>
                </div>
              )}

              {emergency.hospitalEmergencyPhone && (
                <div className="chat-emergency-contact-row">
                  <span>Hospital emergency</span>
                  <a href={toTelephoneHref(emergency.hospitalEmergencyPhone)}>
                    {emergency.hospitalEmergencyPhone}
                  </a>
                </div>
              )}

              {emergency.ambulanceDispatchPhone && (
                <div className="chat-emergency-contact-row">
                  <span>Ambulance</span>
                  <a href={toTelephoneHref(emergency.ambulanceDispatchPhone)}>
                    {emergency.ambulanceDispatchPhone}
                  </a>
                </div>
              )}

              {emergency.alternativeEmergencyPhone && (
                <div className="chat-emergency-contact-row">
                  <span>Alternative contact</span>
                  <a href={toTelephoneHref(emergency.alternativeEmergencyPhone)}>
                    {emergency.alternativeEmergencyPhone}
                  </a>
                </div>
              )}
            </div>

            <p className="chat-emergency-demo-notice">
              Demo only: verify contacts before use. Phone links do not
              dispatch an ambulance or notify hospital staff.
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
            aria-label="Emergency concern registration"
          >
            <div className="chat-care-case-heading">
              <div>
                <strong>Emergency concern registered</strong>
                <span className="chat-care-case-status">
                  Registration status: {careCase.status}
                </span>
              </div>
              <span className="chat-care-case-demo-label">
                SYNTHETIC DEMO
              </span>
            </div>

            <div className="chat-care-case-reference">
              <span>Demonstration case reference</span>
              <strong>{careCase.caseId}</strong>
            </div>

            <div className="chat-care-case-details">
              <div>
                <span>Reported concern</span>
                <p>{careCase.reportedConcern}</p>
              </div>
              <div>
                <span>Registered</span>
                <time dateTime={careCase.createdAt}>
                  {Number.isNaN(Date.parse(careCase.createdAt))
                    ? careCase.createdAt
                    : new Date(careCase.createdAt).toLocaleString()}
                </time>
              </div>
            </div>

            <p className="chat-care-case-data-notice">
              {careCase.dataNotice}
            </p>

            <div className="chat-care-case-safety-notice" role="note">
              <strong>Important: this is not a real hospital notification.</strong>
              <p>
                This record is stored only in this demonstration. It has not
                been sent to hospital staff, has not been acknowledged by
                staff, and has not been clinically triaged. This is not an
                emergency response service. If this is an emergency, contact
                local emergency services or go to the nearest emergency
                department.
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
