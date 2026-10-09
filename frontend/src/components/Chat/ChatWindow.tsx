import { useState } from "react";
import ChatHeader from "./ChatHeader";
import ChatInput from "./ChatInput";
import MessageBubble from "../Message/MessageBubble";
import { sendChatMessage } from "../../services/api";
import type {
  ChatMessage,
  Language,
  SummaryDetail,
} from "../../types/chat";

const suggestions = [
  "Explain my latest lab results",
  "Summarize my medical history",
  "Explain my medications",
  "What should I prepare for my next appointment?",
];

const createConversationId = () => {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
};

const createMessage = (
  role: ChatMessage["role"],
  content: string
): ChatMessage => ({
  id: createConversationId(),
  role,
  content,
  timestamp: new Date().toISOString(),
});

export default function ChatWindow() {
  const [language, setLanguage] = useState<Language>("en");
  const [detail, setDetail] = useState<SummaryDetail>("normal");

  const [conversationId] = useState(createConversationId);

  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage(
      "assistant",
      "Hello. I’m your hospital AI assistant. I can help explain information from your hospital record, such as laboratory results, medications, medical history, and treatment information.\n\nI can explain medical information in simpler language, but I cannot diagnose conditions or change your medications."
    ),
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (content: string) => {
    if (loading) {
      return;
    }

    setError("");

    const userMessage = createMessage("user", content);

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setLoading(true);

    try {
      const response = await sendChatMessage({
        message: content,
        conversationId,
        language,
        detail,
      });

      const assistantMessage: ChatMessage = {
        id: createConversationId(),
        role: "assistant",
        content: response.message,
        timestamp: new Date().toISOString(),
        safety: response.safety
          ? {
              requiresAttention:
                response.safety.requiresAttention,
            }
          : undefined,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting the assistant.";

      setError(errorMessage);

      setMessages((currentMessages) => [
        ...currentMessages,
        createMessage(
          "assistant",
          "I’m unable to connect to the hospital AI service right now. Please try again in a moment."
        ),
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="chat-page">
      <section className="chat-container">
        <ChatHeader
          language={language}
          detail={detail}
          onLanguageChange={setLanguage}
          onDetailChange={setDetail}
        />

        <div className="chat-body">
          <div className="conversation">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
              />
            ))}

            {loading && (
              <div className="message-row message-row-assistant">
                <div className="message-bubble message-assistant">
                  <div className="message-role">
                    Hospital AI Assistant
                  </div>

                  <div className="typing-indicator">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>

          <div className="suggestions">
            <div className="suggestions-title">
              Try asking
            </div>

            <div className="suggestion-list">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleSend(suggestion)}
                  disabled={loading}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>

        <ChatInput
          onSend={handleSend}
          disabled={loading}
        />
      </section>
    </main>
  );
}