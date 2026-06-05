import { ApiError, apiClient, refreshAccessTokenOnce } from "@/lib/api";
import { getAuthToken as getStoredAuthToken } from "@/lib/auth";
import { useUserStore } from "@/store/user-store";
import type { PolicySource } from "@/types";
import type {
  SendMessageRequest,
  StreamCallbackOptions,
  StreamEvent,
} from "../types";
import EventSource from "react-native-sse";
function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseToolArguments(rawArguments: string): unknown {
  try {
    return JSON.parse(rawArguments);
  } catch {
    return rawArguments;
  }
}

function toToolArgsRecord(parsedArguments: unknown): Record<string, unknown> {
  if (isObjectRecord(parsedArguments)) {
    return parsedArguments;
  }

  return { value: parsedArguments };
}

function extractArrayPayload(payload: unknown): unknown[] | null {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (!isObjectRecord(payload)) {
    return null;
  }

  const candidateKeys = [
    "result",
    "results",
    "sources",
    "recommendations",
    "policies",
    "items",
  ];

  for (const key of candidateKeys) {
    const candidate = payload[key];
    if (Array.isArray(candidate)) {
      return candidate;
    }
  }

  return null;
}

function isPolicySourceArray(payload: unknown): payload is PolicySource[] {
  return (
    Array.isArray(payload) &&
    payload.every(
      (item) =>
        isObjectRecord(item) &&
        typeof item.id === "string" &&
        typeof item.name === "string",
    )
  );
}

interface DispatchContext {
  onDelta: (delta: string) => void;
  onSources: (sources: PolicySource[]) => void;
  onDone: () => void;
  options?: StreamCallbackOptions;
  toolCallSequence: number;
}

type EventHandler<E extends StreamEvent> = (
  event: E,
  ctx: DispatchContext,
) => boolean;

function parseStreamEvent(
  type: string,
  chunk: Record<string, unknown>,
): StreamEvent | null {
  switch (type) {
    case "text":
      return typeof chunk.content === "string"
        ? { type: "text", content: chunk.content }
        : null;
    case "tool_call":
      return typeof chunk.tool === "string" &&
        typeof chunk.arguments === "string"
        ? { type: "tool_call", tool: chunk.tool, arguments: chunk.arguments }
        : null;
    case "tool_result":
      return typeof chunk.tool === "string"
        ? { type: "tool_result", tool: chunk.tool, result: chunk.result }
        : null;
    case "done":
      return typeof chunk.conversation_id === "string"
        ? {
            type: "done",
            conversation_id: chunk.conversation_id,
            message_id:
              typeof chunk.message_id === "string" ? chunk.message_id : undefined,
          }
        : null;
    case "error":
      return typeof chunk.message === "string"
        ? {
            type: "error",
            code: typeof chunk.code === "number" ? chunk.code : 0,
            message: chunk.message,
          }
        : null;
    default:
      return null;
  }
}

const eventHandlers: {
  [E in StreamEvent as E["type"]]: EventHandler<E>;
} = {
  text: ({ content }, { onDelta }) => {
    onDelta(content);
    return false;
  },
  tool_call: ({ tool, arguments: args }, ctx) => {
    ctx.toolCallSequence += 1;
    const id = `tool_${ctx.toolCallSequence.toString(36)}`;
    const parsed = parseToolArguments(args);
    ctx.options?.onToolCall?.(id, tool, toToolArgsRecord(parsed));
    if (tool === "recommend_policies") {
      const payload = extractArrayPayload(parsed);
      if (payload && isPolicySourceArray(payload)) {
        ctx.onSources(payload);
        ctx.options?.onToolResult?.(tool, payload);
      }
    }
    return false;
  },
  tool_result: ({ tool, result }, ctx) => {
    if (tool === "recommend_policies" && isPolicySourceArray(result)) {
      ctx.onSources(result);
    }
    ctx.options?.onToolResult?.(tool, result);
    return false;
  },
  done: ({ conversation_id, message_id }, { onDone, options }) => {
    options?.onConversationId?.(conversation_id, message_id);
    onDone();
    return true;
  },
  error: ({ code, message }, ctx) => {
    ctx.options?.onError?.(message, {
      code: code,
      message,
    });
    return true;
  },
};

function dispatchTypedStreamEvent(
  type: string,
  chunk: Record<string, unknown>,
  ctx: DispatchContext,
): boolean {
  const event = parseStreamEvent(type, chunk);
  if (!event) return false;
  return (eventHandlers[event.type] as EventHandler<typeof event>)(event, ctx);
}

function handleStreamDataPayload(raw: string, ctx: DispatchContext): boolean {
  if (!raw) return false;

  let chunk: StreamEvent;
  try {
    chunk = JSON.parse(raw) as StreamEvent;
  } catch {
    return false;
  }

  return dispatchTypedStreamEvent(chunk.type, chunk, ctx);
}

function getSseStatusCode(event: unknown): number | null {
  if (!isObjectRecord(event)) {
    return null;
  }

  const xhrStatus = Reflect.get(event, "xhrStatus");
  return typeof xhrStatus === "number" ? xhrStatus : null;
}

/**
 * 發送訊息（SSE 串流）
 * onDelta: 每次收到文字片段回呼
 * onSources: 收到來源清單時回呼（現為 tool_result 攜帶）
 * onDone: 串流結束時回呼
 */
export async function sendMessageStream(
  payload: SendMessageRequest,
  onDelta: (delta: string) => void,
  onSources: (sources: PolicySource[]) => void,
  onDone: () => void,
  options?: StreamCallbackOptions,
): Promise<void> {
  const ctx: DispatchContext = {
    onDelta,
    onSources,
    onDone,
    options,
    toolCallSequence: 0,
  };

  let hasRetriedAfterRefresh = false;

  while (true) {
    const token = await getStoredAuthToken();
    const shouldRetry = await new Promise<boolean>((resolve) => {
      let settled = false;
      let isRetrying = false;
      let isDoneEventHandled = false;

      const settle = (retry: boolean) => {
        if (settled) return;
        settled = true;
        resolve(retry);
      };

      const es = new EventSource(
        `${process.env.EXPO_PUBLIC_STREAM_URL}/chat/stream`,
        {
          method: "POST",
          headers: {
            Accept: "text/event-stream",
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(payload),
          pollingInterval: 0,
        },
      );

      es.addEventListener("open", () => {
        console.log("[chat-api] stream: connected");
      });

      es.addEventListener("message", (event) => {
        if (!event.data) return;
        const shouldStop = handleStreamDataPayload(event.data, ctx);
        if (shouldStop) {
          isDoneEventHandled = true;
          es.close();
          settle(false);
        }
      });

      es.addEventListener("error", async (event) => {
        console.log("[chat-api] stream error:", event);
        const statusCode = getSseStatusCode(event);

        if (statusCode === 401 && !hasRetriedAfterRefresh) {
          try {
            await refreshAccessTokenOnce();
            hasRetriedAfterRefresh = true;
            isRetrying = true;
            es.close();
            settle(true);
            return;
          } catch (error) {
            if (error instanceof ApiError && error.status === 401) {
              useUserStore.getState().clearSession();
            }
          }
        } else if (statusCode === 401 && hasRetriedAfterRefresh) {
          useUserStore.getState().clearSession();
        }

        const message =
          event.type === "error"
            ? `串流連線失敗（${event.message ?? "unknown"}）`
            : "串流連線失敗";
        options?.onError?.(message, {
          code: "STREAM_FETCH_ERROR",
          message,
        });
        es.close();
        settle(false);
      });

      es.addEventListener("close", () => {
        if (isRetrying) {
          settle(true);
          return;
        }

        if (!isDoneEventHandled) {
          onDone();
        }
        settle(false);
      });
    });

    if (!shouldRetry) {
      return;
    }
  }
}

export async function getConversationMessages(
  conversationId: string,
  limit = 50,
  beforeMessageId?: string,
) {
  return apiClient.get<
    | {
        items?: {
          id: string;
          conversation_id?: string;
          role: "user" | "assistant" | "tool";
          content: string;
          tool_name?: string;
          created_at: string;
        }[];
        messages?: {
          id: string;
          conversation_id?: string;
          role: "user" | "assistant" | "tool";
          content: string;
          tool_name?: string;
          created_at: string;
        }[];
        limit?: number;
        has_more?: boolean;
      }
    | {
        id: string;
        conversation_id?: string;
        role: "user" | "assistant" | "tool";
        content: string;
        tool_name?: string;
        created_at: string;
      }[]
  >(`/chat/conversations/${conversationId}/messages`, {
    params: {
      limit,
      before_message_id: beforeMessageId,
    },
  });
}

export async function getConversations(limit = 20, offset = 0) {
  return apiClient.get<{
    items: {
      id: string;
      title: string;
      created_at: string;
      updated_at: string;
    }[];
    total: number;
    limit: number;
    offset: number;
  }>("/chat/conversations", { params: { limit, offset } });
}

export async function searchConversations(q: string, limit = 20, offset = 0) {
  return apiClient.get<{
    items: {
      id: string;
      title: string;
      created_at: string;
      updated_at: string;
    }[];
    total: number;
    limit: number;
    offset: number;
  }>("/chat/conversations/search", { params: { q, limit, offset } });
}

export async function updateConversationTitle(
  conversationId: string,
  title: string,
) {
  return apiClient.patch<unknown>(`/chat/conversations/${conversationId}`, {
    title,
  });
}

export async function deleteConversationById(conversationId: string) {
  return apiClient.delete<unknown>(`/chat/conversations/${conversationId}`);
}

export async function updateConversationMessage(
  conversationId: string,
  messageId: string,
  content: string,
) {
  return apiClient.patch<unknown>(
    `/chat/conversations/${conversationId}/messages/${messageId}`,
    { content },
  );
}

export async function deleteConversationMessage(
  conversationId: string,
  messageId: string,
) {
  return apiClient.delete<unknown>(
    `/chat/conversations/${conversationId}/messages/${messageId}`,
  );
}
