
import { useEffect, useState } from "react";
import ChatHeader from "./ChatHeader";
import ChatInput from "./ChatInput";
import MessageBubble from "../Message/MessageBubble";
import { sendChatMessage } from "../../services/api";
import type {
  ChatMessage,
  ChatImage,
  Language,
  SummaryDetail,
} from "../../types/chat";

const translations = {
  en: {
    greeting:
      "Hello. I’m your hospital AI assistant. I can help explain information from your hospital record, such as laboratory results, medications, medical history, and treatment information.\n\nI can explain medical information in simpler language, but I cannot diagnose conditions or change your medications.",
    suggestionsTitle: "Try asking",
    suggestions: [
      "Explain my latest lab results",
      "Summarize my medical history",
      "Explain my medications",
      "What should I prepare for my next appointment?",
    ],
    assistantName: "Hospital AI Assistant",
    requestError:
      "I’m unable to process your request right now. Please try again in a moment.",
    imageReadError: "Could not read the selected image.",
    imageReadFailure: "Failed to read the selected image.",
    attachedImage: "Attached image",
  },
  am: {
    greeting:
      "ሰላም። እኔ የሆስፒታልዎ የAI ረዳት ነኝ። በሆስፒታልዎ መዝገብ ውስጥ ያሉ የላብራቶሪ ውጤቶችን፣ መድኃኒቶችን፣ የሕክምና ታሪክን እና የሕክምና መረጃዎችን እንዲረዱ ልረዳዎ እችላለሁ።\n\nየሕክምና መረጃን በቀላል ቋንቋ ማብራራት እችላለሁ፤ ሆኖም በሽታን መመርመር ወይም የመድኃኒት አጠቃቀምዎን መቀየር አልችልም።",
    suggestionsTitle: "ከእነዚህ ጥያቄዎች አንዱን ይሞክሩ",
    suggestions: [
      "የቅርብ ጊዜ የላብራቶሪ ውጤቶቼን ያብራሩልኝ",
      "የሕክምና ታሪኬን ያጠቃልሉልኝ",
      "መድኃኒቶቼን ያብራሩልኝ",
      "ለሚቀጥለው ቀጠሮዬ ምን ማዘጋጀት አለብኝ?",
    ],
    assistantName: "የሆስፒታል AI ረዳት",
    requestError:
      "ጥያቄዎን አሁን ማስኬድ አልቻልኩም። እባክዎ ከጥቂት ጊዜ በኋላ እንደገና ይሞክሩ።",
    imageReadError: "የመረጡትን ምስል ማንበብ አልተቻለም።",
    imageReadFailure: "ምስሉን ለማንበብ ስህተት ተፈጥሯል።",
    attachedImage: "የተያያዘ ምስል",
  },
} satisfies Record<
  Language,
  {
    greeting: string;
    suggestionsTitle: string;
    suggestions: string[];
    assistantName: string;
    requestError: string;
    imageReadError: string;
    imageReadFailure: string;
    attachedImage: string;
  }
>;

const createConversationId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
};

const createMessage = (
  role: ChatMessage["role"],
  content: string,
  attachment?: ChatImage
): ChatMessage => ({
  id: createConversationId(),
  role,
  content,
  timestamp: new Date().toISOString(),
  attachment,
});

const fileToDataUrl = (
  file: File,
  language: Language
): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
      } else {
        reject(
          new Error(translations[language].imageReadError)
        );
      }
    };

    reader.onerror = () =>
      reject(
        new Error(translations[language].imageReadFailure)
      );

    reader.readAsDataURL(file);
  });

export default function ChatWindow() {
  const [language, setLanguage] = useState<Language>("en");
  const [detail, setDetail] = useState<SummaryDetail>("normal");
  const [conversationId] = useState(createConversationId);

  const [messages, setMessages] = useState<ChatMessage[]>([
    createMessage("assistant", translations.en.greeting),
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const t = translations[language];

  // Update the welcome message if the user switches languages
  // before starting a conversation.
  useEffect(() => {
    setMessages((currentMessages) =>
      currentMessages.length === 1 &&
      currentMessages[0].role === "assistant"
        ? [createMessage("assistant", t.greeting)]
        : currentMessages
    );
  }, [language]);

  const handleSend = async (content: string, file?: File) => {
    if (loading) return;

    setError("");
    setLoading(true);

    // Capture the selected language for this request.
    const requestLanguage = language;
    const requestTranslations = translations[requestLanguage];

    try {
      let attachment: ChatImage | undefined;

      if (file) {
        attachment = {
          fileName: file.name,
          mimeType: file.type,
          dataUrl: await fileToDataUrl(file, requestLanguage),
        };
      }

      const userMessage = createMessage(
        "user",
        content,
        attachment
      );

      setMessages((currentMessages) => [
        ...currentMessages,
        userMessage,
      ]);

      const response = await sendChatMessage({
        message: content,
        conversationId,
        language: requestLanguage,
        detail,
        image: attachment,
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
    } catch {
      setError(requestTranslations.requestError);

      setMessages((currentMessages) => [
        ...currentMessages,
        createMessage(
          "assistant",
          requestTranslations.requestError
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
              <div key={message.id}>
                <MessageBubble message={message} />

                {message.role === "user" &&
                  message.attachment && (
                    <div
                      style={{
                        margin: "8px 0 16px 44px",
                      }}
                    >
                      <img
                        src={message.attachment.dataUrl}
                        alt={`${t.attachedImage}: ${message.attachment.fileName}`}
                        style={{
                          display: "block",
                          maxWidth: "min(280px, 100%)",
                          maxHeight: "260px",
                          objectFit: "contain",
                          borderRadius: "10px",
                          border: "1px solid #d8dee8",
                        }}
                      />
                      <p className="input-hint">
                        {message.attachment.fileName}
                      </p>
                    </div>
                  )}
              </div>
            ))}

            {loading && (
              <div className="message-row message-row-assistant">
                <div className="message-bubble message-assistant">
                  <div className="message-role">
                    {t.assistantName}
                  </div>

                  <div
                    className="typing-indicator"
                    aria-label={
                      language === "am"
                        ? "በማስኬድ ላይ"
                        : "Processing"
                    }
                  >
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="error-message" role="alert">
                {error}
              </div>
            )}
          </div>

          <div className="suggestions">
            <div className="suggestions-title">
              {t.suggestionsTitle}
            </div>

            <div className="suggestion-list">
              {t.suggestions.map((suggestion) => (
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
          language={language}
        />
      </section>
    </main>
  );
}