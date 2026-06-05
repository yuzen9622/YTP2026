import { memo, useMemo, useCallback } from "react";
import { Platform, View } from "react-native";
import type { ChatMessage } from "@/types";
import { Text } from "@/components/ui/text";
import { cn } from "@/lib/utils";
import { parseSuggestions } from "@/features/chat/utils/parse-suggestions";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuGroup,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Pencil, Trash2 } from "lucide-react-native";
import * as Haptics from "expo-haptics";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { SourceTag } from "./source-tag";
import { SuggestChip } from "./suggest-chip";
import { PolicyCardInline } from "./policy-card-inline";
import { ThinkingAccordion } from "./thinking-accordion";
import { MarkdownText } from "./markdown/markdown-text";

interface Props {
  message: ChatMessage;
  isStreaming?: boolean;
  onSuggestPress?: (text: string) => void;
  onEditPress?: (message: ChatMessage) => void;
  onDeletePress?: (message: ChatMessage) => void;
}

export const MessageBubble = memo(function MessageBubble({
  message,
  isStreaming,
  onSuggestPress,
  onEditPress,
  onDeletePress,
}: Props) {
  const isUser = message.role === "user";
  const insets = useSafeAreaInsets();

  const { cleanContent, suggestions, thinking } = useMemo(
    () =>
      isUser
        ? {
            cleanContent: message.content,
            suggestions: [],
            thinking: undefined,
          }
        : parseSuggestions(message.content),
    [isUser, message.content],
  );

  const handleSuggestPress = useCallback(
    (text: string) => {
      onSuggestPress?.(text);
    },
    [onSuggestPress],
  );

  const hasThinking = Boolean(thinking);
  const showThinking = !isUser && (hasThinking || Boolean(isStreaming));
  const hasBubbleContent = cleanContent.trim().length > 0;
  const contextMenuDisabled = !isUser || isStreaming;
  const contentInsets = useMemo(
    () => ({
      top: insets.top,
      bottom: insets.bottom,
      left: 12,
      right: 12,
    }),
    [insets.bottom, insets.top],
  );

  const handleLongPress = useCallback(() => {
    if (Platform.OS !== "web") {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  }, []);

  const bubbleContent = (
    <>
      {isUser ? (
        <Text
          selectable
          className={cn(
            "text-[15px] leading-[22px]",
            "text-primary-foreground",
          )}
        >
          {cleanContent}
        </Text>
      ) : (
        <MarkdownText content={cleanContent} />
      )}
    </>
  );

  const bubbleClassName = cn(
    "max-w-[80%] min-w-0 shrink self-start overflow-visible rounded-2xl px-3.5 py-2.5",
    isUser
      ? "self-end rounded-br-[4px] bg-primary"
      : "rounded-bl-[4px] bg-muted",
  );
  const bubble = isUser ? (
    <ContextMenu relativeTo="trigger">
      <ContextMenuTrigger
        disabled={contextMenuDisabled}
        onLongPress={handleLongPress}
        className={bubbleClassName}
      >
        {bubbleContent}
      </ContextMenuTrigger>
      <ContextMenuContent className="bg-background" sideOffset={10} insets={contentInsets}>
        <ContextMenuGroup>
          <ContextMenuItem onPress={() => onEditPress?.(message)}>
            <View className="flex-row items-center gap-3">
              <Pencil size={18} />
              <Text className="text-base text-accent-foreground">編輯訊息</Text>
            </View>
          </ContextMenuItem>

          <ContextMenuItem onPress={() => onDeletePress?.(message)}>
            <View className="flex-row items-center gap-3">
              <Trash2 size={18} color="#ff6b81" />
              <Text className="text-base text-[#ff6b81]">刪除訊息</Text>
            </View>
          </ContextMenuItem>
        </ContextMenuGroup>
      </ContextMenuContent>
    </ContextMenu>
  ) : (
    <View className={bubbleClassName}>{bubbleContent}</View>
  );

  return (
    <View
      className={cn(
        "gap-1.5 m-1 min-w-0",
        isUser ? "items-end" : "items-start",
      )}
    >
      {showThinking && (
        <ThinkingAccordion isStreaming={isStreaming} content={thinking} />
      )}

      {(isUser || hasBubbleContent) && bubble}

      {!isUser && (message.recommendations?.length ?? 0) > 0 && (
        <View className="w-full max-w-[92%] gap-2 px-1">
          {message.recommendations?.map((card) => (
            <PolicyCardInline key={card.policyId} policy={card} />
          ))}
        </View>
      )}

      {!isUser &&
        isStreaming &&
        (message.recommendations?.length ?? 0) === 0 && (
          <View className="w-full max-w-[92%] px-1">
            <View className="h-6 rounded-lg bg-muted/60" />
          </View>
        )}

      {!isUser && (message.sources?.length ?? 0) > 0 && (
        <View className="flex-row flex-wrap gap-1.5 px-1">
          {message.sources?.map((source) => (
            <SourceTag
              key={source.id ?? source.sourceId ?? source.title}
              source={source}
            />
          ))}
        </View>
      )}

      {!isUser && suggestions.length > 0 && onSuggestPress && (
        <View className="flex-row flex-wrap gap-1.5 px-1">
          {suggestions.map((suggestion) => (
            <SuggestChip
              key={suggestion}
              text={suggestion}
              onPress={() => handleSuggestPress(suggestion)}
            />
          ))}
        </View>
      )}
    </View>
  );
});
