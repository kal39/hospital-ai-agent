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

  return (
    <div className="hospital-app sage-sidebar-layout">
      <aside className="sage-sidebar">
        <button
          type="button"
          className="sage-sidebar-brand"
          onClick={() => setActivePage("assistant")}
          aria-label={amharic ? "á‹ˆá‹° AI áˆ¨á‹³á‰µ á‹­áˆ˜áˆˆáˆ±" : "Go to AI Assistant"}
        >
          <span className="sage-sidebar-logo" aria-hidden="true">+</span>
          <span className="sage-sidebar-brand-copy">
            <strong>Hospital</strong>
            <span>{amharic ? "á‹¨á‰³áŠ«áˆš áŠ áŒˆáˆáŒáˆŽá‰µ" : "Patient Services"}</span>
          </span>
        </button>

        <div className="sage-sidebar-section-label">
          {amharic ? "á‹¨á‰³áŠ«áˆš áŠ áŒˆáˆáŒáˆŽá‰¶á‰½" : "PATIENT SERVICES"}
        </div>

        <nav className="sage-sidebar-nav" aria-label="Patient services">
          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "assistant" ? "is-active" : ""}`}
            onClick={() => setActivePage("assistant")}
            aria-current={activePage === "assistant" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">âœ§</span>
            <span>{amharic ? "AI áˆ¨á‹³á‰µ" : "AI Assistant"}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">â€º</span>
          </button>

          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "booking" ? "is-active" : ""}`}
            onClick={() => setActivePage("booking")}
            aria-current={activePage === "booking" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">â–¦</span>
            <span>{amharic ? "á‰€áŒ áˆ® á‹­á‹«á‹™" : "Book Appointment"}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">â€º</span>
          </button>
        </nav>

          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "staff" ? "is-active" : ""}`}
            onClick={() => setActivePage("staff")}
            aria-current={activePage === "staff" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">✓</span>
            <span>Staff Review</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>
        <div className="sage-sidebar-preferences">
          <div className="sage-sidebar-section-label">
            {amharic ? "áˆáˆ­áŒ«á‹Žá‰½" : "PREFERENCES"}
          </div>

          <label className="sage-preference-field">
            <span className="sage-preference-label">
              <span aria-hidden="true">æ–‡</span>
              {amharic ? "á‰‹áŠ•á‰‹ / Language" : "Language / á‰‹áŠ•á‰‹"}
            </span>
            <select
              value={language}
              onChange={(event) => updateLanguage(event.target.value as Language)}
              aria-label="Language / á‰‹áŠ•á‰‹"
            >
              <option value="en">English</option>
              <option value="am">áŠ áˆ›áˆ­áŠ› (Amharic)</option>
            </select>
          </label>

          <label className="sage-preference-field">
            <span className="sage-preference-label">
              <span aria-hidden="true">â˜·</span>
              {amharic ? "á‹¨áˆáˆ‹áˆ½ á‹áˆ­á‹áˆ­" : "Response detail"}
            </span>
            <select
              value={detail}
              onChange={(event) =>
                updateDetail(event.target.value as SummaryDetail)
              }
              aria-label={amharic ? "á‹¨áˆáˆ‹áˆ½ á‹áˆ­á‹áˆ­" : "Response detail"}
            >
              <option value="short">{amharic ? "áŠ áŒ­áˆ­" : "Short"}</option>
              <option value="normal">{amharic ? "áˆ˜á‹°á‰ áŠ›" : "Normal"}</option>
              <option value="detailed">{amharic ? "á‹áˆ­á‹áˆ­" : "Detailed"}</option>
            </select>
          </label>
          <p className="sage-preference-note">
            {amharic
              ? "áˆáˆ­áŒ«á‹Žá‰½á‹Ž á‰ áˆáˆˆá‰±áˆ áŒˆáŒ¾á‰½ áˆ‹á‹­ á‹­á‰†á‹«áˆ‰á¢"
              : "Your preferences are shared across both sections."}
          </p>
        </div>

        <div className="sage-sidebar-spacer" />

        <section className="sage-sidebar-help">
          <span className="sage-help-icon" aria-hidden="true">+</span>
          <strong>{amharic ? "áˆˆáŒ¤áŠ“á‹Ž áŠ¥á‹šáˆ… áŠáŠ•" : "Here for your health"}</strong>
          <p>
            {amharic
              ? "á‹¨áˆ•áŠ­áˆáŠ“ áˆ˜áˆ¨áŒƒá‹ŽáŠ• áˆˆáˆ˜áˆ¨á‹³á‰µ áŠ¥áŠ“ á‰€áŒ áˆ® áˆˆáˆ›áŒáŠ˜á‰µ áŠ¥áŠ•áˆ¨á‹³á‹Žá‰³áˆˆáŠ•á¢"
              : "Get help understanding your information and finding an appointment."}
          </p>
        </section>

        <div className="sage-sidebar-demo">
          <span className="sage-demo-indicator" />
          <span>
            <strong>{amharic ? "á‹¨áˆ™áŠ¨áˆ« áŠ áŠ«á‰£á‰¢" : "Demo environment"}</strong>
            <small>
              {amharic ? "áŠ¨á‰€áŒ¥á‰³ áˆ¥áˆ­á‹“á‰¶á‰½ áŒ‹áˆ­ áŠ áˆá‰°áŒˆáŠ“áŠ˜áˆ" : "Not connected to live systems"}
            </small>
          </span>
        </div>
      </aside>

      <div className="sage-main">
        <header className="sage-topbar">
          <div className="sage-breadcrumb">
            <span>{amharic ? "á‹¨á‰³áŠ«áˆš áŠ áŒˆáˆáŒáˆŽá‰µ" : "Patient Services"}</span>
            <span aria-hidden="true">/</span>
            <strong>
              {activePage === "assistant"
                ? (amharic ? "AI áˆ¨á‹³á‰µ" : "AI Assistant")
                : activePage === "booking"
                  ? (amharic ? "á‰€áŒ áˆ® á‹­á‹«á‹™" : "Book Appointment")
                  : "Staff Review"}
            </strong>
          </div>
          <span className="sage-topbar-status">
            <span className="sage-demo-indicator" />
            {amharic ? "á‹¨áˆ™áŠ¨áˆ« áˆáŠ”á‰³" : "Demo mode"}
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
          <span>{amharic ? "á‹¨á‰³áŠ«áˆš áŠ áŒˆáˆáŒáˆŽá‰µ" : "Patient Services"}</span>
          <span>
            {amharic
              ? "á‹¨áˆ™áŠ¨áˆ« áŠ áŠ«á‰£á‰¢ Â· áŠ¨á‰€áŒ¥á‰³ á‹¨áˆ†áˆµá’á‰³áˆ áˆ¥áˆ­á‹“á‰¶á‰½ áŒ‹áˆ­ áŠ áˆá‰°áŒˆáŠ“áŠ˜áˆ"
              : "Demonstration environment Â· Not connected to live hospital systems"}
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;


