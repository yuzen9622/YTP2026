import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { useHomeNewsQuery } from "../hooks/use-home";
import {
  isHomeItemNavigable,
  navigateHomeItem,
} from "../utils/home-item-navigation";

export function ActivityRail() {
  const router = useRouter();
  const newsQuery = useHomeNewsQuery({ limit: 5 });
  const newsItems = newsQuery.data ?? [];

  if (newsQuery.isLoading) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <Text className="text-sm text-gray-500">新聞資料載入中...</Text>
        </View>
      </View>
    );
  }

  if (newsQuery.isError) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <Text className="text-sm text-rose-500">新聞資料載入失敗，請稍後再試</Text>
          <TouchableOpacity
            onPress={() => newsQuery.refetch()}
            className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
          >
            <Text className="text-xs font-semibold text-rose-600">重新載入</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (newsItems.length === 0) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <Text className="text-sm text-gray-500">近期沒有新聞資料</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerClassName="px-5 gap-x-4 pb-2"
      snapToInterval={246}
      decelerationRate="fast"
    >
      {newsItems.map((act) => (
        <TouchableOpacity
          key={act.id}
          onPress={() =>
            void navigateHomeItem({
              documentId: act.documentId,
              sourceLink: act.sourceLink,
              pushDocument: (documentId) =>
                router.push({
                  pathname: "/(policy)/document/[documentId]",
                  params: { documentId },
                }),
            })
          }
          disabled={!isHomeItemNavigable(act)}
          className="w-[230px] bg-white rounded-2xl shadow-sm border border-gray-100 flex-row overflow-hidden active:opacity-90"
        >
          {/* Date Left Panel */}
          <View
            className={`w-[60px] p-3 items-center justify-center ${act.isToday ? "bg-primary" : "bg-gray-50"}`}
          >
            <Text
              className={`text-xs font-bold uppercase ${act.isToday ? "text-rose-100" : "text-gray-400"}`}
            >
              {act.monthText}
            </Text>
            <Text
              className={`text-2xl font-bold tracking-tighter my-0.5 ${act.isToday ? "text-white" : "text-gray-800"}`}
            >
              {act.dayText}
            </Text>
            <Text
              className={`text-xs font-semibold ${act.isToday ? "text-white" : "text-gray-500"}`}
            >
              {act.weekText}
            </Text>
          </View>

          <View className="flex-1 p-3">
            <View className="flex-row items-center mb-1">
              <View className="w-1.5 h-1.5 rounded-full bg-blue-500 mr-1.5" />
              <Text className="text-xs font-bold text-gray-500">
                {act.dateText}
              </Text>
            </View>
            <Text
              className="mb-2 text-base font-bold leading-snug text-gray-900"
              numberOfLines={2}
            >
              {act.title}
            </Text>
            <View className="mt-auto">
              <Text className="text-xs font-medium text-gray-500">
                {act.summary}
              </Text>
            </View>
          </View>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}
