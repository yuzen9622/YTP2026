import { View, Text, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { Flame } from "lucide-react-native";
import { useHomeSubsidyRankingQuery } from "../hooks/use-home";
import {
  isHomeItemNavigable,
  navigateHomeItem,
} from "../utils/home-item-navigation";

export function RankingSection() {
  const router = useRouter();
  const rankingQuery = useHomeSubsidyRankingQuery({ limit: 5 });
  const rankingItems = rankingQuery.data?.items ?? [];

  if (rankingQuery.isLoading) {
    return (
      <View className="bg-white rounded-3xl p-4 shadow-sm border border-gray-100">
        <Text className="text-sm text-gray-500">補助資料載入中...</Text>
      </View>
    );
  }

  if (rankingQuery.isError) {
    return (
      <View className="bg-white rounded-3xl p-4 shadow-sm border border-gray-100">
        <Text className="text-sm text-rose-500">補助資料載入失敗，請稍後再試</Text>
        <TouchableOpacity
          onPress={() => rankingQuery.refetch()}
          className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
        >
          <Text className="text-xs font-semibold text-rose-600">重新載入</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (rankingItems.length === 0) {
    return (
      <View className="bg-white rounded-3xl p-4 shadow-sm border border-gray-100">
        <Text className="text-sm text-gray-500">目前沒有可顯示的補助排行</Text>
      </View>
    );
  }

  return (
    <View className="bg-white rounded-3xl p-2 shadow-sm border border-gray-100">
      {rankingItems.map((item, index) => (
        <TouchableOpacity
          key={item.id}
          onPress={() =>
            void navigateHomeItem({
              documentId: item.documentId,
              sourceLink: item.sourceLink,
              pushDocument: (documentId) =>
                router.push({
                  pathname: "/(policy)/document/[documentId]",
                  params: { documentId },
                }),
            })
          }
          disabled={!isHomeItemNavigable(item)}
          className={`flex-row items-center p-3 rounded-2xl ${index !== rankingItems.length - 1 ? "border-b border-gray-50" : ""}`}
        >
          {/* Index */}
          <View className="w-8 items-center justify-center">
            <Text
              className={`font-mono text-lg font-bold ${index < 3 ? "text-rose-500" : "text-gray-300"}`}
            >
              {String(index + 1).padStart(2, "0")}
            </Text>
          </View>

          <View className="flex-1 ml-3 pr-2">
            <View className="flex-row items-center">
              <Text
                className="text-base font-bold text-gray-900 leading-snug flex-1"
                numberOfLines={1}
              >
                {item.title}
              </Text>
            </View>
            <View className="flex-row items-center mt-1">
              <Text className="text-xs text-gray-500 font-medium">
                {item.departmentText}
              </Text>
              {index < 3 && (
                <View className="flex-row items-center ml-2 border border-orange-100 bg-orange-50 px-1 rounded">
                  <Flame size={12} color="#f97316" />
                </View>
              )}
            </View>
          </View>

          <View className="items-end pl-2 border-l border-gray-100 min-w-[90px]">
            <Text className="text-gray-900 font-semibold">{item.amountText}</Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
}
