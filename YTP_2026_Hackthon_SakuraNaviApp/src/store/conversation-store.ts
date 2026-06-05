import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { ChatMessage, Conversation } from "@/types";

const STORAGE_KEY = "sakura.conversations.v3";

interface ConversationState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;
  total: number;
  offset: number;
}

interface ConversationAction {
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (id: string) => void;
  createConversation: (seedTitle?: string) => string;
  renameConversation: (id: string, title: string) => void;
  deleteConversation: (id: string) => void;
  renameConversationRemote: (id: string, title: string) => Promise<void>;
  deleteConversationRemote: (id: string) => Promise<void>;
  touchConversation: (id: string, updatedAt?: string) => void;
  replaceConversationId: (oldId: string, newId: string) => void;
  togglePinConversation: (id: string) => void;
  fetchConversations: () => Promise<void>;
  fetchMoreConversations: () => Promise<void>;
  refreshConversations: () => Promise<void>;
}

type ConversationStore = ConversationState & ConversationAction;

type ConversationGroup = {
  today: Conversation[];
  yesterday: Conversation[];
  older: Conversation[];
};

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toConversationMessageArray(payload: unknown): Array<Record<string, unknown>> {
  if (Array.isArray(payload)) {
    return payload.filter(isObjectRecord);
  }

  if (!isObjectRecord(payload)) {
    return [];
  }

  const candidates = ["items", "messages", "data", "results"];
  for (const key of candidates) {
    const candidate = payload[key];
    if (Array.isArray(candidate)) {
      return candidate.filter(isObjectRecord);
    }
  }

  return [];
}

function mapToPreviewMessage(
  payload: unknown,
  conversationId: string,
): ChatMessage | undefined {
  const items = toConversationMessageArray(payload);
  if (items.length === 0) {
    return undefined;
  }

  const raw = items[items.length - 1];
  const role = raw.role;
  if (role !== "user" && role !== "assistant") {
    return undefined;
  }

  const content =
    typeof raw.content === "string" ? raw.content : String(raw.content ?? "");
  const rawTimestamp =
    typeof raw.created_at === "string"
      ? raw.created_at
      : typeof raw.timestamp === "string"
        ? raw.timestamp
        : new Date().toISOString();
  const id =
    typeof raw.id === "string" && raw.id.length > 0
      ? raw.id
      : `${conversationId}_${rawTimestamp}`;

  return {
    messageId: id,
    id,
    conversationId,
    role,
    content,
    timestamp: rawTimestamp,
    status: "done",
    sources: [],
    recommendations: [],
  };
}

async function attachConversationPreviews(conversations: Conversation[]) {
  const { getConversationMessages } = await import("@/features/chat/api/chat-api");

  const previews = await Promise.allSettled(
    conversations.map(async (conversation) => {
      if (conversation.id.startsWith("conversation_")) {
        return { id: conversation.id, preview: undefined as ChatMessage | undefined };
      }

      const payload = await getConversationMessages(conversation.id, 1);
      return {
        id: conversation.id,
        preview: mapToPreviewMessage(payload, conversation.id),
      };
    }),
  );

  const previewMap = new Map<string, ChatMessage | undefined>();
  previews.forEach((result) => {
    if (result.status === "fulfilled") {
      previewMap.set(result.value.id, result.value.preview);
    }
  });

  return conversations.map((conversation) => {
    const preview = previewMap.get(conversation.id);
    return {
      ...conversation,
      lastMessageAt: preview?.timestamp ?? conversation.lastMessageAt ?? conversation.updatedAt,
      messages: preview ? [preview] : [],
    };
  });
}

function generateConversationId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `conversation_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeConversation(input: Partial<Conversation>): Conversation {
  const now = new Date().toISOString();
  const createdAt = input.createdAt ?? now;
  const updatedAt = input.updatedAt ?? input.lastMessageAt ?? createdAt;

  return {
    id: input.id ?? generateConversationId(),
    title: input.title?.trim() ? input.title : "新對話",
    createdAt,
    updatedAt,
    pinned: input.pinned,
    lastMessageAt: input.lastMessageAt,
    unread: input.unread,
    status: input.status,
    topic: input.topic,
    caseId: input.caseId,
  };
}

function sortConversations(conversations: Conversation[]) {
  return [...conversations].sort((a, b) => {
    if (Boolean(a.pinned) !== Boolean(b.pinned)) {
      return a.pinned ? -1 : 1;
    }

    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
}

function createDefaultConversation(seedTitle?: string): Conversation {
  const now = new Date().toISOString();
  const conversationId = generateConversationId();

  return {
    id: conversationId,
    title: seedTitle?.trim() ? seedTitle : "新對話",
    createdAt: now,
    updatedAt: now,
    pinned: false,
  };
}

function getDateKey(iso: string) {
  const date = new Date(iso);
  return new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  ).getTime();
}

export function groupConversationsByDate(conversations: Conversation[]): ConversationGroup {
  const groups: ConversationGroup = { today: [], yesterday: [], older: [] };
  const now = new Date();
  const todayKey = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const yesterdayKey = todayKey - 24 * 60 * 60 * 1000;

  conversations.forEach((conversation) => {
    const key = getDateKey(conversation.updatedAt || conversation.createdAt);

    if (key === todayKey) {
      groups.today.push(conversation);
      return;
    }

    if (key === yesterdayKey) {
      groups.yesterday.push(conversation);
      return;
    }

    groups.older.push(conversation);
  });

  groups.today = sortConversations(groups.today);
  groups.yesterday = sortConversations(groups.yesterday);
  groups.older = sortConversations(groups.older);

  return groups;
}

export const useConversationStore = create<ConversationStore>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      isLoadingMore: false,
      error: null,
      total: 0,
      offset: 0,

      setConversations: (conversations) => {
        const normalized = sortConversations(
          conversations.map((item) => normalizeConversation(item)),
        );

        set((state) => ({
          conversations: normalized,
          currentConversationId:
            state.currentConversationId &&
            normalized.some((item) => item.id === state.currentConversationId)
              ? state.currentConversationId
              : (normalized[0]?.id ?? null),
          error: null,
        }));
      },

      setCurrentConversation: (id) => {
        const exists = get().conversations.some((item) => item.id === id);
        if (!exists) {
          return;
        }

        set({ currentConversationId: id });
      },

      createConversation: (seedTitle) => {
        const conversation = createDefaultConversation(seedTitle);

        set((state) => ({
          conversations: sortConversations([conversation, ...state.conversations]),
          currentConversationId: conversation.id,
          error: null,
        }));

        return conversation.id;
      },

      renameConversation: (id, title) => {
        const nextTitle = title.trim();
        if (!nextTitle) {
          return;
        }

        set((state) => ({
          conversations: state.conversations.map((conversation) =>
            conversation.id === id ? { ...conversation, title: nextTitle } : conversation,
          ),
        }));
      },

      deleteConversation: (id) => {
        const state = get();
        const remaining = state.conversations.filter((conversation) => conversation.id !== id);

        if (remaining.length === 0) {
          const conversation = createDefaultConversation();
          set({
            conversations: [conversation],
            currentConversationId: conversation.id,
            error: null,
          });
          return;
        }

        const sortedRemaining = sortConversations(remaining);
        const currentConversationId =
          state.currentConversationId === id
            ? sortedRemaining[0].id
            : (state.currentConversationId ?? sortedRemaining[0].id);

        set({ conversations: sortedRemaining, currentConversationId, error: null });
      },

      renameConversationRemote: async (id, title) => {
        const nextTitle = title.trim();
        if (!nextTitle) {
          return;
        }

        if (id.startsWith("conversation_")) {
          get().renameConversation(id, nextTitle);
          return;
        }

        const { updateConversationTitle } = await import("@/features/chat/api/chat-api");
        await updateConversationTitle(id, nextTitle);
        get().renameConversation(id, nextTitle);
      },

      deleteConversationRemote: async (id) => {
        if (id.startsWith("conversation_")) {
          get().deleteConversation(id);
          return;
        }

        const { deleteConversationById } = await import("@/features/chat/api/chat-api");
        await deleteConversationById(id);
        get().deleteConversation(id);
      },

      touchConversation: (id, updatedAt) => {
        const nextUpdatedAt = updatedAt ?? new Date().toISOString();

        set((state) => ({
          conversations: sortConversations(
            state.conversations.map((conversation) =>
              conversation.id === id
                ? {
                    ...conversation,
                    updatedAt: nextUpdatedAt,
                    lastMessageAt: nextUpdatedAt,
                  }
                : conversation,
            ),
          ),
        }));
      },

      replaceConversationId: (oldId: string, newId: string) => {
        set((state) => ({
          conversations: state.conversations.map((conversation) =>
            conversation.id === oldId ? { ...conversation, id: newId } : conversation,
          ),
          currentConversationId:
            state.currentConversationId === oldId ? newId : state.currentConversationId,
        }));
      },

      togglePinConversation: (id) => {
        set((state) => ({
          conversations: sortConversations(
            state.conversations.map((conversation) =>
              conversation.id === id
                ? {
                    ...conversation,
                    pinned: !conversation.pinned,
                  }
                : conversation,
            ),
          ),
        }));
      },

      fetchConversations: async () => {
        set({ isLoading: true, error: null });
        try {
          const { getConversations } = await import("@/features/chat/api/chat-api");
          const response = await getConversations(20, 0);
          const conversations = response.items.map((item) => ({
            id: item.id,
            title: item.title,
            createdAt: item.created_at,
            updatedAt: item.updated_at,
          }));
          const conversationsWithPreview =
            await attachConversationPreviews(conversations);
          set({
            conversations: conversationsWithPreview,
            total: response.total,
            offset: response.items.length,
            isLoading: false,
          });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "載入失敗",
            isLoading: false,
          });
        }
      },

      fetchMoreConversations: async () => {
        const { offset, total, conversations } = get();
        if (offset >= total) return;
        set({ isLoadingMore: true });
        try {
          const { getConversations } = await import("@/features/chat/api/chat-api");
          const response = await getConversations(20, offset);
          const newConversations = response.items.map((item) => ({
            id: item.id,
            title: item.title,
            createdAt: item.created_at,
            updatedAt: item.updated_at,
          }));
          const newConversationsWithPreview =
            await attachConversationPreviews(newConversations);
          set({
            conversations: [...conversations, ...newConversationsWithPreview],
            total: response.total,
            offset: offset + response.items.length,
            isLoadingMore: false,
          });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "載入失敗",
            isLoadingMore: false,
          });
        }
      },

      refreshConversations: async () => {
        set({ offset: 0, error: null });
        try {
          const { getConversations } = await import("@/features/chat/api/chat-api");
          const response = await getConversations(20, 0);
          const conversations = response.items.map((item) => ({
            id: item.id,
            title: item.title,
            createdAt: item.created_at,
            updatedAt: item.updated_at,
          }));
          const conversationsWithPreview =
            await attachConversationPreviews(conversations);
          set({
            conversations: conversationsWithPreview,
            total: response.total,
            offset: response.items.length,
          });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : "載入失敗",
          });
        }
      },
    }),
    {
      name: STORAGE_KEY,
      version: 5,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
      }),
      migrate: (persistedState) => {
        const rawState = persistedState as Partial<ConversationStore> | undefined;
        const normalizedConversations = sortConversations(
          (rawState?.conversations ?? []).map((item) => normalizeConversation(item)),
        );

        if (normalizedConversations.length === 0) {
          const conversation = createDefaultConversation();

          return {
            conversations: [conversation],
            currentConversationId: conversation.id,
            isLoading: false,
            error: null,
          } as unknown as ConversationStore;
        }

        const currentConversationId =
          rawState?.currentConversationId &&
          normalizedConversations.some(
            (conversation) => conversation.id === rawState.currentConversationId,
          )
            ? rawState.currentConversationId
            : normalizedConversations[0].id;

        return {
          conversations: normalizedConversations,
          currentConversationId,
          isLoading: false,
          error: null,
        } as unknown as ConversationStore;
      },
      onRehydrateStorage: () => (state) => {
        if (!state) {
          return;
        }

        const normalizedConversations = sortConversations(
          (state.conversations ?? []).map((item) => normalizeConversation(item)),
        );

        if (normalizedConversations.length === 0) {
          const conversation = createDefaultConversation();
          state.conversations = [conversation];
          state.currentConversationId = conversation.id;
          return;
        }

        state.conversations = normalizedConversations;

        if (
          !state.currentConversationId ||
          !normalizedConversations.some(
            (conversation) => conversation.id === state.currentConversationId,
          )
        ) {
          state.currentConversationId = normalizedConversations[0].id;
        }
      },
    },
  ),
);

export function ensureConversationExists() {
  const { conversations, currentConversationId, createConversation } =
    useConversationStore.getState();

  if (conversations.length === 0 || !currentConversationId) {
    return createConversation();
  }

  return currentConversationId;
}
