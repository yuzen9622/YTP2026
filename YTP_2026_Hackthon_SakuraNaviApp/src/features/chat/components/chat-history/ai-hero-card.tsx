import { View, Text, Pressable } from "react-native";
import { Sparkles } from "lucide-react-native";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  Easing,
} from "react-native-reanimated";
import { useEffect } from "react";
import { colors } from "@/lib/colors.ios";

interface AIHeroCardProps {
  onNewChat: () => void;
}

export function AIHeroCard({ onNewChat }: AIHeroCardProps) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  useEffect(() => {
    scale.value = withRepeat(
      withSequence(
        withTiming(1.05, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
      ),
      -1,
      true,
    );
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.8, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
      ),
      -1,
      true,
    );
  }, [opacity, scale]);

  const buttonAnimatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: scale.value }],
      opacity: opacity.value,
    };
  });

  return (
    <View
      className="mx-4 mt-2 mb-6 overflow-hidden rounded-3xl bg-secondary/30"
      style={{ borderCurve: "continuous" }}
    >
      <View className="absolute top-0 right-0 w-32 h-32 translate-x-8 -translate-y-8 rounded-full bg-primary/10" />
      <View className="absolute w-24 h-24 rounded-full opacity-50 -bottom-8 left-4 bg-primary/20 blur-3xl" />

      <View className="flex-row items-center justify-between p-5">
        <View className="flex-row items-center gap-3">
          <View
            className="items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary to-primary/80"
            style={{ borderCurve: "continuous" }}
          >
            <Sparkles size={24} color="#fff" />
          </View>
          <View>
            <Text className="text-base font-bold text-foreground">
              政府 AI 助手 · 小櫻
            </Text>
            <Text className="mt-1 text-sm font-medium text-primary">
              24h · 整合 37 機關
            </Text>
          </View>
        </View>

        <Pressable onPress={onNewChat}>
          <Animated.View
            style={[
              {
                backgroundColor: colors.background,
                paddingHorizontal: 16,
                paddingVertical: 10,
                borderRadius: 20,
                borderCurve: "continuous",
                shadowColor: colors.primary,
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.15,
                shadowRadius: 8,
                elevation: 4,
              },
              buttonAnimatedStyle,
            ]}
          >
            <Text className="text-[15px] font-bold text-primary">新對話</Text>
          </Animated.View>
        </Pressable>
      </View>
    </View>
  );
}
