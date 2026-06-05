import { View, Text, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { useHomeAnnouncementsQuery } from "../hooks/use-home";
import {
  isHomeItemNavigable,
  navigateHomeItem,
} from "../utils/home-item-navigation";

export function AnnouncementSection() {
  const router = useRouter();
  const announcementsQuery = useHomeAnnouncementsQuery({ limit: 5 });
  const announcements = announcementsQuery.data ?? [];

  if (announcementsQuery.isLoading) {
    return (
      <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
        <Text className="text-sm text-gray-500">公告資料載入中...</Text>
      </View>
    );
  }

  if (announcementsQuery.isError) {
    return (
      <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
        <Text className="text-sm text-rose-500">公告資料載入失敗，請稍後再試</Text>
        <TouchableOpacity
          onPress={() => announcementsQuery.refetch()}
          className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
        >
          <Text className="text-xs font-semibold text-rose-600">重新載入</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (announcements.length === 0) {
    return (
      <View className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
        <Text className="text-sm text-gray-500">目前沒有最新公告</Text>
      </View>
    );
  }

  return (
    <View className="gap-y-3">
      {announcements.map((item) => (
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
          className="p-4 rounded-2xl shadow-sm border bg-white border-gray-100 flex-row items-start active:opacity-90"
        >
          <View className="flex-1">
            <View className="flex-row items-center mb-1">
              <Text className="text-xs font-medium text-gray-500">
                {item.publishedAtText}
              </Text>
            </View>
            <Text className="mb-1 text-base font-bold text-gray-900">
              {item.title}
            </Text>
            <Text
              className="text-sm leading-relaxed text-gray-500"
              numberOfLines={2}
            >
              {item.summary}
            </Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
}
