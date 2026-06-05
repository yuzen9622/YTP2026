import { SafeAreaView } from "react-native-safe-area-context";
import { ChatHistoryScreen } from "@/features/chat/components/chat-history/chat-history-screen";

export default function ChatTabRoute() {
  return (
    <SafeAreaView className="flex-1 bg-background" edges={["top"]}>
      <ChatHistoryScreen />
    </SafeAreaView>
  );
}
