import { useState } from "react";

import AppointmentBooking from "./components/AppointmentBooking/AppointmentBooking";
import ChatWindow from "./components/Chat/ChatWindow";

type ActivePage = "assistant" | "booking";

function App() {
  const [activePage, setActivePage] = useState<ActivePage>("assistant");

  return (
    <div className="hospital-app">
      <header className="hospital-app-nav">
        <a
          href="#home"
          className="hospital-brand"
          onClick={(event) => {
            event.preventDefault();
            setActivePage("assistant");
          }}
        >
          <span className="hospital-brand-mark" aria-hidden="true">
            +
          </span>
          <span className="hospital-brand-text">
            <strong>Hospital</strong>
            <span>Patient Services</span>
          </span>
        </a>

        <nav className="hospital-nav-links" aria-label="Patient services">
          <button
            type="button"
            className={`hospital-nav-button ${
              activePage === "assistant" ? "is-active" : ""
            }`}
            onClick={() => setActivePage("assistant")}
            aria-current={activePage === "assistant" ? "page" : undefined}
          >
            <span aria-hidden="true">✧</span>
            AI Assistant
          </button>

          <button
            type="button"
            className={`hospital-nav-button ${
              activePage === "booking" ? "is-active" : ""
            }`}
            onClick={() => setActivePage("booking")}
            aria-current={activePage === "booking" ? "page" : undefined}
          >
            <span aria-hidden="true">▦</span>
            Book Appointment
          </button>
        </nav>

        <span className="hospital-demo-pill">
          <span className="hospital-demo-dot" />
          Demo environment
        </span>
      </header>

      <div className="hospital-app-content">
        {activePage === "assistant" ? (
          <ChatWindow />
        ) : (
          <AppointmentBooking />
        )}
      </div>

      <footer className="hospital-app-footer">
        <span>Patient Services</span>
        <span>
          Demonstration environment · Not connected to live hospital systems
        </span>
      </footer>
    </div>
  );
}

export default App;
