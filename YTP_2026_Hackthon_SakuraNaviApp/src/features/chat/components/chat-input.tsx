import { useCallback, useEffect } from "react";
import {
  Platform,
  Pressable,
  TextInputKeyPressEvent,
  View,
} from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { Send } from "lucide-react-native";
import { Input } from "@/components/ui/input";

interface ChatInputProps {
  value: string;
  disabled?: boolean;
  suggestions?: string[];
  onChange: (value: string) => void;
  onSend: () => void;
}

export function ChatInput({
  value,
  disabled,
  suggestions = [],
  onChange,
  onSend,
}: ChatInputProps) {
  const canSend = value.trim().length > 0 && !disabled;

  const handleSend = useCallback(
    (event: TextInputKeyPressEvent) => {
      if (Platform.OS !== "web") {
        return;
      }

      const nativeEvent = (
        event as { nativeEvent?: { key?: string; shiftKey?: boolean } }
      ).nativeEvent;
      if (nativeEvent?.key === "Enter" && !nativeEvent.shiftKey && canSend) {
        onSend();
      }
    },
    [canSend, onSend],
  );

  return (
    <View className="gap-2 ">
      <View className="relative justify-end">
        <Input
          testID="chat-input"
          value={value}
          onChangeText={onChange}
          placeholder="輸入你的問題..."
          multiline
          onKeyPress={handleSend}
          className="h-auto max-h-32 min-h-11 rounded-[22px] border-0 bg-muted pl-4 pr-12 py-2.5 text-[15px]"
        />

        <SendButton
          visible={canSend}
          onPress={onSend}
          testID="chat-send-button"
        />
      </View>
    </View>
  );
}

interface SendButtonProps {
  visible: boolean;
  onPress: () => void;
  testID?: string;
}

function SendButton({ visible, onPress, testID }: SendButtonProps) {
  const progress = useSharedValue(visible ? 1 : 0);

  useEffect(() => {
    progress.value = withTiming(visible ? 1 : 0, { duration: 180 });
  }, [progress, visible]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [{ scale: 0.5 + progress.value * 0.5 }],
  }));

  return (
    <Animated.View
      pointerEvents={visible ? "auto" : "none"}
      style={[
        {
          position: "absolute",
          right: 6,
          bottom: 6,
        },
        animatedStyle,
      ]}
    >
      <Pressable
        testID={testID}
        onPress={onPress}
        disabled={!visible}
        className="items-center justify-center w-10 h-8 px-3 rounded-full bg-primary active:opacity-80"
      >
        <Send size={16} color="#fff" />
      </Pressable>
    </Animated.View>
  );
}
