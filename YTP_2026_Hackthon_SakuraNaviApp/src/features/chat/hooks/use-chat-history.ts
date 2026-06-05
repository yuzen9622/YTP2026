import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "expo-router";

import { useConversationStore } from "@/store/conversation-store";
import { useChatStore } from "@/store/chat-store";
import { groupChatConversationsByDate } from "@/features/chat/utils/conversation-utils";

import type { Conversation } from "@/types";
import type { ConversationStatus } from "../components/chat-history/category-chips";

interface UseChatHistoryReturn {
  conversations: Conversation[];
  total: number;
  offset: number;
  isLoading: boolean;
  isLoadingMore: boolean;
  refreshing: boolean;
  filteredConversations: Conversation[];
  sections: { title: string; data: Conversation[] }[];
  onRefresh: () => Promise<void>;
  onEndReached: () => void;
  handleNewChat: () => void;
  handleSelectConversation: (conversationId: string) => void;
}

export function useChatHistory(): UseChatHistoryReturn {
  const router = useRouter();

  const conversations = useConversationStore((state) => state.conversations);
  const total = useConversationStore((state) => state.total);
  const offset = useConversationStore((state) => state.offset);
  const isLoading = useConversationStore((state) => state.isLoading);
  const isLoadingMore = useConversationStore((state) => state.isLoadingMore);
  const createConversation = useConversationStore(
    (state) => state.createConversation,
  );
  const fetchConversations = useConversationStore(
    (state) => state.fetchConversations,
  );
  const fetchMoreConversations = useConversationStore(
    (state) => state.fetchMoreConversations,
  );
  const refreshConversations = useConversationStore(
    (state) => state.refreshConversations,
  );

  const [refreshing, setRefreshing] = useState(false);
  const [activeStatus] = useState<ConversationStatus>("all");

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshConversations();
    setRefreshing(false);
  }, [refreshConversations]);

  const onEndReached = useCallback(() => {
    if (!isLoadingMore && offset < total) {
      fetchMoreConversations();
    }
  }, [isLoadingMore, offset, total, fetchMoreConversations]);

  const handleNewChat = useCallback(() => {
    if (conversations.length > 0) {
      const latestConversation = [...conversations].sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      )[0];

      const messages = useChatStore.getState().messages[latestConversation.id];
      if (!messages || messages.length === 0) {
        router.push(`/(chat-detail)/${latestConversation.id}`);
        return;
      }
    }

    const conversationId = createConversation();
    router.push(`/(chat-detail)/${conversationId}`);
  }, [createConversation, router, conversations]);

  const handleSelectConversation = useCallback(
    (conversationId: string) => {
      router.push(`/(chat-detail)/${conversationId}`);
    },
    [router],
  );

  const filteredConversations = useMemo(() => {
    if (activeStatus === "all") return conversations;
    return conversations.filter((c) => (c.status || "active") === activeStatus);
  }, [conversations, activeStatus]);

  const sections = useMemo(
    () => groupChatConversationsByDate(filteredConversations),
    [filteredConversations],
  );

  return {
    conversations,
    total,
    offset,
    isLoading,
    isLoadingMore,
    refreshing,
    filteredConversations,
    sections,
    onRefresh,
    onEndReached,
    handleNewChat,
    handleSelectConversation,
  };
}