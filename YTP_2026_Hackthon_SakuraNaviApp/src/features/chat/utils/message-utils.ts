import type { ChatMessage, PolicyCard } from "@/types";

export function generateMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `msg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export function normalizePolicyCard(card: PolicyCard): PolicyCard {
  return {
    ...card,
    category: card.category ?? "subsidy",
    reason: card.reason ?? "依你的對話脈絡推薦",
    deadline: card.deadline ?? null,
    applyUrl: card.applyUrl ?? "",
    sourceDocUrl: card.sourceDocUrl ?? "",
  };
}

export function upsertMessage(
  current: Record<string, ChatMessage[]>,
  conversationId: string,
  updater: (messages: ChatMessage[]) => ChatMessage[],
): Record<string, ChatMessage[]> {
  const messages = current[conversationId] ?? [];
  return {
    ...current,
    [conversationId]: updater(messages),
  };
}

export function updateLastAssistant(
  messages: ChatMessage[],
  updater: (message: ChatMessage) => ChatMessage,
): ChatMessage[] {
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