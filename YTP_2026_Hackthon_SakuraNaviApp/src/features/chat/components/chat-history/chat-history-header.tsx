import { Text, View } from "react-native";

import { ChatSearch } from "./chat-search";

interface ChatHistoryHeaderProps {
  userName: string;
  totalConversations: number;
  unreadConversations: number;
  isSearchActive?: boolean;
  searchResultCount?: number;
}

export function ChatHistoryHeader({
  userName,
  totalConversations,
  unreadConversations,
  isSearchActive,
  searchResultCount,
}: ChatHistoryHeaderProps) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "早安" : hour < 18 ? "午安" : "晚安";

  return (
    <View className="flex-row items-center justify-between px-4 py-3">
      <View>
        <Text className="mb-1 text-sm font-medium text-muted-foreground">
          {greeting}，{userName}
        </Text>
        <Text className="mb-2 text-3xl font-bold text-foreground">
          對話紀錄
        </Text>
        <Text className="text-xs text-muted-foreground">
          {isSearchActive
            ? `${searchResultCount ?? 0} 則搜尋結果`
            : `共 ${totalConversations} 則對話`}
        </Text>
      </View>
      <ChatSearch />
    </View>
  );
}
