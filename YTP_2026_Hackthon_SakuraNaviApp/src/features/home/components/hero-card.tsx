import { View, Text, TouchableOpacity } from "react-native";
import { Sparkles } from "lucide-react-native";

export function HeroCard() {
  // default: gradient style (marca-red to deep burgundy)
  return (
    <View className="p-5 overflow-hidden font-sans bg-primary rounded-3xl">
      <View className="absolute w-32 h-32 rounded-full -top-10 -right-10 bg-white/10" />

      <View className="flex-row items-center self-start px-2 py-1 mb-3 rounded-full bg-white/20">
        <Sparkles size={14} color="#fff" />
        <Text className="ml-1 text-xs font-semibold text-white">
          主動為你設想
        </Text>
      </View>

      <Text className="mt-1 text-xl font-bold text-primary-foreground">
        2026 台北青年就業啟航補助
      </Text>
      <Text className="mt-1 text-lg font-semibold text-accent">
        最高 NT$ 60,000
      </Text>

      <View className="flex-row items-center mt-5 space-x-2">
        <View className="flex-1 bg-black/20 h-1.5 rounded-full overflow-hidden">
          <View className="bg-white h-full w-[94%] rounded-full" />
        </View>
        <Text className="text-xs font-bold text-right text-white w-14">
          94%
        </Text>
      </View>

      <View className="flex-row items-end justify-between mt-4">
        <View>
          <Text className="text-xs font-medium text-accent">
            剩 7 天 · 1,284 人申請
          </Text>
          <Text className="mt-1 text-xs text-accent">
            理由：科系與修課符合 5/5
          </Text>
        </View>
        <TouchableOpacity className="bg-background px-5 py-2.5 rounded-full shadow-sm shadow-primary/20 active:opacity-80">
          <Text className="text-sm font-bold text-rose-600">立即申請</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
