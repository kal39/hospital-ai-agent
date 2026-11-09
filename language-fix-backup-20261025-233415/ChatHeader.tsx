import type { Language } from "../../types/chat";

interface ChatHeaderProps {
  language: Language;
}

const labels: Record<Language, { title: string; status: string }> = {
  en: {
    title: "Hospital AI Assistant",
    status: "Ready to help",
  },
  am: {
    title: "የሆስፒታል AI ረዳት",
    status: "ለመርዳት ዝግጁ ነኝ",
  },
};

export default function ChatHeader({ language }: ChatHeaderProps) {
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
    </header>
  );
}
