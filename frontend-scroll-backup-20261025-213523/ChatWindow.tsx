
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
    fileReadError: "Could not read the selected file.",
    fileReadFailure: "Failed to read the selected file.",
    attachedImage: "Attached image",
    attachedDocument: "Attached PDF document",
    unsupportedFileError:
      "Please select a JPG, PNG, WebP image, or PDF document.",
  },

  am: {
    greeting:
      "ሰላም! እኔ የሆስፒታል AI ረዳትዎ ነኝ። ከሆስፒታል መዝገብዎ የላቦራቶሪ ውጤቶችን፣ መድኃኒቶችን፣ የሕክምና ታሪክን እና የሕክምና መረጃዎችን እንዲረዱ እረዳዎታለሁ።\n\nመረጃውን በቀላል ቋንቋ ማብራራት እችላለሁ፣ ነገር ግን በሽታ መመርመር ወይም የመድኃኒት ሕክምናዎን መቀየር አልችልም።",
    suggestionsTitle: "እነዚህን መጠየቅ ይችላሉ",
    suggestions: [
      "የቅርብ ጊዜ የላቦራቶሪ ውጤቶቼን አብራራልኝ",
      "የሕክምና ታሪኬን አጠቃልልልኝ",
      "መድኃኒቶቼን አብራራልኝ",
      "ለሚቀጥለው ቀጠሮዬ ምን ማዘጋጀት አለብኝ?",
    ],
    assistantName: "የሆስፒታል AI ረዳት",
    requestError:
      "ጥያቄዎን በአሁኑ ጊዜ ማስኬድ አልተቻለም። እባክዎ ቆይተው እንደገና ይሞክሩ።",
    fileReadError: "የተመረጠውን ፋይል ማንበብ አልተቻለም።",
    fileReadFailure: "ፋይሉን በማንበብ ላይ ስህተት ተፈጥሯል።",
    attachedImage: "የተያያዘ ምስል",
    attachedDocument: "የተያያዘ PDF ሰነድ",
    unsupportedFileError:
      "እባክዎ JPG፣ PNG፣ WebP ምስል ወይም PDF ሰነድ ይምረጡ።",
  },

} satisfies Record<
  Language,
  {
    greeting: string;
    suggestionsTitle: string;
    suggestions: string[];
    assistantName: string;
    requestError: string;
    fileReadError: string;
    fileReadFailure: string;
    attachedImage: string;
    attachedDocument: string;
    unsupportedFileError: string;
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

const getSupportedMimeType = (
  file: File
): ChatImage["mimeType"] | undefined => {
  const extension = file.name.split(".").pop()?.toLowerCase();

  if (file.type === "image/jpeg" || extension === "jpg" || extension === "jpeg") {
    return "image/jpeg";
  }

  if (file.type === "image/png" || extension === "png") {
    return "image/png";
  }

  if (file.type === "image/webp" || extension === "webp") {
    return "image/webp";
  }

  if (file.type === "application/pdf" || extension === "pdf") {
    return "application/pdf";
  }

  return undefined;
};

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
        reject(new Error(translations[language].fileReadError));
      }
    };

    reader.onerror = () =>
      reject(new Error(translations[language].fileReadFailure));

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

  useEffect(() => {
    // The initial greeting is intentionally synchronized when the language changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMessages((currentMessages) =>
      currentMessages.length === 1 &&
      currentMessages[0].role === "assistant"
        ? [createMessage("assistant", t.greeting)]
        : currentMessages
    );
  }, [language, t.greeting]);

  const handleSend = async (content: string, file?: File) => {
    if (loading) return;

    setError("");

    const requestLanguage = language;
    const requestTranslations = translations[requestLanguage];

    let attachment: ChatImage | undefined;

    if (file) {
      const mimeType = getSupportedMimeType(file);

      if (!mimeType) {
        setError(requestTranslations.unsupportedFileError);
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        setError(
          requestLanguage === "en"
            ? "The file must be 5 MB or smaller."
            : 
            "የፋይሉ መጠን 5 MB ወይም ከዚያ በታች መሆን አለበት።"
        );
        return;
      }
    }

    setLoading(true);

    try {
      if (file) {
        attachment = {
          fileName: file.name,
          mimeType: getSupportedMimeType(file)!,
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
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : requestTranslations.requestError
      );

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
               <MessageBubble message={message} language={language} />

                {message.role === "user" &&
                  message.attachment && (
                    <div
                      style={{
                        margin: "8px 0 16px 44px",
                        maxWidth: "min(360px, calc(100% - 44px))",
                      }}
                    >
                      {message.attachment.mimeType ===
                      "application/pdf" ? (
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "12px",
                            padding: "12px 14px",
                            border: "1px solid #d8dee8",
                            borderRadius: "10px",
                            background: "#f8fafc",
                            overflowWrap: "anywhere",
                          }}
                        >
                          <span
                            aria-hidden="true"
                            style={{
                              fontSize: "28px",
                              lineHeight: 1,
                            }}
                          >
                            📄
                          </span>

                          <div style={{ minWidth: 0 }}>
                            <div
                              style={{
                                fontWeight: 600,
                                fontSize: "14px",
                              }}
                            >
                              {t.attachedDocument}
                            </div>

                            <div
                              style={{
                                fontSize: "13px",
                                color: "#475569",
                                overflowWrap: "anywhere",
                              }}
                            >
                              {message.attachment.fileName}
                            </div>
                          </div>
                        </div>
                      ) : (
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
                      )}

                      {message.attachment.mimeType !==
                        "application/pdf" && (
                        <p className="input-hint">
                          {message.attachment.fileName}
                        </p>
                      )}
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
                      language === "am" ? "Processing" : "Processing"
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
