import { Alert, Platform, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { Stack } from "expo-router/stack";
import { toast } from "sonner-native";

import { useChatStore } from "@/store/chat-store";
import { useConversationStore } from "@/store/conversation-store";
import { ChartNoAxesGantt } from "lucide-react-native";
import { Button, Host, Menu, Section, Text, Toggle } from "@expo/ui/swift-ui";
import { buttonStyle, labelStyle } from "@expo/ui/swift-ui/modifiers";
import { NoIndexHead } from "@/lib/seo";

export default function ChatDetailLayout() {
  const router = useRouter();
  const conversations = useConversationStore((state) => state.conversations);
  const currentConversationId = useConversationStore(
    (state) => state.currentConversationId,
  );
  const renameConversationRemote = useConversationStore(
    (state) => state.renameConversationRemote,
  );
  const deleteConversationRemote = useConversationStore(
    (state) => state.deleteConversationRemote,
  );
  const clearMessagesByConversation = useChatStore(
    (state) => state.clearMessagesByConversation,
  );

  function resolveTitle(conversationId?: string) {
    const targetConversationId = conversationId ?? currentConversationId;
    if (!targetConversationId) {
      return "新對話";
    }

    const matched = conversations.find((c) => c.id === targetConversationId);
    return matched?.title ?? "新對話";
  }

  function handleRenameConversation(conversationId?: string) {
    if (!conversationId) {
      return;
    }

    const currentTitle = resolveTitle(conversationId);
    const submitRename = async (rawTitle?: string) => {
      const nextTitle = rawTitle?.trim() ?? "";

      if (!nextTitle) {
        toast.error("請輸入對話標題");
        return;
      }

      if (nextTitle === currentTitle) {
        return;
      }

      try {
        await renameConversationRemote(conversationId, nextTitle);
        toast.success("對話標題已更新");
      } catch {
        // API interceptor handles toasts
      }
    };

    if (Platform.OS === "ios") {
      Alert.prompt(
        "更新對話標題",
        "請輸入新的標題",
        [
          { text: "取消", style: "cancel" },
          {
            text: "更新",
            onPress: (value?: string) => {
              void submitRename(value);
            },
          },
        ],
        "plain-text",
        currentTitle,
      );
      return;
    }

    Alert.alert("更新對話標題", "此功能目前僅支援 iOS 裝置。");
  }

  function handleDeleteConversation(conversationId?: string) {
    if (!conversationId) {
      return;
    }

    const currentTitle = resolveTitle(conversationId);

    Alert.alert("刪除對話", `確定要刪除「${currentTitle}」嗎？`, [
      { text: "取消", style: "cancel" },
      {
        text: "刪除",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteConversationRemote(conversationId);
            clearMessagesByConversation(conversationId);
            toast.success("對話已刪除");

            const nextConversationId =
              useConversationStore.getState().currentConversationId;

            if (nextConversationId) {
              router.replace(`/(chat-detail)/${nextConversationId}`);
            } else {
              router.replace("/(tabs)/chat");
            }
          } catch {
            // API interceptor handles toasts
          }
        },
      },
    ]);
  }

  return (
    <>
      <NoIndexHead />
      <Stack
        screenOptions={{
          headerBackVisible: false,
          headerBackButtonDisplayMode: "minimal",
        }}
      >
        <Stack.Screen
          name="[conversationId]"
          options={({ route }) => {
            const params = route.params as
              | { conversationId?: string }
              | undefined;
            const routeConversationId =
              typeof params?.conversationId === "string"
                ? params.conversationId
                : undefined;

            return {
              title: resolveTitle(routeConversationId),

              headerLeft: () => (
                <Pressable
                  onPress={() => router.back()}
                  accessibilityRole="button"
                  accessibilityLabel="返回聊天列表"
                  style={{ paddingHorizontal: 10, paddingVertical: 10 }}
                >
                  <ChartNoAxesGantt />
                </Pressable>
              ),
              headerRight: () => {
                const targetConversationId =
                  routeConversationId ?? currentConversationId ?? undefined;

                return (
                  <Host matchContents>
                    <Menu
                      label=""
                      modifiers={[labelStyle("iconOnly"), buttonStyle("plain")]}
                      systemImage="ellipsis"
                    >
                      <Section title={resolveTitle(targetConversationId)}>
                        <Toggle isOn={false} onIsOnChange={() => {}}>
                          <Text>真人客服</Text>
                        </Toggle>
                        <Button
                          label="更新對話標題"
                          systemImage="square.and.pencil"
                          onPress={() =>
                            handleRenameConversation(targetConversationId)
                          }
                        />
                        <Button
                          label="刪除對話"
                          role="destructive"
                          systemImage="trash"
                          onPress={() =>
                            handleDeleteConversation(targetConversationId)
                          }
                        />
                      </Section>
                    </Menu>
                  </Host>
                );
              },
            };
          }}
        />
      </Stack>
    </>
  );
}
