import { ScrollView, TouchableOpacity, View, Text } from "react-native";
import { useRouter } from "expo-router";
import { useKnowledgeCategoriesQuery } from "../hooks/use-knowledge";

export function KnowledgeCategoriesSection() {
  const router = useRouter();
  const categoriesQuery = useKnowledgeCategoriesQuery();

  if (categoriesQuery.isLoading) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-3xl border border-gray-100 p-4">
          <Text className="text-sm text-gray-500">分類載入中...</Text>
        </View>
      </View>
    );
  }

  if (categoriesQuery.isError) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-3xl border border-gray-100 p-4">
          <Text className="text-sm text-rose-500">分類載入失敗，請稍後再試</Text>
          <TouchableOpacity
            onPress={() => categoriesQuery.refetch()}
            className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
          >
            <Text className="text-xs font-semibold text-rose-600">重新載入</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const categories = categoriesQuery.data?.categories ?? [];

  if (categories.length === 0) {
    return (
      <View className="px-5">
        <View className="bg-white rounded-3xl border border-gray-100 p-4">
          <Text className="text-sm text-gray-500">目前沒有分類資料</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerClassName="px-5 gap-3"
    >
      {categories.map((category) => {
        const previewTitle = category.articles[0]?.title;
        return (
          <TouchableOpacity
            key={category.name}
            onPress={() =>
              router.push({
                pathname: "/(knowledge)/[category]",
                params: { category: category.name },
              })
            }
            className="w-64 bg-white rounded-3xl border border-gray-100 p-4 active:opacity-80"
          >
            <View className="flex-row items-center justify-between">
              <Text
                className="text-base font-bold text-gray-900 flex-1"
                numberOfLines={1}
              >
                {category.name}
              </Text>
              <View className="ml-3 px-2 py-1 rounded-full bg-rose-50">
                <Text className="text-xs font-semibold text-rose-600">
                  {category.article_count} 篇
                </Text>
              </View>
            </View>

            <Text className="mt-3 text-xs text-gray-400">最新文章預覽</Text>
            <Text className="mt-1 text-sm text-gray-600" numberOfLines={2}>
              {previewTitle || "此分類目前沒有文章預覽"}
            </Text>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
}
