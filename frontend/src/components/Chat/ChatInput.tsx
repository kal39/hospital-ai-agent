import { useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({
  onSend,
  disabled = false,
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-area">
      <div className="input-wrapper">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your hospital information..."
          rows={1}
          disabled={disabled}
          aria-label="Message"
        />

        <div className="input-actions">
          <button
            type="button"
            className="secondary-input-button"
            disabled
            title="File and image support will be added later"
          >
            Attach
          </button>

          <button
            type="button"
            className="secondary-input-button"
            disabled
            title="Voice support will be added later"
          >
            Voice
          </button>

          <button
            type="button"
            className="send-button"
            onClick={handleSend}
            disabled={disabled || !message.trim()}
          >
            {disabled ? "Sending..." : "Send"}
          </button>
        </div>
      </div>

      <p className="input-hint">
        Press Enter to send. Use Shift + Enter for a new line.
      </p>
    </div>
  );
}