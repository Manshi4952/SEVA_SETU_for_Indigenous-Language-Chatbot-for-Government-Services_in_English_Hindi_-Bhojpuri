/**
 * store/useStore.js  –  Global Zustand state for SevaSetu.
 *
 * Slices:
 *   auth        – current user + JWT token
 *   chat        – active conversation, messages, loading
 *   settings    – language, mode (beginner/advanced), dark mode
 *   schemes     – cached scheme list
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "../utils/api";

const useStore = create(
  persist(
    (set, get) => ({
      // ── Auth ──────────────────────────────────────────────────────────────
      user:  null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        api.defaults.headers.common["Authorization"] = `Bearer ${data.access_token}`;
        set({ token: data.access_token, isAuthenticated: true,
              user: { id: data.user_id, role: data.role, preferred_lang: data.preferred_lang } });
        set({ language: data.preferred_lang });
        return data;
      },

      register: async (payload) => {
        const { data } = await api.post("/auth/register", payload);
        api.defaults.headers.common["Authorization"] = `Bearer ${data.access_token}`;
        set({ token: data.access_token, isAuthenticated: true,
              user: { id: data.user_id, role: data.role, preferred_lang: data.preferred_lang } });
        return data;
      },

      logout: () => {
        delete api.defaults.headers.common["Authorization"];
        set({ user: null, token: null, isAuthenticated: false,
              messages: [], activeConversationId: null });
      },

      // ── Settings ─────────────────────────────────────────────────────────
      language:  "hindi",
      mode:      "beginner",
      darkMode:  false,

      setLanguage: (lang) => set({ language: lang }),
      setMode:     (mode) => set({ mode }),
      toggleDark:  ()     => set((s) => ({ darkMode: !s.darkMode })),

      // ── Chat ─────────────────────────────────────────────────────────────
      messages:              [],
      activeConversationId:  null,
      conversations:         [],
      isTyping:              false,

      setActiveConversation: (id) => set({ activeConversationId: id, messages: [] }),

      loadConversations: async () => {
        const { data } = await api.get("/chat/conversations");
        set({ conversations: data });
      },

      loadMessages: async (convId) => {
        const { data } = await api.get(`/chat/conversations/${convId}`);
        set({ messages: data.messages, activeConversationId: convId });
      },

      sendMessage: async (text, voiceOutput = false) => {
        const { language, mode, activeConversationId } = get();

        // Optimistically add user message
        const tempMsg = {
          id: Date.now(), role: "user", content: text,
          language, created_at: new Date().toISOString(),
        };
        set((s) => ({ messages: [...s.messages, tempMsg], isTyping: true }));

        try {
          const { data } = await api.post("/chat/message", {
            message: text,
            language,
            mode,
            conversation_id: activeConversationId,
            voice_output: voiceOutput,
          });

          const botMsg = {
            id: data.message_id,
            role: "assistant",
            content: data.reply,
            language: data.language,
            retrieved_schemes: data.retrieved_schemes,
            audio_url: data.audio_url,
            created_at: new Date().toISOString(),
          };

          set((s) => ({
            messages: [...s.messages, botMsg],
            activeConversationId: data.conversation_id,
            isTyping: false,
          }));

          // Refresh conversation list
          get().loadConversations();
          return data;
        } catch (err) {
          set((s) => ({ isTyping: false,
            messages: s.messages.filter((m) => m.id !== tempMsg.id) }));
          throw err;
        }
      },

      clearChat: () => set({ messages: [], activeConversationId: null }),

      // ── Schemes ───────────────────────────────────────────────────────────
      schemes: [],
      loadSchemes: async () => {
        const { data } = await api.get("/schemes/");
        set({ schemes: data });
      },
    }),
    {
      name: "sevasetu-store",
      partialize: (s) => ({
        token: s.token,
        user:  s.user,
        isAuthenticated: s.isAuthenticated,
        language: s.language,
        mode:     s.mode,
        darkMode: s.darkMode,
      }),
    }
  )
);

export default useStore;
