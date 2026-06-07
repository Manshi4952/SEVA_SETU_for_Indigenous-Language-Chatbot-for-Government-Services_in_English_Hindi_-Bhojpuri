/**
 * pages/ChatPage.jsx  –  Full-page chat interface with sidebar.
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, MessageSquare, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import { t } from "../utils/i18n";
import api from "../utils/api";
import clsx from "clsx";

function ConversationItem({ conv, isActive, onClick, onDelete }) {
  return (
    <div
      className={clsx(
        "group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all",
        isActive
          ? "bg-ashoka text-white shadow-glow-blue"
          : "hover:bg-blue-50 dark:hover:bg-white/5 text-charcoal/70 dark:text-white/70"
      )}
      onClick={onClick}
    >
      <MessageSquare size={14} className="flex-shrink-0" />
      <span className="flex-1 text-sm truncate">{conv.title}</span>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
        className={clsx(
          "opacity-0 group-hover:opacity-100 p-1 rounded transition-all",
          isActive ? "hover:bg-white/20" : "hover:bg-red-50 hover:text-red-500"
        )}
      >
        <Trash2 size={12} />
      </button>
    </div>
  );
}

export default function ChatPage() {
  const {
    isAuthenticated, language,
    conversations, loadConversations,
    activeConversationId, setActiveConversation, loadMessages,
    clearChat,
  } = useStore();
  const navigate = useNavigate();
  const tx = (key) => t(key, language);

  useEffect(() => {
    if (!isAuthenticated) { navigate("/login"); return; }
    loadConversations().catch(() => {});
  }, [isAuthenticated]);

  const handleNewChat = () => {
    clearChat();
    toast("✨ New conversation started");
  };

  const handleSelect = async (conv) => {
    if (conv.id === activeConversationId) return;
    try {
      await loadMessages(conv.id);
    } catch {
      toast.error("Failed to load conversation");
    }
  };

  const handleDelete = async (convId) => {
    try {
      await api.delete(`/chat/conversations/${convId}`);
      if (convId === activeConversationId) clearChat();
      await loadConversations();
      toast.success("Deleted");
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="flex h-[calc(100vh-57px)]">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="hidden md:flex flex-col w-64 border-r border-blue-50 dark:border-white/10
                        bg-white/60 dark:bg-charcoal/60 p-3 gap-2 overflow-y-auto flex-shrink-0">
        <button
          onClick={handleNewChat}
          className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-saffron text-white
                     font-medium text-sm hover:bg-saffron-dark shadow-glow transition-all"
        >
          <Plus size={16} /> {tx("newChat")}
        </button>

        <p className="text-xs text-charcoal/40 dark:text-white/40 px-1 mt-2 uppercase tracking-wider font-semibold">
          {tx("chatHistory")}
        </p>

        {conversations.length === 0 ? (
          <p className="text-xs text-charcoal/30 dark:text-white/30 text-center mt-8 px-4">
            {language === "hindi" ? "अभी तक कोई बातचीत नहीं" : "No conversations yet"}
          </p>
        ) : (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conv={conv}
              isActive={conv.id === activeConversationId}
              onClick={() => handleSelect(conv)}
              onDelete={handleDelete}
            />
          ))
        )}
      </aside>

      {/* ── Chat area ───────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-blue-50 dark:border-white/10
                        bg-white/80 dark:bg-charcoal/80 backdrop-blur-md">
          <div className="w-2 h-2 rounded-full bg-jade animate-pulse" />
          <span className="text-sm font-medium text-charcoal dark:text-white">SevaSetu AI</span>
          <span className="text-xs text-charcoal/40 dark:text-white/40">● Online</span>
          <div className="flex-1" />
          <span className="text-xs px-2 py-0.5 rounded-full bg-ashoka/10 text-ashoka font-medium">
            {tx(useStore.getState().mode)}
          </span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4">
          <ChatWindow />
        </div>

        {/* Input */}
        <ChatInput />
      </div>
    </div>
  );
}
