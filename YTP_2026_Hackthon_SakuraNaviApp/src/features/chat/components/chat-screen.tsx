import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  InteractionManager,
  KeyboardAvoidingView,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Platform,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useShallow } from "zustand/react/shallow";
import { toast } from "sonner-native";

import { BlurView } from "expo-blur";

import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Text } from "@/components/ui/text";
import { useChat } from "../hooks/use-chat";
import { ChatInput } from "./chat-input";
import { MessageBubble } from "./message-bubble";
import { useConversationStore } from "@/store/conversation-store";
import type { ChatMessage } from "@/types";

const TOP_LOAD_THRESHOLD = 24;

export function ChatScreen() {
  const router = useRouter();

  const { conversationId: routeConversationId } = useLocalSearchParams<{
    conversationId?: string;
  }>();
  const insets = useSafeAreaInsets();
  const {
    messages,
    isStreaming,
    isHistoryLoading,
    hasMoreHistory,
    isLoadingMoreHistory,
    sendMessage,
    editMessage,
    deleteMessage,
    streamError,
    loadConversationMessages,
    loadOlderMessages,
  } = useChat();

  const {
    conversations,
    setCurrentConversation,
    currentConversationId,
    createConversation,
  } = useConversationStore(
    useShallow((state) => ({
      conversations: state.conversations,
      setCurrentConversation: state.setCurrentConversation,
      currentConversationId: state.currentConversationId,
      createConversation: state.createConversation,
    })),
  );
  const [input, setInput] = useState("");
  const listRef = useRef<FlatList>(null);
  const didInitialScrollRef = useRef(false);
  const followStreamRef = useRef(false);
  const listMetricsRef = useRef({
    offsetY: 0,
    contentHeight: 0,
  });
  const pendingPrependRef = useRef<{
    prevOffsetY: number;
    prevContentHeight: number;
  } | null>(null);

  const scrollToBottom = useCallback((animated: boolean) => {
    requestAnimationFrame(() => {
      listRef.current?.scrollToEnd({ animated });
    });
  }, []);

  const latestMessageSignature = (() => {
    const last = messages[messages.length - 1];
    if (!last) {
      return "";
    }

    return [
      messages.length,
      last.messageId,
      last.content.length,
      last.status ?? "",
      last.recommendations?.length ?? 0,
      last.sources?.length ?? 0,
    ].join(":");
  })();

  const quickSuggestions = [
    "我想找實習機會",
    "有適合新鮮人的補助嗎",
    "幫我規劃求職下一步",
  ];

  useEffect(() => {
    if (!routeConversationId) {
      return;
    }

    if (routeConversationId === "new") {
      const newConversationId = createConversation();
      router.replace(`/(chat-detail)/${newConversationId}`);
      return;
    }

    const exists = conversations.some((c) => c.id === routeConversationId);
    if (!exists) {
      const fallbackConversationId =
        currentConversationId ?? conversations[0]?.id ?? createConversation();
      router.replace(`/(chat-detail)/${fallbackConversationId}`);

      return;
    }

    if (currentConversationId !== routeConversationId) {
      setCurrentConversation(routeConversationId);
    }
  }, [
    createConversation,
    currentConversationId,
    routeConversationId,
    router,
    conversations,
    setCurrentConversation,
  ]);

  useEffect(() => {
    didInitialScrollRef.current = false;
    followStreamRef.current = false;
    pendingPrependRef.current = null;
    listMetricsRef.current = {
      offsetY: 0,
      contentHeight: 0,
    };
  }, [currentConversationId]);

  useEffect(() => {
    if (!latestMessageSignature) {
      return;
    }

    if (!followStreamRef.current) {
      return;
    }

    if (pendingPrependRef.current) {
      return;
    }

    const animated = didInitialScrollRef.current && !isStreaming;
    scrollToBottom(animated);
    didInitialScrollRef.current = true;
  }, [isStreaming, latestMessageSignature, scrollToBottom]);

  useEffect(() => {
    if (!isStreaming) {
      followStreamRef.current = false;
    }
  }, [isStreaming]);

  useEffect(() => {
    if (!isLoadingMoreHistory) {
      const pending = pendingPrependRef.current;
      if (
        pending &&
        listMetricsRef.current.contentHeight <= pending.prevContentHeight
      ) {
        pendingPrependRef.current = null;
      }
    }
  }, [isLoadingMoreHistory]);

  useEffect(() => {
    if (!currentConversationId) {
      return;
    }

    void loadConversationMessages(currentConversationId);
  }, [currentConversationId, loadConversationMessages]);

  useEffect(() => {
    if (didInitialScrollRef.current) {
      return;
    }

    if (messages.length === 0 || isHistoryLoading || isLoadingMoreHistory) {
      return;
    }

    if (pendingPrependRef.current) {
      return;
    }

    const task = InteractionManager.runAfterInteractions(() => {
      scrollToBottom(false);
      didInitialScrollRef.current = true;
    });

    return () => {
      task.cancel();
    };
  }, [
    isHistoryLoading,
    isLoadingMoreHistory,
    messages.length,
    scrollToBottom,
  ]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) {
      return;
    }

    setInput("");
    followStreamRef.current = true;
    scrollToBottom(false);
    await sendMessage(text);
  }, [input, isStreaming, scrollToBottom, sendMessage]);

  const handleSuggestPress = useCallback((text: string) => {
    setInput(text);
  }, []);

  const handleLoadOlderMessages = useCallback(() => {
    if (!currentConversationId) {
      return;
    }

    if (isHistoryLoading || isLoadingMoreHistory || !hasMoreHistory) {
      return;
    }

    if (pendingPrependRef.current) {
      return;
    }

    pendingPrependRef.current = {
      prevOffsetY: listMetricsRef.current.offsetY,
      prevContentHeight: listMetricsRef.current.contentHeight,
    };

    void loadOlderMessages(currentConversationId);
  }, [
    currentConversationId,
    hasMoreHistory,
    isHistoryLoading,
    isLoadingMoreHistory,
    loadOlderMessages,
  ]);

  const handleScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      listMetricsRef.current = {
        offsetY: event.nativeEvent.contentOffset.y,
        contentHeight: event.nativeEvent.contentSize.height,
      };

      if (event.nativeEvent.contentOffset.y <= TOP_LOAD_THRESHOLD) {
        handleLoadOlderMessages();
      }
    },
    [handleLoadOlderMessages],
  );

  const handleContentSizeChange = useCallback((_: number, height: number) => {
    listMetricsRef.current.contentHeight = height;

    const pendingPrepend = pendingPrependRef.current;
    if (pendingPrepend) {
      const delta = height - pendingPrepend.prevContentHeight;
      if (delta > 0) {
        listRef.current?.scrollToOffset({
          offset: Math.max(0, pendingPrepend.prevOffsetY + delta),
          animated: false,
        });
      }
      pendingPrependRef.current = null;
    }
  }, []);

  const handleMessageEdit = useCallback(
    (message: ChatMessage) => {
      const chainHint =
        "注意：這是連鎖操作，更新後會刪除這則訊息後面所有較新的訊息。";

      if (Platform.OS === "ios") {
        Alert.prompt(
          "編輯訊息",
          chainHint,
          [
            { text: "取消", style: "cancel" },
            {
              text: "更新",
              onPress: async (value?: string) => {
                const nextContent = value?.trim() ?? "";
                if (!nextContent) {
                  toast.error("請輸入訊息內容");
                  return;
                }

                if (nextContent === message.content.trim()) {
                  return;
                }

                try {
                  await editMessage(
                    message.conversationId,
                    message.id ?? message.messageId,
                    nextContent,
                  );
                  toast.success("訊息已更新");
                } catch (error) {
                  toast.error(
                    error instanceof Error ? error.message : "更新訊息失敗",
                  );
                }
              },
            },
          ],
          "plain-text",
          message.content,
        );
        return;
      }

      Alert.alert("編輯訊息", "此功能目前僅支援 iOS 裝置。");
    },
    [editMessage],
  );

  const handleMessageDelete = useCallback(
    (message: ChatMessage) => {
      Alert.alert(
        "刪除訊息",
        "注意：這是連鎖操作，刪除後會連同後面所有較新的訊息一起刪除。",
        [
          { text: "取消", style: "cancel" },
          {
            text: "刪除",
            style: "destructive",
            onPress: async () => {
              try {
                await deleteMessage(
                  message.conversationId,
                  message.id ?? message.messageId,
                );
                toast.success("訊息已刪除");
              } catch (error) {
                toast.error(
                  error instanceof Error ? error.message : "刪除訊息失敗",
                );
              }
            },
          },
        ],
      );
    },
    [deleteMessage],
  );

  const renderItem = useCallback(
    ({ item, index }: { item: (typeof messages)[0]; index: number }) => (
      <MessageBubble
        message={item}
        isStreaming={isStreaming && index === messages.length - 1}
        onSuggestPress={handleSuggestPress}
        onEditPress={handleMessageEdit}
        onDeletePress={handleMessageDelete}
      />
    ),
    [
      isStreaming,
      messages.length,
      handleSuggestPress,
      handleMessageEdit,
      handleMessageDelete,
    ],
  );

  const chatPane = (
    <KeyboardAvoidingView
      behavior={
        process.env.EXPO_OS === "ios"
          ? "padding"
          : Platform.OS === "ios"
            ? "padding"
            : "height"
      }
      className="flex-1"
      keyboardVerticalOffset={90}
    >
      {streamError && (
        <View className="px-3 py-2 mx-4 mt-2 border rounded-xl border-destructive/30 bg-destructive/10">
          <Text className="text-xs text-destructive">{streamError}</Text>
        </View>
      )}

      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.messageId}
        className="flex-1 max-h-full gap-1 px-3 space-y-2 overflow-auto"
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={{
          flexGrow: 1,
        }}
        ListHeaderComponent={
          isLoadingMoreHistory ? (
            <View className="items-center justify-center py-2">
              <ActivityIndicator size="small" />
            </View>
          ) : null
        }
        onContentSizeChange={handleContentSizeChange}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        renderItem={renderItem}
      />

      <BlurView intensity={80} tint="light">
        <View
          className="px-4 pt-1.5"
          style={{ paddingBottom: 12 + insets.bottom }}
        >
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isStreaming}
            suggestions={quickSuggestions}
          />
        </View>
      </BlurView>
    </KeyboardAvoidingView>
  );

  return (
    <>
      <View className="flex-1 h-full bg-background">{chatPane}</View>
    </>
  );
}
