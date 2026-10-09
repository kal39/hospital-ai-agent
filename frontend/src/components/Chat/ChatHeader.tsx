import type { Language, SummaryDetail } from "../../types/chat";

interface ChatHeaderProps {
  language: Language;
  detail: SummaryDetail;
  onLanguageChange: (language: Language) => void;
  onDetailChange: (detail: SummaryDetail) => void;
}

export default function ChatHeader({
  language,
  detail,
  onLanguageChange,
  onDetailChange,
}: ChatHeaderProps) {
  return (
    <header className="chat-header">
      <div className="assistant-identity">
        <div className="assistant-icon">AI</div>

        <div>
          <h1>Hospital AI Assistant</h1>
          <div className="assistant-status">
            <span className="status-dot" />
            Ready to help
          </div>
        </div>
      </div>

      <div className="chat-controls">
        <label>
          <span>Language</span>
          <select
            value={language}
            onChange={(event) =>
              onLanguageChange(event.target.value as Language)
            }
          >
            <option value="en">English</option>
            <option value="am">አማርኛ</option>
          </select>
        </label>

        <label>
          <span>Detail</span>
          <select
            value={detail}
            onChange={(event) =>
              onDetailChange(event.target.value as SummaryDetail)
            }
          >
            <option value="short">Short</option>
            <option value="normal">Normal</option>
            <option value="detailed">Detailed</option>
          </select>
        </label>
      </div>
    </header>
  );
}