import { useConversationStore } from "./conversation-store";
import type { Conversation } from "@/types";

export function usePinnedConversations(): Conversation[] {
  return useConversationStore((state) =>
    state.conversations.filter((c) => c.pinned),
  );
}

export function useActiveConversations(): Conversation[] {
  return useConversationStore((state) =>
    state.conversations.filter((c) => !c.pinned),
  );
}

export function useConversationById(id: string): Conversation | undefined {
  return useConversationStore((state) =>
    state.conversations.find((c) => c.id === id),
  );
}

export function useUnreadCount(): number {
  return useConversationStore((state) =>
    state.conversations.reduce((acc, c) => acc + (c.unread ?? 0), 0),
  );
}