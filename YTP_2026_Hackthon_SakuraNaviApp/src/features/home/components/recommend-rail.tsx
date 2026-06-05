import { View, Text, ScrollView, Pressable } from "react-native";

const RECS = [
  {
    id: 1,
    tag: "實習",
    match: 94,
    title: "2026 海外暑期實習 (日本)",
    organizer: "國際局",
    amount: "NT$ 30,000",
    daysLeft: 5,
  },
  {
    id: 2,
    tag: "創業",
    match: 88,
    title: "青創貸款利息補貼計畫",
    organizer: "青年局",
    amount: "NT$ 200,000",
    daysLeft: 12,
  },
  {
    id: 3,
    tag: "技能",
    match: 82,
    title: "AI 應用實戰密集班",
    organizer: "經發局",
    amount: "全額補助",
    daysLeft: 2,
  },
  {
    id: 4,
    tag: "心理",
    match: 79,
    title: "青年免費心理諮商服務",
    organizer: "衛生局",
    amount: "免費 3 次",
    daysLeft: 30,
  },
];

export function RecommendRail() {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerClassName="px-5 gap-x-4 pb-2"
      snapToInterval={236}
      decelerationRate="fast"
    >
      {RECS.map((rec) => (
        <Pressable
          key={rec.id}
          className="w-[220px] bg-white rounded-2xl shadow-sm border border-gray-100 active:opacity-90 overflow-hidden"
        >
          {/* Header Gradient Banner */}
          <View className="flex-row items-center justify-between px-4 py-3 border-b bg-primary-foreground border-rose-100/50">
            <Text className="text-primary font-bold text-xs bg-white px-2 py-0.5 rounded-md shadow-sm">
              {rec.tag}
            </Text>
            <View className="bg-primary px-2 py-0.5 rounded-full">
              <Text className="text-xs font-bold text-white">
                {rec.match}% 配對
              </Text>
            </View>
          </View>

          <View className="p-4">
            <Text
              className="h-12 text-base font-bold leading-snug text-gray-900"
              numberOfLines={2}
            >
              {rec.title}
            </Text>

            <View className="mt-3">
              <Text className="mb-1 text-sm font-medium text-gray-500">
                {rec.organizer}
              </Text>
              <Text className="text-lg font-bold text-rose-500">
                {rec.amount}
              </Text>
            </View>

            <View className="flex-row items-center justify-between pt-3 mt-3 border-t border-gray-100">
              <Text className="px-2 py-1 text-xs font-medium rounded text-accent bg-primary">
                剩 {rec.daysLeft} 天
              </Text>
            </View>
          </View>
        </Pressable>
      ))}
    </ScrollView>
  );
}
