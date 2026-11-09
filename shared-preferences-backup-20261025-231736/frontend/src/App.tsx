import { useState } from "react";

import AppointmentBooking from "./components/AppointmentBooking/AppointmentBooking";
import ChatWindow from "./components/Chat/ChatWindow";

type ActivePage = "assistant" | "booking";

function App() {
  const [activePage, setActivePage] = useState<ActivePage>("assistant");

  return (
    <div className="hospital-app sage-sidebar-layout">
      <aside className="sage-sidebar">
        <button
          type="button"
          className="sage-sidebar-brand"
          onClick={() => setActivePage("assistant")}
          aria-label="Go to AI Assistant"
        >
          <span className="sage-sidebar-logo" aria-hidden="true">+</span>
          <span className="sage-sidebar-brand-copy">
            <strong>Hospital</strong>
            <span>Patient Services</span>
          </span>
        </button>

        <div className="sage-sidebar-section-label">PATIENT SERVICES</div>

        <nav className="sage-sidebar-nav" aria-label="Patient services">
          <button
            type="button"
            className={`sage-sidebar-link ${
              activePage === "assistant" ? "is-active" : ""
            }`}
            onClick={() => setActivePage("assistant")}
            aria-current={activePage === "assistant" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">✧</span>
            <span>AI Assistant</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>

          <button
            type="button"
            className={`sage-sidebar-link ${
              activePage === "booking" ? "is-active" : ""
            }`}
            onClick={() => setActivePage("booking")}
            aria-current={activePage === "booking" ? "page" : undefined}
          >
            <span className="sage-sidebar-icon" aria-hidden="true">▦</span>
            <span>Book Appointment</span>
            <span className="sage-sidebar-link-arrow" aria-hidden="true">›</span>
          </button>
        </nav>

        <div className="sage-sidebar-spacer" />

        <section className="sage-sidebar-help">
          <span className="sage-help-icon" aria-hidden="true">+</span>
          <strong>Here for your health</strong>
          <p>Get help understanding your information and finding an appointment.</p>
        </section>

        <div className="sage-sidebar-demo">
          <span className="sage-demo-indicator" />
          <span>
            <strong>Demo environment</strong>
            <small>Not connected to live systems</small>
          </span>
        </div>
      </aside>

      <div className="sage-main">
        <header className="sage-topbar">
          <div className="sage-breadcrumb">
            <span>Patient Services</span>
            <span aria-hidden="true">/</span>
            <strong>
              {activePage === "assistant" ? "AI Assistant" : "Book Appointment"}
            </strong>
          </div>
          <span className="sage-topbar-status">
            <span className="sage-demo-indicator" />
            Demo mode
          </span>
        </header>

        <main className="hospital-app-content sage-main-content">
          {activePage === "assistant" ? (
            <ChatWindow />
          ) : (
            <AppointmentBooking />
          )}
        </main>

        <footer className="hospital-app-footer sage-main-footer">
          <span>Patient Services</span>
          <span>
            Demonstration environment · Not connected to live hospital systems
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;
