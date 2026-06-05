import { create } from "zustand";
import type {
  ChatMessage,
  PolicyCard,
  PolicySource,
  StreamPhase,
} from "@/types";
import {
  deleteConversationMessage,
  getConversationMessages,
  sendMessageStream,
  updateConversationMessage,
} from "@/features/chat/api/chat-api";
import {
  ensureConversationExists,
  useConversationStore,
} from "@/store/conversation-store";
import { useUserStore } from "@/store/user-store";

interface ChatState {
  messages: Record<string, ChatMessage[]>;
  streamPhaseByConversation: Record<string, StreamPhase>;
  streamErrorByConversation: Record<string, string | null>;
  historyLoadingByConversation: Record<string, boolean>;
  historyLoadedByConversation: Record<string, boolean>;
  historyHasMoreByConversation: Record<string, boolean>;
  historyLoadingMoreByConversation: Record<string, boolean>;
}

interface ChatAction {
  loadConversationMessages: (
    conversationId: string,
    options?: { force?: boolean },
  ) => Promise<void>;
  loadOlderMessages: (conversationId: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  appendMessage: (msg: ChatMessage) => void;
  appendDelta: (conversationId: string, delta: string) => void;
  attachRecommendations: (conversationId: string, cards: PolicyCard[]) => void;
  attachSources: (conversationId: string, sources: PolicySource[]) => void;
  markStreamDone: (conversationId: string) => void;
  markStreamError: (conversationId: string, message: string) => void;
  clearMessagesByConversation: (conversationId: string) => void;
  editMessage: (
    conversationId: string,
    messageId: string,
    content: string,
  ) => Promise<void>;
  deleteMessage: (conversationId: string, messageId: string) => Promise<void>;
}

type ChatStore = ChatState & ChatAction;

function generateMessageId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `msg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function normalizePolicyCard(card: PolicyCard): PolicyCard {
  return {
    ...card,
    category: card.category ?? "subsidy",
    reason: card.reason ?? "依你的對話脈絡推薦",
    deadline: card.deadline ?? null,
    applyUrl: card.applyUrl ?? "",
    sourceDocUrl: card.sourceDocUrl ?? "",
  };
}

function upsertMessage(
  current: Record<string, ChatMessage[]>,
  conversationId: string,
  updater: (messages: ChatMessage[]) => ChatMessage[],
) {
  const messages = current[conversationId] ?? [];
  return {
    ...current,
    [conversationId]: updater(messages),
  };
}

function updateLastAssistant(
  messages: ChatMessage[],
  updater: (message: ChatMessage) => ChatMessage,
) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === "assistant") {
      return [
        ...messages.slice(0, index),
        updater(messages[index]),
        ...messages.slice(index + 1),
      ];
    }
  }

  return messages;
}

function updateLastUser(
  messages: ChatMessage[],
  updater: (message: ChatMessage) => ChatMessage,
) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === "user") {
      return [
        ...messages.slice(0, index),
        updater(messages[index]),
        ...messages.slice(index + 1),
      ];
    }
  }

  return messages;
}

function findMessageIndex(messages: ChatMessage[], messageId: string) {
  return messages.findIndex(
    (message) => message.id === messageId || message.messageId === messageId,
  );
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toConversationMessageArray(
  payload: unknown,
): Array<Record<string, unknown>> {
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

function extractConversationPage(payload: unknown) {
  const items = toConversationMessageArray(payload);
  const fallbackHasMore = items.length >= 50;
  if (!isObjectRecord(payload)) {
    return {
      items,
      hasMore: fallbackHasMore,
    };
  }

  const rawHasMore = payload.has_more ?? payload.hasMore;
  return {
    items,
    hasMore: typeof rawHasMore === "boolean" ? rawHasMore : fallbackHasMore,
  };
}

function mapRemoteMessagesToChatMessages(
  items: Array<Record<string, unknown>>,
  conversationId: string,
): ChatMessage[] {
  const mapped: ChatMessage[] = [];

  for (const item of items) {
    const role = item.role;
    if (role !== "user" && role !== "assistant") {
      continue;
    }

    const content =
      typeof item.content === "string"
        ? item.content
        : String(item.content ?? "");
    const rawTimestamp =
      typeof item.created_at === "string"
        ? item.created_at
        : typeof item.timestamp === "string"
          ? item.timestamp
          : new Date().toISOString();
    const id =
      typeof item.id === "string" && item.id.length > 0
        ? item.id
        : generateMessageId();

    mapped.push({
      messageId: id,
      id,
      conversationId,
      role,
      content,
      timestamp: rawTimestamp,
      status: "done",
      sources: [],
      recommendations: [],
    });
  }

  return mapped.sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp, "en", { sensitivity: "base" }),
  );
}

function getMessageCursor(message?: ChatMessage) {
  if (!message) {
    return null;
  }

  return message.id ?? message.messageId ?? null;
}

function prependDedupedMessages(
  existingMessages: ChatMessage[],
  incomingMessages: ChatMessage[],
) {
  if (incomingMessages.length === 0) {
    return existingMessages;
  }

  const existingKeys = new Set(
    existingMessages.map((item) => item.id ?? item.messageId),
  );
  const uniqueIncoming = incomingMessages.filter((item) => {
    const key = item.id ?? item.messageId;
    if (existingKeys.has(key)) {
      return false;
    }

    existingKeys.add(key);
    return true;
  });

  return [...uniqueIncoming, ...existingMessages];
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  messages: {},
  streamPhaseByConversation: {},
  streamErrorByConversation: {},
  historyLoadingByConversation: {},
  historyLoadedByConversation: {},
  historyHasMoreByConversation: {},
  historyLoadingMoreByConversation: {},

  loadConversationMessages: async (conversationId, options) => {
    if (!conversationId || conversationId.startsWith("conversation_")) {
      return;
    }

    const { force = false } = options ?? {};
    const state = get();

    if (state.historyLoadingByConversation[conversationId]) {
      return;
    }

    if (!force && state.historyLoadedByConversation[conversationId]) {
      return;
    }

    if (!force && (state.messages[conversationId]?.length ?? 0) > 0) {
      set((prev) => ({
        historyLoadedByConversation: {
          ...prev.historyLoadedByConversation,
          [conversationId]: true,
        },
        historyHasMoreByConversation: {
          ...prev.historyHasMoreByConversation,
          [conversationId]:
            prev.historyHasMoreByConversation[conversationId] ?? true,
        },
      }));
      return;
    }

    set((prev) => ({
      historyLoadingByConversation: {
        ...prev.historyLoadingByConversation,
        [conversationId]: true,
      },
      streamErrorByConversation: {
        ...prev.streamErrorByConversation,
        [conversationId]: null,
      },
    }));

    try {
      const response = await getConversationMessages(conversationId);
      const page = extractConversationPage(response);
      const history = mapRemoteMessagesToChatMessages(
        page.items,
        conversationId,
      );

      set((prev) => {
        const hasLocalMessages = (prev.messages[conversationId]?.length ?? 0) > 0;
        const shouldReplace = force || !hasLocalMessages;

        return {
          messages: shouldReplace
            ? {
                ...prev.messages,
                [conversationId]: history,
              }
            : prev.messages,
          historyLoadingByConversation: {
            ...prev.historyLoadingByConversation,
            [conversationId]: false,
          },
          historyLoadedByConversation: {
            ...prev.historyLoadedByConversation,
            [conversationId]: true,
          },
          historyHasMoreByConversation: {
            ...prev.historyHasMoreByConversation,
            [conversationId]: page.hasMore,
          },
          streamErrorByConversation: {
            ...prev.streamErrorByConversation,
            [conversationId]: null,
          },
        };
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "載入歷史訊息失敗";
      set((prev) => ({
        historyLoadingByConversation: {
          ...prev.historyLoadingByConversation,
          [conversationId]: false,
        },
        streamErrorByConversation: {
          ...prev.streamErrorByConversation,
          [conversationId]: message,
        },
      }));
    }
  },

  loadOlderMessages: async (conversationId) => {
    if (!conversationId || conversationId.startsWith("conversation_")) {
      return;
    }

    const state = get();
    if (
      state.historyLoadingByConversation[conversationId] ||
      state.historyLoadingMoreByConversation[conversationId]
    ) {
      return;
    }

    if (state.historyHasMoreByConversation[conversationId] === false) {
      return;
    }

    const currentMessages = state.messages[conversationId] ?? [];
    const oldestMessage = currentMessages[0];
    const cursor = getMessageCursor(oldestMessage);

    if (!cursor) {
      set((prev) => ({
        historyHasMoreByConversation: {
          ...prev.historyHasMoreByConversation,
          [conversationId]: false,
        },
      }));
      return;
    }

    set((prev) => ({
      historyLoadingMoreByConversation: {
        ...prev.historyLoadingMoreByConversation,
        [conversationId]: true,
      },
      streamErrorByConversation: {
        ...prev.streamErrorByConversation,
        [conversationId]: null,
      },
    }));

    try {
      const response = await getConversationMessages(conversationId, 50, cursor);
      const page = extractConversationPage(response);
      const olderHistory = mapRemoteMessagesToChatMessages(
        page.items,
        conversationId,
      );

      set((prev) => {
        const existingMessages = prev.messages[conversationId] ?? [];
        return {
          messages: {
            ...prev.messages,
            [conversationId]: prependDedupedMessages(
              existingMessages,
              olderHistory,
            ),
          },
          historyLoadingMoreByConversation: {
            ...prev.historyLoadingMoreByConversation,
            [conversationId]: false,
          },
          historyLoadedByConversation: {
            ...prev.historyLoadedByConversation,
            [conversationId]: true,
          },
          historyHasMoreByConversation: {
            ...prev.historyHasMoreByConversation,
            [conversationId]: page.hasMore,
          },
          streamErrorByConversation: {
            ...prev.streamErrorByConversation,
            [conversationId]: null,
          },
        };
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "載入歷史訊息失敗";
      set((prev) => ({
        historyLoadingMoreByConversation: {
          ...prev.historyLoadingMoreByConversation,
          [conversationId]: false,
        },
        streamErrorByConversation: {
          ...prev.streamErrorByConversation,
          [conversationId]: message,
        },
      }));
    }
  },

  appendMessage: (msg) => {
    set((state) => ({
      messages: upsertMessage(
        state.messages,
        msg.conversationId,
        (messages) => [...messages, msg],
      ),
    }));
  },

  appendDelta: (conversationId, delta) => {
    if (!delta) {
      return;
    }

    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) =>
        updateLastAssistant(messages, (message) => ({
          ...message,
          content: `${message.content}${delta}`,
          status: "streaming",
        })),
      ),
      streamPhaseByConversation: {
        ...state.streamPhaseByConversation,
        [conversationId]: "streaming",
      },
      streamErrorByConversation: {
        ...state.streamErrorByConversation,
        [conversationId]: null,
      },
    }));
  },

  attachRecommendations: (conversationId, cards) => {
    const normalizedCards = cards.map((item) => normalizePolicyCard(item));

    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) =>
        updateLastAssistant(messages, (message) => ({
          ...message,
          recommendations: normalizedCards,
        })),
      ),
    }));
  },

  attachSources: (conversationId, sources) => {
    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) =>
        updateLastAssistant(messages, (message) => ({
          ...message,
          sources,
        })),
      ),
    }));
  },

  markStreamDone: (conversationId) => {
    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) =>
        updateLastAssistant(messages, (message) => ({
          ...message,
          status: "done",
        })),
      ),
      streamPhaseByConversation: {
        ...state.streamPhaseByConversation,
        [conversationId]: "done",
      },
      streamErrorByConversation: {
        ...state.streamErrorByConversation,
        [conversationId]: null,
      },
    }));
  },

  markStreamError: (conversationId, message) => {
    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) =>
        updateLastAssistant(messages, (item) => ({
          ...item,
          status: "error",
          content: item.content || "目前服務暫時忙碌，請稍後再試。",
        })),
      ),
      streamPhaseByConversation: {
        ...state.streamPhaseByConversation,
        [conversationId]: "error",
      },
      streamErrorByConversation: {
        ...state.streamErrorByConversation,
        [conversationId]: message,
      },
    }));
  },

  clearMessagesByConversation: (conversationId) => {
    set((state) => {
      const nextMessages = { ...state.messages };
      delete nextMessages[conversationId];

      const nextPhase = { ...state.streamPhaseByConversation };
      delete nextPhase[conversationId];

      const nextError = { ...state.streamErrorByConversation };
      delete nextError[conversationId];
      const nextHistoryLoading = { ...state.historyLoadingByConversation };
      delete nextHistoryLoading[conversationId];
      const nextHistoryLoaded = { ...state.historyLoadedByConversation };
      delete nextHistoryLoaded[conversationId];
      const nextHistoryHasMore = { ...state.historyHasMoreByConversation };
      delete nextHistoryHasMore[conversationId];
      const nextHistoryLoadingMore = {
        ...state.historyLoadingMoreByConversation,
      };
      delete nextHistoryLoadingMore[conversationId];

      return {
        messages: nextMessages,
        streamPhaseByConversation: nextPhase,
        streamErrorByConversation: nextError,
        historyLoadingByConversation: nextHistoryLoading,
        historyLoadedByConversation: nextHistoryLoaded,
        historyHasMoreByConversation: nextHistoryHasMore,
        historyLoadingMoreByConversation: nextHistoryLoadingMore,
      };
    });
  },

  editMessage: async (conversationId, messageId, content) => {
    const nextContent = content.trim();
    if (!nextContent) {
      return;
    }

    const state = get();
    const currentMessages = state.messages[conversationId] ?? [];
    const targetIndex = findMessageIndex(currentMessages, messageId);
    if (targetIndex < 0) {
      return;
    }

    const targetMessage = currentMessages[targetIndex];

    if (!conversationId.startsWith("conversation_")) {
      const remoteMessageId = targetMessage.id;
      if (!remoteMessageId) {
        throw new Error("訊息尚未同步，請稍後再試");
      }

      await updateConversationMessage(conversationId, remoteMessageId, nextContent);
    }

    set((prev) => ({
      messages: upsertMessage(prev.messages, conversationId, (messages) =>
        messages
          .slice(0, targetIndex + 1)
          .map((message, index) =>
            index === targetIndex
              ? {
                  ...message,
                  content: nextContent,
                  status: "done",
                }
              : message,
          ),
      ),
      streamPhaseByConversation: {
        ...prev.streamPhaseByConversation,
        [conversationId]: "done",
      },
      streamErrorByConversation: {
        ...prev.streamErrorByConversation,
        [conversationId]: null,
      },
    }));

    if (!conversationId.startsWith("conversation_")) {
      await get().loadConversationMessages(conversationId, { force: true });
    }
  },

  deleteMessage: async (conversationId, messageId) => {
    const state = get();
    const currentMessages = state.messages[conversationId] ?? [];
    const targetIndex = findMessageIndex(currentMessages, messageId);
    if (targetIndex < 0) {
      return;
    }

    const targetMessage = currentMessages[targetIndex];

    if (!conversationId.startsWith("conversation_")) {
      const remoteMessageId = targetMessage.id;
      if (!remoteMessageId) {
        throw new Error("訊息尚未同步，請稍後再試");
      }

      await deleteConversationMessage(conversationId, remoteMessageId);
    }

    set((prev) => ({
      messages: upsertMessage(prev.messages, conversationId, (messages) =>
        messages.slice(0, targetIndex),
      ),
      streamPhaseByConversation: {
        ...prev.streamPhaseByConversation,
        [conversationId]: "done",
      },
      streamErrorByConversation: {
        ...prev.streamErrorByConversation,
        [conversationId]: null,
      },
    }));

    if (!conversationId.startsWith("conversation_")) {
      await get().loadConversationMessages(conversationId, { force: true });
    }
  },

  sendMessage: async (text) => {
    const content = text.trim();
    if (!content) {
      return;
    }

    const { user } = useUserStore.getState();
    if (!user?.id) {
      return;
    }

    const conversationId = ensureConversationExists();
    const { touchConversation, renameConversation, conversations } =
      useConversationStore.getState();
    const now = new Date().toISOString();

    const userMessage: ChatMessage = {
      messageId: generateMessageId(),
      conversationId,
      role: "user",
      content,
      timestamp: now,
      status: "done",
      sources: [],
      recommendations: [],
    };

    const assistantMessage: ChatMessage = {
      messageId: generateMessageId(),
      conversationId,
      role: "assistant",
      content: "",
      timestamp: now,
      status: "streaming",
      sources: [],
      recommendations: [],
    };

    set((state) => ({
      messages: upsertMessage(state.messages, conversationId, (messages) => [
        ...messages,
        userMessage,
        assistantMessage,
      ]),
      streamPhaseByConversation: {
        ...state.streamPhaseByConversation,
        [conversationId]: "requesting",
      },
      streamErrorByConversation: {
        ...state.streamErrorByConversation,
        [conversationId]: null,
      },
    }));

    const currentConversation = conversations.find(
      (item) => item.id === conversationId,
    );

    const isLocalConversation = conversationId.startsWith("conversation_");

    const serverConversationId = isLocalConversation ? null : conversationId;

    if (currentConversation && currentConversation.title === "新對話") {
      renameConversation(conversationId, content.slice(0, 18));
    }

    touchConversation(conversationId, now);

    try {
      await sendMessageStream(
        {
          message: content,
          conversation_id: serverConversationId,
        },
        (delta) => {
          get().appendDelta(conversationId, delta);
        },
        (sources) => {
          get().attachSources(conversationId, sources);
        },
        () => {
          get().markStreamDone(conversationId);
          touchConversation(conversationId);
        },
        {
          onToolResult: (name, result) => {
            if (name === "recommend_policies" && Array.isArray(result)) {
              get().attachRecommendations(
                conversationId,
                result as PolicyCard[],
              );
            }
          },
          onError: (message) => {
            get().markStreamError(conversationId, message);
            touchConversation(conversationId);
          },
          onConversationId: (newId, messageId) => {
            if (messageId) {
              set((state) => ({
                messages: upsertMessage(state.messages, conversationId, (messages) =>
                  updateLastUser(messages, (message) => ({
                    ...message,
                    id: messageId,
                  })),
                ),
              }));
            }

            if (isLocalConversation && newId && newId !== conversationId) {
              useConversationStore
                .getState()
                .replaceConversationId(conversationId, newId);
            }
          },
        },
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "訊息傳送失敗";
      get().markStreamError(conversationId, message);
      touchConversation(conversationId);
    }
  },
}));
