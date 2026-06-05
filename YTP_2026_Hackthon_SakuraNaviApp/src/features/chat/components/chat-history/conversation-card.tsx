import { memo, useMemo, useCallback } from "react";
import { Pressable, Text, View } from "react-native";
import { FileText } from "lucide-react-native";
import { ChatMessage, Conversation } from "@/types";
import { colors } from "@/lib/colors.ios";
import { formatTimeOnly } from "@/features/chat/utils/date-utils";

import { useChatStore } from "@/store/chat-store";

interface ConversationCardProps {
  conversation: Conversation;
  onPress: () => void;
  onLongPress?: () => void;
  borderRadius?: number;
}

const EMPTY_MESSAGES: ChatMessage[] = [];
const AI_HIDDEN_BLOCK_REGEX = /<(thing|think)\b[^>]*>[\s\S]*?<\/\1>/gi;
const AI_TAG_REGEX = /<\/?[^>]+>/g;

function toPreviewText(content?: string): string {
  if (!content) {
    return "新對話...";
  }

  const sanitized = content
    .replace(AI_HIDDEN_BLOCK_REGEX, "")
    .replace(AI_TAG_REGEX, "")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/```[\w-]*\n?/g, "")
    .replace(/```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^ {0,3}(#{1,6}\s*|>\s?)/gm, "")
    .replace(/^ {0,3}([-*+]\s+|\d+\.\s+)/gm, "")
    .replace(/(\*\*|__|\*|_|~~)/g, "")
    .replace(/\n/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  return sanitized || "新對話...";
}

export const ConversationCard = memo(function ConversationCard({
  conversation,
  onPress,
  onLongPress,
  borderRadius = 16,
}: ConversationCardProps) {
  const { title, messages = [], caseId } = conversation;
  const selectConversationMessages = useCallback(
    (state: { messages: Record<string, ChatMessage[]> }) =>
      state.messages[conversation.id],
    [conversation.id],
  );
  const newMessages = useChatStore(selectConversationMessages) ?? EMPTY_MESSAGES;
  const lastMessage = useMemo(() => {
    const latestNewMessage = newMessages[newMessages.length - 1];
    if (latestNewMessage?.content) {
      return latestNewMessage;
    }
    return messages[messages.length - 1];
  }, [messages, newMessages]);
  const lastMessageText = toPreviewText(lastMessage?.content);
  const lastMessageTime = lastMessage?.timestamp
    ? formatTimeOnly(lastMessage.timestamp)
    : "";

  const handlePress = useCallback(() => onPress(), [onPress]);
  const handleLongPress = useCallback(() => onLongPress?.(), [onLongPress]);

  return (
    <Pressable
      onPress={handlePress}
      onLongPress={handleLongPress}
      className="flex-col gap-2 p-4 mx-4 mb-3 bg-card active:opacity-80"
      style={{
        borderRadius,
        borderCurve: "continuous",
        shadowColor: "rgba(0,0,0,0.06)",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 1,
        shadowRadius: 6,
        elevation: 2,
      }}
    >
      {/* Row 2: title + unread */}
      <View className="flex-row items-center justify-between">
        <Text
          className="text-[17px] font-bold text-foreground flex-1 pr-2"
          numberOfLines={1}
        >
          {title}
        </Text>
        <Text className="text-[12px] font-medium text-muted-foreground shrink-0">
          {lastMessageTime}
        </Text>
      </View>

      {/* Row 3: AI marker + lastMsg */}
      <View className="flex-row items-start gap-1.5">
        <Text
          className="text-[14px] leading-5 text-muted-foreground flex-1"
          numberOfLines={1}
        >
          {lastMessageText}
        </Text>
      </View>

      {/* Row 4: status + caseId */}
      <View className="flex-row items-center justify-between mt-1">
        {caseId && (
          <View className="flex-row items-center gap-1">
            <FileText size={12} color={colors.mutedForeground} />
            <Text
              className="text-[12px] font-medium text-muted-foreground tracking-tight"
              style={{ fontFamily: "Menlo" }}
            >
              {caseId}
            </Text>
          </View>
        )}
      </View>
    </Pressable>
  );
});
