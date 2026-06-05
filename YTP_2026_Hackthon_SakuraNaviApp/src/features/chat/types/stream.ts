export interface StreamErrorEvent {
  code: number | string;
  message: string;
  retryable?: boolean;
}

export type StreamEvent =
  | { type: "text"; content: string }
  | { type: "tool_call"; tool: string; arguments: string }
  | { type: "tool_result"; tool: string; result: unknown }
  | { type: "done"; conversation_id: string; message_id?: string }
  | { type: "error"; code: number; message: string };

export interface StreamCallbackOptions {
  onToolCall?: (
    id: string,
    name: string,
    args: Record<string, unknown>,
  ) => void;
  onToolResult?: (name: string, result: unknown) => void;
  onError?: (message: string, detail?: StreamErrorEvent) => void;
  onConversationId?: (conversationId: string, messageId?: string) => void;
}
