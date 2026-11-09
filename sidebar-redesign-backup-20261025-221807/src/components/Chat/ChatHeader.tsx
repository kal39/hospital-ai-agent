
import type { Language, SummaryDetail } from "../../types/chat";

interface ChatHeaderProps {
  language: Language;
  detail: SummaryDetail;
  onLanguageChange: (language: Language) => void;
  onDetailChange: (detail: SummaryDetail) => void;
}

const labels = {
  en: {
    title: "Hospital AI Assistant",
    status: "Ready to help",
    language: "Language",
    detail: "Response detail",
    short: "Short",
    normal: "Normal",
    detailed: "Detailed",
  },
  am: {
    title: "የሆስፒታል AI ረዳት",
    status: "ለመርዳት ዝግጁ ነኝ",
    language: "ቋንቋ",
    detail: "የምላሽ ዝርዝር ደረጃ",
    short: "አጭር",
    normal: "መደበኛ",
    detailed: "ዝርዝር",
  },
} satisfies Record<Language, Record<string, string>>;

export default function ChatHeader({
  language,
  detail,
  onLanguageChange,
  onDetailChange,
}: ChatHeaderProps) {
  const t = labels[language];

  return (
    <header className="chat-header">
      <div className="assistant-identity">
        <div className="assistant-icon">AI</div>

        <div>
          <h1>{t.title}</h1>
          <div className="assistant-status">
            <span className="status-dot" />
            {t.status}
          </div>
        </div>
      </div>

      <div className="chat-controls">
        <label>
          <span>{t.language}</span>
          <select
            value={language}
            onChange={(event) =>
              onLanguageChange(event.target.value as Language)
            }
            aria-label={t.language}
          >
            <option value="en">English</option>
            <option value="am">አማርኛ</option>
          </select>
        </label>

        <label>
          <span>{t.detail}</span>
          <select
            value={detail}
            onChange={(event) =>
              onDetailChange(event.target.value as SummaryDetail)
            }
            aria-label={t.detail}
          >
            <option value="short">{t.short}</option>
            <option value="normal">{t.normal}</option>
            <option value="detailed">{t.detailed}</option>
          </select>
        </label>
      </div>
    </header>
  );
}