/**
 * components/ChatWindow.jsx  –  Chat message list with markdown rendering (v2)
 *
 * Fixes:
 *  - NaN% guard on SchemeChip (score may be undefined/null)
 *  - Bold markdown (**text**) rendered properly
 *  - Numbered steps rendered as <ol>
 *  - Copy button on bot messages
 *  - Smooth scroll on new message
 */
import { useEffect, useRef, useState } from "react";
import { Copy, Check, ExternalLink } from "lucide-react";
import clsx from "clsx";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";

// ── Simple markdown renderer ──────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return [];

  const lines = text.split("\n");
  const elements = [];
  let key = 0;
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Numbered list: lines starting with "1. " "2. " etc.
    if (/^\d+\.\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        const content = lines[i].replace(/^\d+\.\s/, "");
        listItems.push(<li key={i} className="mb-1">{inlineFormat(content)}</li>);
        i++;
      }
      elements.push(
        <ol key={key++} className="list-decimal list-inside space-y-1 my-2 pl-2">
          {listItems}
        </ol>
      );
      continue;
    }

    // Bullet list
    if (/^[-•]\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^[-•]\s/.test(lines[i])) {
        const content = lines[i].replace(/^[-•]\s/, "");
        listItems.push(<li key={i} className="mb-1">{inlineFormat(content)}</li>);
        i++;
      }
      elements.push(
        <ul key={key++} className="list-disc list-inside space-y-1 my-2 pl-2">
          {listItems}
        </ul>
      );
      continue;
    }

    // Empty line → spacer
    if (line.trim() === "") {
      elements.push(<div key={key++} className="h-2" />);
      i++;
      continue;
    }

    // Separator line
    if (line.trim() === "---") {
      elements.push(<hr key={key++} className="border-blue-100 dark:border-white/10 my-3" />);
      i++;
      continue;
    }

    // Normal paragraph
    elements.push(
      <p key={key++} className="leading-relaxed">
        {inlineFormat(line)}
      </p>
    );
    i++;
  }

  return elements;
}

// Inline formatting: **bold**, *italic*
function inlineFormat(text) {
  if (!text) return null;
  const parts = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let last = 0;
  let m;

  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[2]) parts.push(<strong key={m.index} className="font-semibold text-charcoal dark:text-white">{m[2]}</strong>);
    else if (m[3]) parts.push(<em key={m.index}>{m[3]}</em>);
    last = m.index + m[0].length;
  }

  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

// ── Scheme chip ───────────────────────────────────────────────────────────────
function SchemeChip({ name, score }) {
  const pct = (score != null && !isNaN(score) && isFinite(score))
    ? Math.round(score * 100)
    : null;

  return (
    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full
                     bg-jade/10 text-jade border border-jade/20 font-medium whitespace-nowrap">
      📋 {name}
      {pct !== null && <span className="text-jade/60 ml-0.5">({pct}%)</span>}
    </span>
  );
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 mb-4 animate-fade-up">
      <div className="w-8 h-8 rounded-full bg-ashoka flex items-center justify-center flex-shrink-0">
        <span className="text-white text-xs font-bold">SS</span>
      </div>
      <div className="chat-bubble-bot flex items-center gap-1 px-4 py-3">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}

// ── Individual message ────────────────────────────────────────────────────────
function ChatMessage({ msg }) {
  const [copied, setCopied] = useState(false);
  const isUser = msg.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className={clsx("flex gap-3 mb-4 animate-fade-up", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold",
        isUser ? "bg-saffron" : "bg-ashoka"
      )}>
        {isUser ? "आप" : "SS"}
      </div>

      <div className={clsx("flex flex-col gap-1", isUser ? "items-end" : "items-start", "max-w-[82%]")}>
        {/* Bubble */}
        <div className={clsx(isUser ? "chat-bubble-user" : "chat-bubble-bot")}>
          {isUser ? (
            <p className="leading-relaxed text-sm">{msg.content}</p>
          ) : (
            <div className="text-sm space-y-1">{renderMarkdown(msg.content)}</div>
          )}
        </div>

        {/* Scheme chips */}
        {!isUser && msg.retrieved_schemes?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {msg.retrieved_schemes.map((s) => (
              <SchemeChip key={s.id} name={s.name} score={s.relevance_score} />
            ))}
          </div>
        )}

        {/* Actions row */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-charcoal/30 dark:text-white/30">
            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
          </span>

          {!isUser && (
            <button
              onClick={handleCopy}
              title="Copy"
              className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/10 text-charcoal/30 hover:text-charcoal/60 transition-colors"
            >
              {copied ? <Check size={12} className="text-jade" /> : <Copy size={12} />}
            </button>
          )}

          {/* Audio playback */}
          {!isUser && msg.audio_url && (
            <audio controls src={msg.audio_url} className="h-6 max-w-[140px] opacity-70 hover:opacity-100" />
          )}
        </div>
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ language }) {
  const suggestions = {
    hindi: [
      "PM किसान योजना के बारे में बताएं",
      "PMAY आवास योजना क्या है?",
      "वृद्धजन पेंशन कैसे मिलेगी?",
      "बिहार स्टूडेंट क्रेडिट कार्ड",
    ],
    bhojpuri: [
      "PM किसान के बारे में बताईं",
      "PMAY आवास योजना का बा?",
      "वृद्धजन पेंशन कइसे मिलेला?",
      "बिहार स्टूडेंट क्रेडिट कार्ड",
    ],
    english: [
      "Tell me about PM Kisan scheme",
      "What is PMAY housing scheme?",
      "How to get old age pension?",
      "Bihar Student Credit Card",
    ],
  };

  const items = suggestions[language] || suggestions.hindi;

  return (
    <div className="flex flex-col items-center justify-center h-full py-16 px-6 text-center">
      <div className="text-6xl mb-4">🏛️</div>
      <h3 className="font-display text-xl font-bold text-charcoal dark:text-white mb-2">
        {language === "hindi" ? "SevaSetu से पूछें" : language === "bhojpuri" ? "SevaSetu से पूछीं" : "Ask SevaSetu"}
      </h3>
      <p className="text-sm text-charcoal/50 dark:text-white/50 mb-6 max-w-sm">
        {language === "hindi"
          ? "बिहार की 218+ सरकारी योजनाओं की जानकारी पाएं"
          : language === "bhojpuri"
          ? "बिहार के 218+ सरकारी योजनाओं के बारे में जानीं"
          : "Get information on 218+ Bihar government schemes"}
      </p>
      <div className="flex flex-col gap-2 w-full max-w-sm">
        {items.map((s) => (
          <SuggestionChip key={s} text={s} />
        ))}
      </div>
    </div>
  );
}

function SuggestionChip({ text }) {
  const { sendMessage, language, isTyping } = useStore();
  const mode = "beginner";

  const handleClick = () => {
    if (isTyping) return;
    sendMessage(text, language, mode);
  };

  return (
    <button
      onClick={handleClick}
      className="text-left px-4 py-2.5 rounded-xl border border-blue-100 dark:border-white/10
                 bg-white dark:bg-charcoal text-sm text-charcoal dark:text-white
                 hover:border-ashoka hover:bg-ashoka/5 transition-all active:scale-95"
    >
      {text}
    </button>
  );
}

// ── Main ChatWindow ───────────────────────────────────────────────────────────
export default function ChatWindow() {
  const { messages, isTyping, language } = useStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (messages.length === 0 && !isTyping) {
    return <div className="flex-1 overflow-y-auto"><EmptyState language={language} /></div>;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} msg={msg} />
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
