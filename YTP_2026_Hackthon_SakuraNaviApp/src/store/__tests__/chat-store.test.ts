const memoryStorage: Record<string, string> = {};
const mockSendMessageStream = jest.fn();
const mockGetConversationMessages = jest.fn();

jest.mock("@react-native-async-storage/async-storage", () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(async (key: string) => memoryStorage[key] ?? null),
    setItem: jest.fn(async (key: string, value: string) => {
      memoryStorage[key] = value;
    }),
    removeItem: jest.fn(async (key: string) => {
      delete memoryStorage[key];
    }),
  },
}));

jest.mock("expo-secure-store", () => ({
  __esModule: true,
  getItemAsync: jest.fn(async () => null),
  setItemAsync: jest.fn(async () => undefined),
  deleteItemAsync: jest.fn(async () => undefined),
}));

jest.mock("@/features/chat/api/chat-api", () => ({
  sendMessageStream: (...args: unknown[]) => mockSendMessageStream(...args),
  getConversationMessages: (...args: unknown[]) =>
    mockGetConversationMessages(...args),
  updateConversationMessage: jest.fn(),
  deleteConversationMessage: jest.fn(),
}));

import { useChatStore } from "../chat-store";
import { useConversationStore } from "../conversation-store";
import { useUserStore } from "../user-store";

function createBaseConversation() {
  const now = new Date().toISOString();
  return {
    id: "conversation-1",
    title: "新對話",
    createdAt: now,
    updatedAt: now,
    lastMessageAt: now,
    pinned: false,
  };
}

function createRemoteMessage(id: string, role: "user" | "assistant", createdAt: string) {
  return {
    id,
    role,
    content: `${role}-${id}`,
    created_at: createdAt,
  };
}

describe("chat-store", () => {
  beforeEach(() => {
    Object.keys(memoryStorage).forEach((key) => {
      delete memoryStorage[key];
    });

    mockSendMessageStream.mockReset();
    mockGetConversationMessages.mockReset();

    const conversation = createBaseConversation();
    useConversationStore.setState({
      conversations: [conversation],
      currentConversationId: conversation.id,
      isLoading: false,
      error: null,
    });

    useUserStore.setState({
      user: {
        id: "user-1",
        email: "test@example.com",
        name: "測試者",
        account: "test",
        bio: "",
        is_active: true,
      },
      token: null,
    });

    useChatStore.setState({
      messages: {},
      streamPhaseByConversation: {},
      streamErrorByConversation: {},
      historyLoadingByConversation: {},
      historyLoadedByConversation: {},
      historyHasMoreByConversation: {},
      historyLoadingMoreByConversation: {},
    });
  });

  it("sets hasMore from first page response", async () => {
    mockGetConversationMessages.mockResolvedValue({
      items: [
        createRemoteMessage("m-1", "user", "2024-01-01T00:00:00.000Z"),
        createRemoteMessage("m-2", "assistant", "2024-01-01T00:00:01.000Z"),
      ],
      has_more: true,
    });

    await useChatStore.getState().loadConversationMessages("conversation-1", {
      force: true,
    });

    const state = useChatStore.getState();
    expect(state.messages["conversation-1"]).toHaveLength(2);
    expect(state.historyHasMoreByConversation["conversation-1"]).toBe(true);
    expect(state.historyLoadingByConversation["conversation-1"]).toBe(false);
  });

  it("does not load older messages when hasMore is false", async () => {
    useChatStore.setState({
      messages: {
        "conversation-1": [
          {
            messageId: "m-3",
            id: "m-3",
            conversationId: "conversation-1",
            role: "user",
            content: "hello",
            timestamp: "2024-01-03T00:00:00.000Z",
            status: "done",
            sources: [],
            recommendations: [],
          },
        ],
      },
      historyHasMoreByConversation: {
        "conversation-1": false,
      },
    });

    await useChatStore.getState().loadOlderMessages("conversation-1");

    expect(mockGetConversationMessages).not.toHaveBeenCalled();
  });

  it("does not load older messages when loadingMore is already in progress", async () => {
    useChatStore.setState({
      messages: {
        "conversation-1": [
          {
            messageId: "m-3",
            id: "m-3",
            conversationId: "conversation-1",
            role: "user",
            content: "hello",
            timestamp: "2024-01-03T00:00:00.000Z",
            status: "done",
            sources: [],
            recommendations: [],
          },
        ],
      },
      historyHasMoreByConversation: {
        "conversation-1": true,
      },
      historyLoadingMoreByConversation: {
        "conversation-1": true,
      },
    });

    await useChatStore.getState().loadOlderMessages("conversation-1");

    expect(mockGetConversationMessages).not.toHaveBeenCalled();
  });

  it("prepends older messages without duplicates and updates hasMore", async () => {
    useChatStore.setState({
      messages: {
        "conversation-1": [
          {
            messageId: "m-3",
            id: "m-3",
            conversationId: "conversation-1",
            role: "user",
            content: "m-3",
            timestamp: "2024-01-03T00:00:00.000Z",
            status: "done",
            sources: [],
            recommendations: [],
          },
          {
            messageId: "m-4",
            id: "m-4",
            conversationId: "conversation-1",
            role: "assistant",
            content: "m-4",
            timestamp: "2024-01-04T00:00:00.000Z",
            status: "done",
            sources: [],
            recommendations: [],
          },
        ],
      },
      historyHasMoreByConversation: {
        "conversation-1": true,
      },
    });

    mockGetConversationMessages.mockResolvedValue({
      items: [
        createRemoteMessage("m-2", "assistant", "2024-01-02T00:00:00.000Z"),
        createRemoteMessage("m-3", "user", "2024-01-03T00:00:00.000Z"),
      ],
      has_more: false,
    });

    await useChatStore.getState().loadOlderMessages("conversation-1");

    expect(mockGetConversationMessages).toHaveBeenCalledWith(
      "conversation-1",
      50,
      "m-3",
    );

    const messageIds = useChatStore
      .getState()
      .messages["conversation-1"].map((item) => item.messageId);

    expect(messageIds).toEqual(["m-2", "m-3", "m-4"]);
    expect(useChatStore.getState().historyHasMoreByConversation["conversation-1"]).toBe(
      false,
    );
    expect(
      useChatStore.getState().historyLoadingMoreByConversation["conversation-1"],
    ).toBe(false);
  });

  it("sends message and attaches streamed delta/recommendations/sources", async () => {
    mockSendMessageStream.mockImplementation(
      async (
        _payload,
        onDelta: (delta: string) => void,
        onSources: (sources: unknown[]) => void,
        onDone: () => void,
        options?: { onToolResult?: (name: string, result: unknown) => void },
      ) => {
        onDelta("這是串流回覆");
        options?.onToolResult?.("recommend_policies", [
          {
            policyId: "policy-1",
            title: "青年就業旗艦計畫",
            summary: "協助青年提升就業能力",
            tags: ["就業"],
            reason: "符合你的求職背景",
            category: "training",
            deadline: null,
            applyUrl: "https://example.com/apply",
            sourceDocUrl: "https://example.com/doc",
          },
        ]);
        onSources([
          {
            id: "source-1",
            name: "勞動部",
            url: "https://example.com/source",
          },
        ]);
        onDone();
      },
    );

    await useChatStore.getState().sendMessage("我想找工作補助");

    const conversationId = useConversationStore.getState()
      .currentConversationId as string;
    const messages = useChatStore.getState().messages[conversationId];

    expect(messages).toHaveLength(2);
    expect(messages[0].role).toBe("user");
    expect(messages[0].content).toBe("我想找工作補助");

    expect(messages[1].role).toBe("assistant");
    expect(messages[1].content).toContain("這是串流回覆");
    expect(messages[1].status).toBe("done");
    expect(messages[1].recommendations?.[0]?.policyId).toBe("policy-1");
    expect(messages[1].sources?.[0]?.id).toBe("source-1");
    expect(useChatStore.getState().streamPhaseByConversation[conversationId]).toBe(
      "done",
    );
  });

  it("marks stream as error when API fails", async () => {
    mockSendMessageStream.mockRejectedValue(new Error("network down"));

    await useChatStore.getState().sendMessage("測試錯誤");

    const conversationId = useConversationStore.getState()
      .currentConversationId as string;
    const messages = useChatStore.getState().messages[conversationId];

    expect(messages).toHaveLength(2);
    expect(messages[1].status).toBe("error");
    expect(useChatStore.getState().streamPhaseByConversation[conversationId]).toBe(
      "error",
    );
    expect(useChatStore.getState().streamErrorByConversation[conversationId]).toBe(
      "network down",
    );
  });

  it("binds backend message_id from done event to the latest user message", async () => {
    mockSendMessageStream.mockImplementation(
      async (
        _payload,
        onDelta: (delta: string) => void,
        _onSources: (sources: unknown[]) => void,
        onDone: () => void,
        options?: {
          onConversationId?: (conversationId: string, messageId?: string) => void;
        },
      ) => {
        onDelta("收到回覆");
        options?.onConversationId?.("conversation-1", "message-remote-1");
        onDone();
      },
    );

    await useChatStore.getState().sendMessage("我要編輯這則訊息");

    const conversationId = useConversationStore.getState()
      .currentConversationId as string;
    const messages = useChatStore.getState().messages[conversationId];

    expect(messages[0].role).toBe("user");
    expect(messages[0].id).toBe("message-remote-1");
  });
});
