
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import type { ChatMessage, Language } from "../../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
  language: Language;
}

export default function MessageBubble({
  message,
  language,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const content =
    typeof message.content === "string" ? message.content : "";
  const [speaking, setSpeaking] = useState(false);
  const speechAvailable =
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

function stopSpeech() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }

  function speakMessage() {
    if (!speechAvailable || !content.trim()) return;

    // Stop any previous response before playing this one.
    window.speechSynthesis.cancel();

    // Read the actual text, not Markdown formatting.
    const plainText = content
      .replace(/```[\s\S]*?```/g, " Code block omitted. ")
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[#*_>`~-]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    const utterance = new SpeechSynthesisUtterance(plainText);
    utterance.lang = language === "am" ? "am-ET" : "en-US";
    utterance.rate = 0.95;

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }

  return (
    <div
      className={`message-row ${
        isUser ? "message-row-user" : "message-row-assistant"
      }`}
    >
      <div
        className={`message-bubble ${
          isUser ? "message-user" : "message-assistant"
        }`}
      >
        <div className="message-role">
          {isUser ? "You" : "Hospital AI Assistant"}
        </div>

        <div
          className={`message-content ${
            isUser
              ? "message-content-user"
              : "message-content-assistant"
          }`}
        >
          {isUser ? (
            content
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeSanitize]}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>

        <div className="message-footer">
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>

          {!isUser && content.trim() && speechAvailable && (
            <button
              type="button"
              className="message-speech-button"
              onClick={speaking ? stopSpeech : speakMessage}
              aria-label={speaking ? "Stop speaking" : "Read response aloud"}
              title={speaking ? "Stop speaking" : "Read response aloud"}
            >
              {speaking ? "■ Stop" : "▶ Listen"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}