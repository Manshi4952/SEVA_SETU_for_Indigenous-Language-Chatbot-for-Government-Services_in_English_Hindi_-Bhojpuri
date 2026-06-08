/**
 * store/useStore.js  –  Zustand global state (v3)
 *
 * Fixes:
 *  - sendMessage now keeps user message in UI after bot reply (was overwriting)
 *  - addMessage / setTyping helpers for optimistic UI
 *  - activeConversationId tracked per session
 *  - Race condition fix when switching chats
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "../utils/api";

const useStore = create(
  persist(
    (set, get) => ({
      // ── Auth ──────────────────────────────────────────────────────────────
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const res = await api.post("/auth/login", { email, password });
        const { access_token, user_id, role, preferred_lang } = res.data;
        set({
          token: access_token,
          isAuthenticated: true,
          user: { id: user_id, role, preferred_lang },
          language: preferred_lang || "hindi",
        });
      },

      register: async (payload) => {
        const res = await api.post("/auth/register", payload);
        const { access_token, user_id, role, preferred_lang } = res.data;
        set({
          token: access_token,
          isAuthenticated: true,
          user: { id: user_id, role, preferred_lang },
          language: preferred_lang || "hindi",
        });
      },

      logout: () =>
        set({
          user: null, token: null, isAuthenticated: false,
          messages: [], conversations: [], activeConversationId: null,
        }),

      // ── Chat ──────────────────────────────────────────────────────────────
      messages: [],
      conversations: [],
      activeConversationId: null,
      isTyping: false,
      isLoadingHistory: false,

      setTyping: (val) => set({ isTyping: val }),

      addMessage: (msg) =>
        set((s) => ({ messages: [...s.messages, msg] })),

      setMessages: (msgs) => set({ messages: msgs }),

      clearMessages: () => set({ messages: [], activeConversationId: null }),

      sendMessage: async (text, language, mode, voiceOutput = false) => {
        const convId = get().activeConversationId;

        // Optimistically add the user message to UI
        const tempId = `temp-${Date.now()}`;
        const tempUserMsg = {
          id: tempId,
          role: "user",
          content: text,
          language,
          created_at: new Date().toISOString(),
          _temp: true,
        };
        set((s) => ({ messages: [...s.messages, tempUserMsg], isTyping: true }));

        try {
          const res = await api.post("/chat/message", {
            message: text,
            language,
            mode,
            conversation_id: convId || undefined,
            voice_output: voiceOutput,
          });

          const { reply, language: detectedLang, conversation_id,
                  retrieved_schemes, audio_url } = res.data;

          // Replace temp user msg with confirmed version, then add bot reply
          const confirmedUserMsg = {
            id: `user-${Date.now()}`,
            role: "user",
            content: text,
            language,
            created_at: new Date().toISOString(),
          };

          const botMsg = {
            id: `bot-${Date.now()}`,
            role: "assistant",
            content: reply,
            language: detectedLang,
            retrieved_schemes: retrieved_schemes || [],
            audio_url,
            created_at: new Date().toISOString(),
          };

          set((s) => ({
            // Keep all non-temp messages, then append confirmed user msg + bot reply
            messages: [
              ...s.messages.filter((m) => !m._temp),
              confirmedUserMsg,
              botMsg,
            ],
            activeConversationId: conversation_id,
            isTyping: false,
          }));

          // Refresh conversation list silently
          get().loadConversations();

          return botMsg;
        } catch (err) {
          // On error: remove temp msg, show error toast handled by caller
          set((s) => ({
            messages: s.messages.filter((m) => !m._temp),
            isTyping: false,
          }));
          throw err;
        }
      },

      loadConversations: async () => {
        if (!get().isAuthenticated) return;
        try {
          const res = await api.get("/chat/conversations");
          set({ conversations: res.data });
        } catch (_) {}
      },

      loadConversation: async (convId) => {
        set({
          messages: [],
          isLoadingHistory: true,
          activeConversationId: convId,
        });
        try {
          const res = await api.get(`/chat/conversations/${convId}`);
          set({ messages: res.data.messages, isLoadingHistory: false });
        } catch (_) {
          set({ isLoadingHistory: false });
        }
      },

      deleteConversation: async (convId) => {
        await api.delete(`/chat/conversations/${convId}`);
        set((s) => ({
          conversations: s.conversations.filter((c) => c.id !== convId),
          messages: s.activeConversationId === convId ? [] : s.messages,
          activeConversationId: s.activeConversationId === convId ? null : s.activeConversationId,
        }));
      },

      // ── Schemes ───────────────────────────────────────────────────────────
      schemes: [],
      loadSchemes: async (lang = "hindi") => {
        try {
          const res = await api.get(`/schemes/?language=${lang}&limit=100`);
          set({ schemes: res.data });
        } catch (_) {}
      },

      // ── UI prefs ──────────────────────────────────────────────────────────
      language: "hindi",
      setLanguage: (lang) => set({ language: lang }),

      darkMode: false,
      toggleDark: () => set((s) => ({ darkMode: !s.darkMode })),
    }),
    {
      name: "sevasetu-store",
      partialize: (s) => ({
        token: s.token,
        user: s.user,
        isAuthenticated: s.isAuthenticated,
        language: s.language,
        darkMode: s.darkMode,
      }),
    }
  )
);

export default useStore;
