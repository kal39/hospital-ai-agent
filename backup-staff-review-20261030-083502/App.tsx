import { useState } from "react";

import AppointmentBooking from "./components/AppointmentBooking/AppointmentBooking";
import StaffReview from "./components/StaffReview/StaffReview";
import ChatWindow from "./components/Chat/ChatWindow";
import type { Language, SummaryDetail } from "./types/chat";

type ActivePage = "assistant" | "booking" | "staff";

function readPreference<T extends string>(
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  try {
    const stored = localStorage.getItem(key);
    return allowed.includes(stored as T) ? (stored as T) : fallback;
  } catch {
    return fallback;
  }
}

function App() {
  const [activePage, setActivePage] = useState<ActivePage>("assistant");

  const [language, setLanguage] = useState<Language>(() =>
    readPreference("hospital-ui-language", ["en", "am"] as const, "en"),
  );

  const [detail, setDetail] = useState<SummaryDetail>(() =>
    readPreference(
      "hospital-ai-response-detail",
      ["short", "normal", "detailed"] as const,
      "normal",
    ),
  );

  function updateLanguage(next: Language) {
    setLanguage(next);
    try {
      localStorage.setItem("hospital-ui-language", next);
    } catch {
      // The preference still works for this session if storage is unavailable.
    }
  }

  function updateDetail(next: SummaryDetail) {
    setDetail(next);
    try {
      localStorage.setItem("hospital-ai-response-detail", next);
    } catch {
      // The preference still works for this session if storage is unavailable.
    }
  }

  const amharic = language === "am";

  const pageLabels: Record<ActivePage, string> = {
    assistant: amharic ? "AI ረዳት" : "AI Assistant",
    booking: amharic ? "ቀጠሮ ይያዙ" : "Book Appointment",
    staff: amharic ? "የሰራተኞች ግምገማ" : "Staff Review",
  };

  return (
    <div className="hospital-app sage-sidebar-layout">
      <aside className="sage-sidebar">
        <button
          type="button"
          className="sage-sidebar-brand"
          onClick={() => setActivePage("assistant")}
          aria-label={amharic ? "ወደ AI ረዳት ይመለሱ" : "Go to AI Assistant"}
        >
          <span className="sage-sidebar-logo" aria-hidden="true">+</span>
          <span className="sage-sidebar-brand-copy">
            <strong>Hospital</strong>
            <span>{amharic ? "የታካሚ አገልግሎቶች" : "Patient Services"}</span>
          </span>
        </button>

        <div className="sage-sidebar-section-label">
          {amharic ? "የታካሚ አገልግሎቶች" : "PATIENT SERVICES"}
        </div>

        <nav className="sage-sidebar-nav" aria-label="Patient services">
          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "assistant" ? "is-active" : ""}`}
            onClick={() => setActivePage("assistant")}
            aria-current={activePage === "assistant" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">✧</span>
            <span>{pageLabels.assistant}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>

          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "booking" ? "is-active" : ""}`}
            onClick={() => setActivePage("booking")}
            aria-current={activePage === "booking" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">▦</span>
            <span>{pageLabels.booking}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>

          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "staff" ? "is-active" : ""}`}
            onClick={() => setActivePage("staff")}
            aria-current={activePage === "staff" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">✓</span>
            <span>{pageLabels.staff}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>
        </nav>

        <div className="sage-sidebar-preferences">
          <div className="sage-sidebar-section-label">
            {amharic ? "ቅንብሮች" : "PREFERENCES"}
          </div>

          <label className="sage-preference-field">
            <span className="sage-preference-label">
              <span aria-hidden="true">文</span>
              {amharic ? "ቋንቋ / Language" : "Language / ቋንቋ"}
            </span>
            <select
              value={language}
              onChange={(event) => updateLanguage(event.target.value as Language)}
              aria-label={amharic ? "ቋንቋ" : "Language"}
            >
              <option value="en">English</option>
              <option value="am">አማርኛ (Amharic)</option>
            </select>
          </label>

          <label className="sage-preference-field">
            <span className="sage-preference-label">
              <span aria-hidden="true">☷</span>
              {amharic ? "የምላሽ ዝርዝር" : "Response detail"}
            </span>
            <select
              value={detail}
              onChange={(event) =>
                updateDetail(event.target.value as SummaryDetail)
              }
              aria-label={amharic ? "የምላሽ ዝርዝር" : "Response detail"}
            >
              <option value="short">{amharic ? "አጭር" : "Short"}</option>
              <option value="normal">{amharic ? "መደበኛ" : "Normal"}</option>
              <option value="detailed">{amharic ? "ዝርዝር" : "Detailed"}</option>
            </select>
          </label>

          <p className="sage-preference-note">
            {amharic
              ? "ምርጫዎችዎ በሁለቱም ክፍሎች ይተገበራሉ።"
              : "Your preferences are shared across both sections."}
          </p>
        </div>

        <div className="sage-sidebar-spacer" />

        <section className="sage-sidebar-help">
          <span className="sage-help-icon" aria-hidden="true">+</span>
          <strong>
            {amharic ? "ለጤናዎ እዚህ ነን" : "Here for your health"}
          </strong>
          <p>
            {amharic
              ? "የጤና መረጃዎን ለመረዳት እና ቀጠሮ ለማግኘት እንረዳዎታለን።"
              : "Get help understanding your information and finding an appointment."}
          </p>
        </section>

        <div className="sage-sidebar-demo">
          <span className="sage-demo-indicator" />
          <span>
            <strong>
              {amharic ? "የሙከራ አካባቢ" : "Demo environment"}
            </strong>
            <small>
              {amharic
                ? "ከቀጥታ የሆስፒታል ሥርዓቶች ጋር አልተገናኘም"
                : "Not connected to live systems"}
            </small>
          </span>
        </div>
      </aside>

      <div className="sage-main">
        <header className="sage-topbar">
          <div className="sage-breadcrumb">
            <span>
              {amharic ? "የታካሚ አገልግሎቶች" : "Patient Services"}
            </span>
            <span aria-hidden="true">/</span>
            <strong>{pageLabels[activePage]}</strong>
          </div>
          <span className="sage-topbar-status">
            <span className="sage-demo-indicator" />
            {amharic ? "የሙከራ ሁኔታ" : "Demo mode"}
          </span>
        </header>

        <main className="hospital-app-content sage-main-content">
          {activePage === "assistant" ? (
            <ChatWindow language={language} detail={detail} />
          ) : activePage === "booking" ? (
            <AppointmentBooking language={language} />
          ) : (
            <StaffReview />
          )}
        </main>

        <footer className="hospital-app-footer sage-main-footer">
          <span>
            {amharic ? "የታካሚ አገልግሎቶች" : "Patient Services"}
          </span>
          <span>
            {amharic
              ? "የሙከራ አካባቢ · ከቀጥታ የሆስፒታል ሥርዓቶች ጋር አልተገናኘም"
              : "Demonstration environment · Not connected to live hospital systems"}
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;