import { useMemo } from "react";
import { useChatStore } from "@/store/chat-store";
import { useConversationStore } from "@/store/conversation-store";

export function useChat() {
  const currentConversationId = useConversationStore((state) => state.currentConversationId);
  const createConversation = useConversationStore((state) => state.createConversation);
  const setCurrentConversation = useConversationStore((state) => state.setCurrentConversation);
  const messagesByConversation = useChatStore((state) => state.messages);
  const streamPhaseByConversation = useChatStore(
    (state) => state.streamPhaseByConversation,
  );
  const streamErrorByConversation = useChatStore(
    (state) => state.streamErrorByConversation,
  );
  const historyLoadingByConversation = useChatStore(
    (state) => state.historyLoadingByConversation,
  );
  const historyHasMoreByConversation = useChatStore(
    (state) => state.historyHasMoreByConversation,
  );
  const historyLoadingMoreByConversation = useChatStore(
    (state) => state.historyLoadingMoreByConversation,
  );
  const sendMessage = useChatStore((state) => state.sendMessage);
  const loadConversationMessages = useChatStore(
    (state) => state.loadConversationMessages,
  );
  const loadOlderMessages = useChatStore((state) => state.loadOlderMessages);
  const editMessage = useChatStore((state) => state.editMessage);
  const deleteMessage = useChatStore((state) => state.deleteMessage);

  const messages = useMemo(() => {
    if (!currentConversationId) {
      return [];
    }

    return messagesByConversation[currentConversationId] ?? [];
  }, [currentConversationId, messagesByConversation]);

  const streamPhase = currentConversationId
    ? (streamPhaseByConversation[currentConversationId] ?? "idle")
    : "idle";
  const streamError = currentConversationId
    ? (streamErrorByConversation[currentConversationId] ?? null)
    : null;
  const isStreaming =
    streamPhase === "requesting" || streamPhase === "streaming";
  const isHistoryLoading = currentConversationId
    ? (historyLoadingByConversation[currentConversationId] ?? false)
    : false;
  const hasMoreHistory = currentConversationId
    ? (historyHasMoreByConversation[currentConversationId] ?? true)
    : false;
  const isLoadingMoreHistory = currentConversationId
    ? (historyLoadingMoreByConversation[currentConversationId] ?? false)
    : false;

  function resetConversation() {
    const conversationId = createConversation();
    setCurrentConversation(conversationId);
  }

  return {
    conversationId: currentConversationId,
    messages,
    streamPhase,
    streamError,
    isStreaming,
    isHistoryLoading,
    hasMoreHistory,
    isLoadingMoreHistory,
    sendMessage,
    editMessage,
    deleteMessage,
    loadConversationMessages,
    loadOlderMessages,
    resetConversation,
  };
}
