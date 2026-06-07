/**
 * components/ChatInput.jsx  –  Message input bar with voice recording.
 */
import { useState, useEffect, useRef } from "react";
import { Send, Mic, MicOff, Volume2, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";
import clsx from "clsx";

export default function ChatInput() {
  const { sendMessage, language, mode, setMode, isTyping } = useStore();
  const [text, setText]           = useState("");
  const [recording, setRecording] = useState(false);
  const [voiceOut, setVoiceOut]   = useState(false);
  const [sending, setSending]     = useState(false);
  const inputRef  = useRef(null);
  const mediaRef  = useRef(null);
  const chunksRef = useRef([]);
  const tx = (key) => t(key, language);

  // Listen for suggestion clicks from ChatWindow empty state
  useEffect(() => {
    const handler = (e) => setText(e.detail);
    window.addEventListener("suggestion-click", handler);
    return () => window.removeEventListener("suggestion-click", handler);
  }, []);

  const handleSend = async () => {
    const msg = text.trim();
    if (!msg || sending || isTyping) return;
    setText("");
    setSending(true);
    try {
      await sendMessage(msg, voiceOut);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to send message");
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Voice recording ────────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        await uploadAudio(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      mediaRef.current = recorder;
      setRecording(true);
      toast("🎙️ Recording… tap again to stop", { duration: 2000 });
    } catch {
      toast.error("Microphone access denied");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  const uploadAudio = async (blob) => {
    const stored = JSON.parse(localStorage.getItem("sevasetu-store") || "{}");
    const token  = stored?.state?.token;
    const form   = new FormData();
    form.append("audio", blob, "recording.wav");
    form.append("language", language);

    setSending(true);
    try {
      const res = await fetch("/api/v1/voice/stt", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await res.json();
      if (data.transcript) {
        setText(data.transcript);
        toast.success("✅ Transcribed!");
      } else {
        toast.error("Could not understand audio");
      }
    } catch {
      toast.error("Transcription failed");
    } finally {
      setSending(false);
    }
  };

  const isDisabled = sending || isTyping;

  return (
    <div className="border-t border-blue-50 dark:border-white/10 p-3 bg-white/80 dark:bg-charcoal/80 backdrop-blur-md">
      {/* Mode toggle */}
      <div className="flex items-center gap-2 mb-2 px-1">
        <span className="text-xs text-charcoal/50 dark:text-white/50">{tx("mode")}:</span>
        {["beginner", "advanced"].map((m) => (
          <button key={m}
            onClick={() => setMode(m)}
            className={clsx(
              "text-xs px-3 py-0.5 rounded-full font-medium transition-all",
              mode === m
                ? "bg-ashoka text-white shadow-glow-blue"
                : "bg-blue-50 dark:bg-white/10 text-charcoal/60 dark:text-white/60 hover:bg-blue-100"
            )}>
            {tx(m)}
          </button>
        ))}

        <div className="flex-1" />

        {/* Voice output toggle */}
        <button
          onClick={() => setVoiceOut((v) => !v)}
          title="Toggle voice response"
          className={clsx(
            "flex items-center gap-1 text-xs px-2 py-0.5 rounded-full transition-all",
            voiceOut
              ? "bg-jade/10 text-jade border border-jade/30"
              : "text-charcoal/40 dark:text-white/40 hover:text-jade"
          )}>
          <Volume2 size={12} />
          {voiceOut ? "आवाज़ चालू" : "आवाज़ बंद"}
        </button>
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKey}
            placeholder={tx("typePlaceholder")}
            rows={1}
            disabled={isDisabled}
            style={{ resize: "none", minHeight: "44px", maxHeight: "120px" }}
            className="w-full px-4 py-2.5 pr-12 rounded-2xl border border-blue-100 dark:border-white/20
                       bg-white dark:bg-charcoal text-sm text-charcoal dark:text-white
                       placeholder:text-charcoal/30 dark:placeholder:text-white/30
                       focus:outline-none focus:ring-2 focus:ring-ashoka/30
                       disabled:opacity-50 transition-all"
          />

          {/* Voice mic inside input */}
          <button
            onClick={recording ? stopRecording : startRecording}
            disabled={isDisabled}
            className={clsx(
              "absolute right-3 bottom-2.5 p-1.5 rounded-full transition-all",
              recording
                ? "bg-red-500 text-white animate-pulse-slow"
                : "text-charcoal/40 hover:text-saffron hover:bg-saffron/10"
            )}>
            {recording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || isDisabled}
          className={clsx(
            "w-11 h-11 rounded-2xl flex items-center justify-center transition-all flex-shrink-0",
            text.trim() && !isDisabled
              ? "bg-ashoka text-white shadow-glow-blue hover:bg-ashoka-dark active:scale-95"
              : "bg-blue-50 dark:bg-white/10 text-charcoal/30 dark:text-white/30 cursor-not-allowed"
          )}>
          {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>

      {/* Recording waveform */}
      {recording && (
        <div className="flex items-center justify-center gap-0.5 mt-2 h-5">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="waveform-bar"
                 style={{ height: `${8 + Math.random() * 12}px`, animationDelay: `${i * 0.08}s` }} />
          ))}
        </div>
      )}
    </div>
  );
}
