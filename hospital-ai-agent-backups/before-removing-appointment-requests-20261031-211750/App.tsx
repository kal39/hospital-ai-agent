import { useEffect, useState } from "react";

import AppointmentBooking from "./components/AppointmentBooking/AppointmentBooking";
import StaffReview from "./components/StaffReview/StaffReview";
import ChatWindow from "./components/Chat/ChatWindow";
import type { Language, SummaryDetail } from "./types/chat";

type ActivePage = "assistant" | "booking" | "staff";

function getPageFromPath(pathname: string): ActivePage {
  switch (pathname.replace(/\/+$/, "") || "/") {
    case "/staff/appointments":
      return "staff";

    case "/patient/appointments":
      return "booking";

    case "/":
      return "assistant";

    default:
      return "assistant";
  }
}

function getPathForPage(page: ActivePage): string {
  switch (page) {
    case "staff":
      return "/staff/appointments";

    case "booking":
      return "/patient/appointments";

    default:
      return "/";
  }
}

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
  const [activePage, setActivePage] = useState<ActivePage>(() =>
    getPageFromPath(window.location.pathname),
  );

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

  useEffect(() => {
    function handlePopState() {
      setActivePage(getPageFromPath(window.location.pathname));
    }

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  function navigateToPage(page: ActivePage) {
    const nextPath = getPathForPage(page);

    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }

    setActivePage(page);
  }

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
    booking: amharic ? "የቀጠሮ አስተዳደር" : "Appointment Management",
    staff: amharic ? "የሰራተኞች የስራ ቦታ" : "Staff Review",
  };

  // Staff Review has its own independent workspace.
  if (activePage === "staff") {
    return (
      <div className="hospital-app">
        <div className="sage-main">
          <header className="sage-topbar">
            <div className="sage-breadcrumb">
              <strong>
                {amharic ? "የሰራተኞች የስራ ቦታ" : "Staff Workspace"}
              </strong>
              <span aria-hidden="true">/</span>
              <span>{pageLabels.staff}</span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
              }}
            >
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span>{amharic ? "ቋንቋ" : "Language"}</span>
                <select
                  value={language}
                  onChange={(event) =>
                    updateLanguage(event.target.value as Language)
                  }
                  aria-label={amharic ? "ቋንቋ" : "Language"}
                >
                  <option value="en">English</option>
                  <option value="am">አማርኛ</option>
                </select>
              </label>

              <span className="sage-topbar-status">
                <span className="sage-demo-indicator" />
                {amharic ? "የሙከራ ሁኔታ" : "Demo mode"}
              </span>
            </div>
          </header>

          <main className="hospital-app-content sage-main-content">
            <StaffReview language={language} />
          </main>

          <footer className="hospital-app-footer sage-main-footer">
            <button
              type="button"
              onClick={() => navigateToPage("assistant")}
              style={{
                border: "none",
                background: "transparent",
                color: "inherit",
                cursor: "pointer",
                font: "inherit",
              }}
            >
              {amharic
                ? "← ወደ ታካሚ አገልግሎቶች ተመለስ"
                : "← Back to Patient Services"}
            </button>

            <span>
              {amharic
                ? "የሙከራ አካባቢ · ከቀጥታ የሆስፒታል ስርዓቶች ጋር አልተገናኘም"
                : "Demonstration environment · Not connected to live hospital systems"}
            </span>
          </footer>
        </div>
      </div>
    );
  }

  // Patient Services workspace.
  return (
    <div className="hospital-app sage-sidebar-layout">
      <aside className="sage-sidebar">
        <button
          type="button"
          className="sage-sidebar-brand"
          onClick={() => navigateToPage("assistant")}
          aria-label={amharic ? "ወደ AI ረዳት ይመለሱ" : "Go to AI Assistant"}
        >
          <span className="sage-sidebar-logo" aria-hidden="true">+</span>
          <span className="sage-sidebar-brand-copy">
            <strong>Hospital</strong>
            <span>
              {amharic ? "የታካሚ አገልግሎቶች" : "Patient Services"}
            </span>
          </span>
        </button>

        <div className="sage-sidebar-section-label">
          {amharic ? "የታካሚ አገልግሎቶች" : "PATIENT SERVICES"}
        </div>

        <nav className="sage-sidebar-nav" aria-label="Patient services">
          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "assistant" ? "is-active" : ""}`}
            onClick={() => navigateToPage("assistant")}
            aria-current={activePage === "assistant" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">✧</span>
            <span>{pageLabels.assistant}</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>

          <button
            type="button"
            className={`sage-sidebar-link ${activePage === "booking" ? "is-active" : ""}`}
            onClick={() => navigateToPage("booking")}
            aria-current={activePage === "booking" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">▦</span>
            <span>{pageLabels.booking}</span>
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
              {amharic ? "ቋንቋ / Language" : "Language"}
            </span>
            <select
              value={language}
              onChange={(event) =>
                updateLanguage(event.target.value as Language)
              }
              aria-label={amharic ? "ቋንቋ" : "Language"}
            >
              <option value="en">English</option>
              <option value="am">አማርኛ (Amharic)</option>
            </select>
          </label>

          <label className="sage-preference-field">
            <span className="sage-preference-label">
              <span aria-hidden="true">☷</span>
              {amharic ? "የመልስ ዝርዝር ደረጃ" : "Response detail"}
            </span>
            <select
              value={detail}
              onChange={(event) =>
                updateDetail(event.target.value as SummaryDetail)
              }
              aria-label={amharic ? "የመልስ ዝርዝር ደረጃ" : "Response detail"}
            >
              <option value="short">{amharic ? "አጭር" : "Short"}</option>
              <option value="normal">{amharic ? "መደበኛ" : "Normal"}</option>
              <option value="detailed">{amharic ? "ዝርዝር" : "Detailed"}</option>
            </select>
          </label>

          <p className="sage-preference-note">
            {amharic
              ? "የመረጡት ቅንብሮች በሁለቱም ክፍሎች ላይ ይሠራሉ።"
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
                ? "ከቀጥታ የሆስፒታል ስርዓቶች ጋር አልተገናኘም"
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
          ) : (
            <AppointmentBooking language={language} />
          )}
        </main>

        <footer className="hospital-app-footer sage-main-footer">
          <span>
            {amharic ? "የታካሚ አገልግሎቶች" : "Patient Services"}
          </span>
          <span>
            {amharic
              ? "የሙከራ አካባቢ · ከቀጥታ የሆስፒታል ስርዓቶች ጋር አልተገናኘም"
              : "Demonstration environment · Not connected to live hospital systems"}
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;
