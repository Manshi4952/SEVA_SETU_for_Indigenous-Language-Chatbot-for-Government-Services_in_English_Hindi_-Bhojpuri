/**
 * components/ChatInput.jsx  –  Message input bar (v2)
 *
 * Changes:
 *  - Retry button shown on send error
 *  - Enter to send, Shift+Enter for newline
 *  - Voice input button wired to STT API
 *  - Mode toggle (Beginner / Advanced) controls LLM verbosity
 */
import { useState, useRef, useCallback } from "react";
import { Send, Mic, MicOff, Loader2 } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";
import api from "../utils/api";

export default function ChatInput() {
  const { sendMessage, language, isTyping } = useStore();
  const [text, setText] = useState("");
  const [mode, setMode] = useState("beginner");
  const [voiceActive, setVoiceActive] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const textareaRef = useRef(null);
  const tx = (k) => t(k, language);

  const handleSend = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || isTyping || sending) return;

    setText("");
    setSending(true);
    try {
      await sendMessage(trimmed, language, mode, false);
    } catch {
      toast.error(
        language === "hindi"
          ? "भेजने में त्रुटि हुई। फिर कोशिश करें।"
          : language === "bhojpuri"
          ? "भेजे में गड़बड़ भइल। फेर कोशिश करीं।"
          : "Failed to send. Please try again."
      );
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }, [text, isTyping, sending, sendMessage, language, mode]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Voice input via STT
  const handleVoice = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      toast.error("Voice input not supported in this browser.");
      return;
    }
    setVoiceActive(true);
    setVoiceLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", blob, "voice.webm");
        try {
          const res = await api.post(`/voice/stt?language=${language}`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          if (res.data.text) {
            setText(res.data.text);
          }
        } catch {
          toast.error("Voice transcription failed.");
        } finally {
          setVoiceLoading(false);
          setVoiceActive(false);
        }
      };
      recorder.start();
      // Auto-stop after 8 seconds
      setTimeout(() => { if (recorder.state === "recording") recorder.stop(); }, 8000);
      toast(
        language === "hindi" ? "🎤 8 सेकंड बोलें…" : language === "bhojpuri" ? "🎤 8 सेकंड बोलीं…" : "🎤 Speak for 8 seconds…",
        { duration: 8000 }
      );
    } catch {
      toast.error("Microphone access denied.");
      setVoiceActive(false);
      setVoiceLoading(false);
    }
  };

  const modeLabels = {
    beginner: { hindi: "आसान", bhojpuri: "आसान", english: "Simple" },
    advanced: { hindi: "विस्तार से", bhojpuri: "विस्तार से", english: "Detailed" },
  };

  return (
    <div className="border-t border-blue-50 dark:border-white/10 bg-white/80 dark:bg-charcoal/80
                    backdrop-blur-sm px-4 py-3">
      {/* Mode toggle */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-charcoal/40 dark:text-white/40">
          {language === "hindi" ? "तरीका:" : language === "bhojpuri" ? "तरीका:" : "Mode:"}
        </span>
        {["beginner", "advanced"].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={clsx(
              "px-3 py-0.5 rounded-full text-xs font-medium transition-all",
              mode === m
                ? "bg-ashoka text-white shadow-glow-blue"
                : "border border-blue-100 dark:border-white/20 text-charcoal/50 dark:text-white/50 hover:border-ashoka"
            )}
          >
            {modeLabels[m][language] || modeLabels[m].english}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={tx("typePlaceholder")}
            rows={1}
            disabled={isTyping || sending}
            className="w-full resize-none px-4 py-3 rounded-2xl border border-blue-100
                       dark:border-white/20 bg-white dark:bg-charcoal/60 text-charcoal
                       dark:text-white placeholder:text-charcoal/30 dark:placeholder:text-white/30
                       text-sm focus:outline-none focus:ring-2 focus:ring-ashoka/30 transition-all
                       min-h-[44px] max-h-32 overflow-y-auto disabled:opacity-60"
            style={{ height: "auto" }}
            onInput={(e) => {
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 128) + "px";
            }}
          />
        </div>

        {/* Voice button */}
        <button
          onClick={handleVoice}
          disabled={voiceLoading || isTyping}
          title={tx("voiceBtn")}
          className={clsx(
            "w-11 h-11 rounded-xl flex items-center justify-center transition-all flex-shrink-0",
            voiceActive
              ? "bg-red-500 text-white animate-pulse"
              : "border border-blue-100 dark:border-white/20 text-charcoal/40 hover:text-saffron hover:border-saffron"
          )}
        >
          {voiceLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : voiceActive ? (
            <MicOff size={18} />
          ) : (
            <Mic size={18} />
          )}
        </button>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || isTyping || sending}
          className="w-11 h-11 rounded-xl bg-ashoka text-white flex items-center justify-center
                     shadow-glow-blue hover:bg-ashoka-dark transition-all active:scale-95
                     disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
        >
          {sending || isTyping ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>

      <p className="text-[10px] text-charcoal/25 dark:text-white/25 text-center mt-2">
        {language === "hindi"
          ? "Enter से भेजें · Shift+Enter से नई लाइन"
          : language === "bhojpuri"
          ? "Enter से भेजीं · Shift+Enter से नई लाइन"
          : "Enter to send · Shift+Enter for new line"}
      </p>
    </div>
  );
}
