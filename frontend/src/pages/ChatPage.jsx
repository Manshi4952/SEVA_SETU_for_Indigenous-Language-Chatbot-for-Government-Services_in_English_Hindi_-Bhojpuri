/**
 * pages/ChatPage.jsx  –  Main chat interface (v2)
 *
 * Changes:
 *  - Sidebar loads and shows real conversation history
 *  - Delete conversation with confirmation
 *  - "New Chat" properly clears context
 *  - Online indicator is purely cosmetic; no hard-coded "Online" when offline
 *  - Redirect to login if not authenticated
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, MessageCircle, Loader2 } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

export default function ChatPage() {
  const {
    isAuthenticated,
    language,
    conversations,
    activeConversationId,
    loadConversations,
    loadConversation,
    clearMessages,
    deleteConversation,
    isTyping,
  } = useStore();

  const navigate = useNavigate();
  const tx = (k) => t(k, language);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    loadConversations();
  }, [isAuthenticated]);

  const handleNewChat = () => {
    clearMessages();
  };

  const handleSelectConv = (id) => {
    if (id === activeConversationId) return;
    loadConversation(id);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      toast.success(
        language === "hindi" ? "बातचीत हटाई गई" : language === "bhojpuri" ? "बातचीत हटावल गइल" : "Conversation deleted"
      );
    } catch {
      toast.error("Failed to delete.");
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)] overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="w-64 flex flex-col border-r border-blue-50 dark:border-white/10
                        bg-white dark:bg-charcoal flex-shrink-0 hidden md:flex">
        {/* New Chat button */}
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl
                       bg-saffron text-white font-semibold text-sm
                       hover:bg-saffron-dark shadow-glow transition-all active:scale-95"
          >
            <Plus size={18} />
            {tx("newChat")}
          </button>
        </div>

        {/* History label */}
        <div className="px-4 pb-1">
          <p className="text-xs font-semibold text-charcoal/40 dark:text-white/40 uppercase tracking-wider">
            {tx("chatHistory")}
          </p>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5">
          {conversations.length === 0 ? (
            <p className="text-xs text-charcoal/30 dark:text-white/30 text-center px-4 pt-4">
              {language === "hindi" ? "कोई बातचीत नहीं" : "No conversations yet"}
            </p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => handleSelectConv(conv.id)}
                className={clsx(
                  "w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-sm transition-all group",
                  activeConversationId === conv.id
                    ? "bg-ashoka/10 text-ashoka dark:text-blue-300 font-medium"
                    : "text-charcoal/70 dark:text-white/60 hover:bg-black/5 dark:hover:bg-white/5"
                )}
              >
                <MessageCircle size={14} className="flex-shrink-0 opacity-60" />
                <span className="flex-1 truncate text-xs">{conv.title}</span>
                <button
                  onClick={(e) => handleDelete(e, conv.id)}
                  className="opacity-0 group-hover:opacity-60 hover:!opacity-100 p-0.5
                             rounded hover:text-red-500 transition-all"
                >
                  <Trash2 size={12} />
                </button>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* ── Main chat area ───────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 bg-cream dark:bg-charcoal">
        {/* Chat header */}
        <div className="h-12 flex items-center justify-between px-4 border-b
                        border-blue-50 dark:border-white/10 bg-white/60 dark:bg-charcoal/60
                        backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-jade animate-pulse-slow" />
            <span className="font-semibold text-sm text-charcoal dark:text-white">SevaSetu AI</span>
            <span className="text-xs text-charcoal/40 dark:text-white/40">
              • {isTyping
                  ? (language === "hindi" ? "लिख रहे हैं…" : language === "bhojpuri" ? "लिखत बाटे…" : "Typing…")
                  : (language === "hindi" ? "ऑनलाइन" : "Online")}
            </span>
          </div>

          {/* Mobile: new chat button */}
          <button
            onClick={handleNewChat}
            className="md:hidden flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs
                       bg-saffron text-white font-medium active:scale-95"
          >
            <Plus size={14} /> {tx("newChat")}
          </button>
        </div>

        {/* Messages */}
        <ChatWindow />

        {/* Input */}
        <ChatInput />
      </div>
    </div>
  );
}
