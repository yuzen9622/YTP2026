import { create } from "zustand";
import type { Conversation } from "@/types";
import { searchConversations } from "@/features/chat/api/chat-api";

interface ChatSearchState {
  query: string;
  results: Conversation[];
  isSearching: boolean;
  error: string | null;
  total: number;
  offset: number;
  isActive: boolean;
}

interface ChatSearchAction {
  setQuery: (query: string) => void;
  search: (q: string) => Promise<void>;
  clearSearch: () => void;
  searchMore: () => Promise<void>;
}

type ChatSearchStore = ChatSearchState & ChatSearchAction;

export const useChatSearchStore = create<ChatSearchStore>((set, get) => ({
  query: "",
  results: [],
  isSearching: false,
  error: null,
  total: 0,
  offset: 0,
  isActive: false,

  setQuery: (query) => set({ query }),

  search: async (q) => {
    if (!q.trim()) {
      set({ results: [], isActive: false, error: null });
      return;
    }

    set({ isSearching: true, error: null, isActive: true });
    try {
      const response = await searchConversations(q, 20, 0);
      const results = response.items.map((item) => ({
        id: item.id,
        title: item.title,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
      set({
        results,
        total: response.total,
        offset: response.items.length,
        isSearching: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "搜尋失敗",
        isSearching: false,
      });
    }
  },

  clearSearch: () => {
    set({
      query: "",
      results: [],
      isSearching: false,
      error: null,
      total: 0,
      offset: 0,
      isActive: false,
    });
  },

  searchMore: async () => {
    const { query, offset, total, isSearching } = get();
    if (isSearching || offset >= total) return;

    set({ isSearching: true });
    try {
      const response = await searchConversations(query, 20, offset);
      const newResults = response.items.map((item) => ({
        id: item.id,
        title: item.title,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      }));
      set((state) => ({
        results: [...state.results, ...newResults],
        total: response.total,
        offset: offset + response.items.length,
        isSearching: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "搜尋失敗",
        isSearching: false,
      });
    }
  },
}));
