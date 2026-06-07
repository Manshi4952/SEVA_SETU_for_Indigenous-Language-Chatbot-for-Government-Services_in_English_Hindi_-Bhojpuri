/**
 * components/ChatWindow.jsx  –  The core chat UI.
 *
 * Features:
 *  - Message bubbles (user / bot)
 *  - Typing indicator
 *  - Retrieved scheme chips
 *  - Voice playback button
 *  - Auto-scroll to latest message
 */
import { useEffect, useRef } from "react";
import { Volume2, Bot, User } from "lucide-react";
import useStore from "../store/useStore";
import clsx from "clsx";

// ── Typing indicator ────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex items-end gap-2 animate-fade-up">
      <div className="w-8 h-8 rounded-full bg-ashoka/10 flex items-center justify-center flex-shrink-0">
        <Bot size={14} className="text-ashoka" />
      </div>
      <div className="chat-bubble-bot flex items-center gap-1 py-3 px-4">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}

// ── Scheme chip ─────────────────────────────────────────────────────────────
function SchemeChip({ name, score }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full
                     bg-jade/10 text-jade border border-jade/20 font-medium">
      📋 {name}
      <span className="text-jade/60">({Math.round(score * 100)}%)</span>
    </span>
  );
}

// ── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === "user";

  const playAudio = () => {
    if (msg.audio_url) {
      new Audio(msg.audio_url).play();
    }
  };

  return (
    <div className={clsx("flex gap-2 animate-fade-up", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-ashoka flex items-center justify-center flex-shrink-0 shadow-glow-blue mt-1">
          <Bot size={14} className="text-white" />
        </div>
      )}

      <div className={clsx("flex flex-col gap-1.5", isUser ? "items-end" : "items-start")}>
        <div className={isUser ? "chat-bubble-user" : "chat-bubble-bot"}>
          {/* Render markdown-like bold text */}
          <p className="text-sm leading-relaxed whitespace-pre-wrap"
             dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
        </div>

        {/* Retrieved scheme chips */}
        {!isUser && msg.retrieved_schemes?.length > 0 && (
          <div className="flex flex-wrap gap-1 px-1">
            {msg.retrieved_schemes.slice(0, 3).map((s) => (
              <SchemeChip key={s.id} name={s.name} score={s.relevance_score} />
            ))}
          </div>
        )}

        {/* Footer: time + audio */}
        <div className="flex items-center gap-2 px-1">
          <span className="text-xs text-charcoal/40">
            {new Date(msg.created_at).toLocaleTimeString("en-IN", {
              hour: "2-digit", minute: "2-digit",
            })}
          </span>
          {msg.audio_url && (
            <button onClick={playAudio}
              className="flex items-center gap-1 text-xs text-ashoka hover:text-saffron transition-colors">
              <Volume2 size={12} /> सुनें
            </button>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-saffron flex items-center justify-center flex-shrink-0 shadow-glow mt-1">
          <User size={14} className="text-white" />
        </div>
      )}
    </div>
  );
}

// Convert **bold** markdown to <strong>
function formatMessage(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

// ── Empty state ──────────────────────────────────────────────────────────────
function EmptyChat({ language }) {
  const prompts = {
    hindi:    ["PM किसान योजना के बारे में बताएं", "Ayushman Bharat के लिए पात्रता क्या है?", "PMAY के लिए आवेदन कैसे करें?"],
    bhojpuri: ["PM किसान के बारे में बताईं", "आयुष्मान भारत खातिर पात्रता का बा?", "PMAY में आवेदन कइसे करीं?"],
    english:  ["Tell me about PM Kisan scheme", "Eligibility for Ayushman Bharat?", "How to apply for PMAY?"],
  };

  const suggestions = prompts[language] || prompts.hindi;

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 py-12">
      <div className="w-20 h-20 rounded-full bg-india-gradient flex items-center justify-center shadow-glow">
        <span className="text-3xl">🤖</span>
      </div>
      <div className="text-center">
        <h3 className="font-display text-xl font-bold text-charcoal dark:text-white mb-1">
          {language === "english" ? "Ask me anything!" : "कुछ भी पूछें!"}
        </h3>
        <p className="text-sm text-charcoal/50">
          {language === "english" ? "Government schemes • Eligibility • Documents • Application process"
                                  : "सरकारी योजनाएं • पात्रता • दस्तावेज़ • आवेदन प्रक्रिया"}
        </p>
      </div>

      <div className="flex flex-col gap-2 w-full max-w-sm">
        {suggestions.map((s, i) => (
          <button key={i}
            className="w-full text-left px-4 py-2.5 rounded-xl border border-blue-100
                       bg-white dark:bg-charcoal hover:border-ashoka hover:shadow-card
                       text-sm text-charcoal/70 dark:text-white/70 transition-all"
            onClick={() => {
              const event = new CustomEvent("suggestion-click", { detail: s });
              window.dispatchEvent(event);
            }}>
            💬 {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main ChatWindow ──────────────────────────────────────────────────────────
export default function ChatWindow() {
  const { messages, isTyping, language } = useStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (messages.length === 0) return <EmptyChat language={language} />;

  return (
    <div className="flex flex-col gap-4 py-4 px-2">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} msg={msg} />
      ))}
      {isTyping && <TypingDots />}
      <div ref={bottomRef} />
    </div>
  );
}
