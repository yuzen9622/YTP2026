import { useCallback, useEffect, useMemo, useState } from "react";
import { SectionList, RefreshControl, View, Text } from "react-native";
import { Conversation } from "@/types";
import { useConversationStore } from "@/store/conversation-store";
import { useChatStore } from "@/store/chat-store";
import { useChatSearchStore } from "@/features/chat/store/chat-search-store";
import { useRouter } from "expo-router";
import { ChatHistoryHeader } from "./chat-history-header";
import { AIHeroCard } from "./ai-hero-card";
import { ConversationStatus } from "./category-chips";
import { ConversationCard } from "./conversation-card";
import { groupChatConversationsByDate } from "@/features/chat/utils/conversation-utils";
import { useUserStore } from "@/store/user-store";

export function ChatHistoryScreen() {
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
  const user = useUserStore((state) => state.user);
  const [activeStatus] = useState<ConversationStatus>("all");
  const [refreshing, setRefreshing] = useState(false);

  const searchIsActive = useChatSearchStore((state) => state.isActive);
  const searchResults = useChatSearchStore((state) => state.results);
  const searchIsLoading = useChatSearchStore((state) => state.isSearching);

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

  const displaySections = useMemo(() => {
    if (searchIsActive) {
      return searchResults.length > 0
        ? [{ title: "搜尋結果", data: searchResults }]
        : [];
    }
    return sections;
  }, [searchIsActive, searchResults, sections]);

  const renderSectionHeader = useCallback(
    ({ section }: { section: { title: string; data: Conversation[] } }) => {
      if (!section.data.length) return null;
      return (
        <View className="px-4 py-2 mt-2 bg-background">
          <Text className="text-[12px] font-bold uppercase tracking-wider text-muted-foreground/80">
            {section.title}
          </Text>
        </View>
      );
    },
    [],
  );

  const renderItem = useCallback(
    ({ item }: { item: Conversation }) => (
      <View className="py-1.5">
        <ConversationCard
          conversation={item}
          onPress={() => handleSelectConversation(item.id)}
          borderRadius={16}
        />
      </View>
    ),
    [handleSelectConversation],
  );

  const ListHeader = useMemo(
    () => (
      <>
        <ChatHistoryHeader
          userName={user?.name || "使用者"}
          totalConversations={conversations.length}
          unreadConversations={
            conversations.filter((c) => (c.unread || 0) > 0).length
          }
          isSearchActive={searchIsActive}
          searchResultCount={searchResults.length}
        />

        <AIHeroCard onNewChat={handleNewChat} />
      </>
    ),
    [conversations, searchIsActive, searchResults.length, handleNewChat, user],
  );

  const ListEmpty = useMemo(() => {
    if (searchIsActive) {
      return (
        <View className="items-center justify-center py-12">
          <Text className="text-muted-foreground text-[15px]">
            {searchIsLoading ? "搜尋中..." : "找不到符合的對話"}
          </Text>
        </View>
      );
    }
    return (
      <View className="items-center justify-center py-12">
        <Text className="text-muted-foreground text-[15px]">
          {isLoading ? "載入中..." : "沒有符合條件的紀錄"}
        </Text>
      </View>
    );
  }, [searchIsActive, searchIsLoading, isLoading]);

  return (
    <View className="flex-1 bg-background">
      <SectionList
        sections={displaySections}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        renderSectionHeader={renderSectionHeader}
        stickySectionHeadersEnabled={false}
        ListHeaderComponent={ListHeader}
        ListEmptyComponent={ListEmpty}
        onEndReached={searchIsActive ? undefined : onEndReached}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={{ paddingBottom: 100 }}
      />
    </View>
  );
}
