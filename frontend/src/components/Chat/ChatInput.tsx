
import { useEffect, useRef, useState } from "react";
import type { Language } from "../../types/chat";

interface ChatInputProps {
  onSend: (message: string, image?: File) => void;
  disabled?: boolean;
  language: Language;
}

interface SpeechAlternative {
  transcript: string;
}

interface SpeechResult {
  readonly isFinal: boolean;
  readonly length: number;
  [index: number]: SpeechAlternative;
}

interface SpeechResultEvent {
  resultIndex: number;
  results: {
    readonly length: number;
    [index: number]: SpeechResult;
  };
}

interface SpeechErrorEvent {
  error: string;
}

interface SpeechRecognitionInstance {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: ((event: SpeechErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

const MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024;

const ALLOWED_ATTACHMENT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
];

const translations = {
  en: {
    placeholder: "Ask about your hospital information...",
    messageLabel: "Message",
    attachImage: "Attach file",
    remove: "Remove",
    removeImage: "Remove selected file",
    selectedImagePreview: "Selected image preview",
    voice: "Voice",
    stopVoice: "Stop voice",
    send: "Send",
    sending: "Sending...",
    imageOnlyPrompt:
      "Please help me understand the information in this attached file.",
    imageTypeError:
      "Choose a JPG, PNG, WebP image, or PDF document.",
    imageSizeError: "The file must be 5 MB or smaller.",
    enterToSend: "Press Enter to send. Use Shift + Enter for a new line.",
    recognizing: "Recognizing",
    listening: "Listening...",
    finished:
      "Voice input finished. Review the text before sending.",
    finishing: "Finishing voice input...",
    unsupported:
      "Voice input is not supported by this browser. Please type your message.",
    microphoneDenied:
      "Microphone access was denied. Allow microphone access in your browser settings.",
    serviceUnavailable:
      "The browser speech-recognition service is unavailable or blocked.",
    noSpeech: "No speech was detected. Please try speaking again.",
    noMicrophone:
      "No microphone was detected. Check your microphone connection.",
    networkError:
      "A network error interrupted voice recognition. Check your connection.",
    stopped: "Voice input was stopped.",
    languageUnsupported:
      "Amharic voice recognition is not supported by the current browser speech service. Type your Amharic message or try another browser that supports Amharic recognition.",
    voiceFailed:
      "Voice input failed. Please try again or type your message.",
    startFailed:
      "Could not start voice input. Check your microphone permissions and try again.",
  },
  am: {
    placeholder: "ስለ ሆስፒታል መረጃዎ ይጠይቁ...",
    messageLabel: "መልዕክት",
    attachImage: "ፋይል ያያይዙ",
    remove: "አስወግድ",
    removeImage: "የተመረጠውን ፋይል አስወግድ",
    selectedImagePreview: "የተመረጠው ምስል ቅድመ እይታ",
    voice: "በድምፅ ይናገሩ",
    stopVoice: "ድምፅ ማዳመጥ አቁም",
    send: "ላክ",
    sending: "በመላክ ላይ...",
    imageOnlyPrompt:
      "በተያያዘው ፋይል ውስጥ ያለውን መረጃ እንድረዳ እርዳኝ።",
    imageTypeError:
      "JPG፣ PNG፣ WebP ምስል ወይም PDF ሰነድ ይምረጡ።",
    imageSizeError:
      "የፋይሉ መጠን 5 MB ወይም ከዚያ በታች መሆን አለበት።",
    enterToSend:
      "ለመላክ Enter ይጫኑ። አዲስ መስመር ለመጀመር Shift + Enter ይጠቀሙ።",
    recognizing: "ድምፅን በመለየት ላይ",
    listening: "በማዳመጥ ላይ...",
    finished:
      "የድምፅ ግቤት ተጠናቋል። ከመላክዎ በፊት ጽሑፉን ይመልከቱ።",
    finishing: "የድምፅ ግቤትን በማጠናቀቅ ላይ...",
    unsupported:
      "ይህ አሳሽ የድምፅ ግቤትን አይደግፍም። እባክዎ መልዕክትዎን በጽሑፍ ያስገቡ።",
    microphoneDenied:
      "የማይክሮፎን ፈቃድ አልተሰጠም። በአሳሹ ቅንብሮች ውስጥ ፈቃዱን ይፍቀዱ።",
    serviceUnavailable:
      "የአሳሹ የድምፅ መለያ አገልግሎት አይገኝም ወይም ታግዷል።",
    noSpeech:
      "ድምፅ አልተለየም። እባክዎ እንደገና ይናገሩ።",
    noMicrophone:
      "ማይክሮፎን አልተገኘም። ግንኙነቱን ያረጋግጡ።",
    networkError:
      "የኔትወርክ ችግር የድምፅ መለያውን አቋረጠ። ግንኙነትዎን ያረጋግጡ።",
    stopped: "የድምፅ ግቤት ቆሟል።",
    languageUnsupported:
      "የአሁኑ የአሳሽ የድምፅ አገልግሎት አማርኛን ላይደግፍ ይችላል። እባክዎ በአማርኛ ይጻፉ ወይም ሌላ ተስማሚ አሳሽ ይሞክሩ።",
    voiceFailed:
      "የድምፅ ግቤት አልተሳካም። እንደገና ይሞክሩ ወይም በጽሑፍ ያስገቡ።",
    startFailed:
      "የድምፅ ግቤትን መጀመር አልተቻለም። የማይክሮፎን ፈቃድዎን ያረጋግጡ።",
  },
} satisfies Record<Language, Record<string, string>>;

export default function ChatInput({
  onSend,
  disabled = false,
  language,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [voiceStatus, setVoiceStatus] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imageError, setImageError] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const t = translations[language];

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      recognitionRef.current = null;
    };
  }, []);

  const handleImageSelection = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    setImageError("");

    if (!ALLOWED_ATTACHMENT_TYPES.includes(file.type)) {
      setImageError(t.imageTypeError);
      return;
    }

    if (file.size > MAX_ATTACHMENT_SIZE) {
      setImageError(t.imageSizeError);
      return;
    }

    setSelectedImage(file);
  };

  const handleSend = () => {
    const trimmed = message.trim();

    if ((!trimmed && !selectedImage) || disabled) return;

    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
      setIsListening(false);
    }

    const finalMessage = trimmed || t.imageOnlyPrompt;

    onSend(finalMessage, selectedImage ?? undefined);

    setMessage("");
    setSelectedImage(null);
    setImageError("");
    setInterimTranscript("");
    setVoiceStatus("");
  };

  const startVoiceInput = () => {
    setVoiceStatus("");
    setInterimTranscript("");

    const speechWindow = window as SpeechWindow;
    const SpeechRecognitionAPI =
      speechWindow.SpeechRecognition ??
      speechWindow.webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      setVoiceStatus(t.unsupported);
      return;
    }

    try {
      const recognition = new SpeechRecognitionAPI();

      recognition.lang = language === "am" ? "am-ET" : "en-US";
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let finalText = "";
        let interimText = "";

        for (
          let index = event.resultIndex;
          index < event.results.length;
          index++
        ) {
          const result = event.results[index];
          const transcript = result[0]?.transcript ?? "";

          if (result.isFinal) {
            finalText += transcript;
          } else {
            interimText += transcript;
          }
        }

        if (finalText.trim()) {
          const recognized = finalText.trim();

          setMessage((previous) => {
            if (!previous.trim()) return recognized;

            const separator = /\s$/.test(previous) ? "" : " ";
            return previous + separator + recognized;
          });
        }

        setInterimTranscript(interimText.trim());
      };

      recognition.onerror = (event) => {
        const errorMessages: Record<string, string> = {
          "not-allowed": t.microphoneDenied,
          "service-not-allowed": t.serviceUnavailable,
          "no-speech": t.noSpeech,
          "audio-capture": t.noMicrophone,
          network: t.networkError,
          aborted: t.stopped,
          "language-not-supported": t.languageUnsupported,
        };

        setVoiceStatus(
          errorMessages[event.error] ??
            `${t.voiceFailed} (${event.error})`
        );

        setIsListening(false);
        setInterimTranscript("");
        recognitionRef.current = null;
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimTranscript("");
        recognitionRef.current = null;

        setVoiceStatus((previous) =>
          previous === t.listening ? t.finished : previous
        );
      };

      recognitionRef.current = recognition;
      recognition.start();

      setIsListening(true);
      setVoiceStatus(t.listening);
    } catch {
      recognitionRef.current = null;
      setIsListening(false);
      setVoiceStatus(t.startFailed);
    }
  };

  const handleVoiceClick = () => {
    if (disabled) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setVoiceStatus(t.finishing);
    } else {
      startVoiceInput();
    }
  };

  const isSelectedPdf =
    selectedImage?.type === "application/pdf";

  return (
    <div className="chat-input-area">
      <div className="input-wrapper">
        {selectedImage && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "10px",
              marginBottom: "10px",
              border: "1px solid #d8dee8",
              borderRadius: "10px",
            }}
          >
            {isSelectedPdf ? (
              <div
                aria-label="PDF document"
                style={{
                  width: "76px",
                  height: "76px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "8px",
                  background: "#f1f5f9",
                  color: "#334155",
                  fontWeight: 700,
                }}
              >
                PDF
              </div>
            ) : (
              <img
                src={URL.createObjectURL(selectedImage)}
                alt={t.selectedImagePreview}
                style={{
                  width: "76px",
                  height: "76px",
                  objectFit: "cover",
                  borderRadius: "8px",
                }}
              />
            )}

            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  fontSize: "14px",
                }}
              >
                {selectedImage.name}
              </div>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                {(selectedImage.size / 1024).toFixed(0)} KB
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setSelectedImage(null);
                setImageError("");
              }}
              disabled={disabled}
              aria-label={t.removeImage}
              title={t.removeImage}
            >
              {t.remove}
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,application/pdf,.pdf"
          onChange={handleImageSelection}
          hidden
          disabled={disabled}
        />

        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          placeholder={t.placeholder}
          rows={1}
          disabled={disabled}
          aria-label={t.messageLabel}
        />

        <div className="input-actions">
          <button
            type="button"
            className="secondary-input-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            title={t.attachImage}
          >
            {t.attachImage}
          </button>

          <button
            type="button"
            className="secondary-input-button"
            onClick={handleVoiceClick}
            disabled={disabled}
            aria-pressed={isListening}
          >
            {isListening ? t.stopVoice : t.voice}
          </button>

          <button
            type="button"
            className="send-button"
            onClick={handleSend}
            disabled={disabled || (!message.trim() && !selectedImage)}
          >
            {disabled ? t.sending : t.send}
          </button>
        </div>
      </div>

      {imageError && (
        <p className="input-hint" role="alert">
          {imageError}
        </p>
      )}

      {interimTranscript && (
        <p className="input-hint" aria-live="polite">
          {t.recognizing}: {interimTranscript}
        </p>
      )}

      {voiceStatus && (
        <p className="input-hint" role="status" aria-live="polite">
          {voiceStatus}
        </p>
      )}

      <p className="input-hint">{t.enterToSend}</p>
    </div>
  );
}
