import { ScrollView, View, Pressable, Text } from "react-native";
import { useRouter } from "expo-router";
import { usePolicyCategoriesQuery } from "../hooks/use-policy";
import { getPolicyCategoryLabel } from "../utils/policy-category-label";

export function PolicyCategoriesSection() {
  const router = useRouter();
  const categoriesQuery = usePolicyCategoriesQuery();

  if (categoriesQuery.isLoading) {
    return (
      <View className="px-5">
        <View className="p-4 bg-white border border-gray-100 rounded-3xl">
          <Text className="text-sm text-gray-500">分類載入中...</Text>
        </View>
      </View>
    );
  }

  if (categoriesQuery.isError) {
    return (
      <View className="px-5">
        <View className="p-4 bg-white border border-gray-100 rounded-3xl">
          <Text className="text-sm text-rose-500">
            分類載入失敗，請稍後再試
          </Text>
          <Pressable
            onPress={() => categoriesQuery.refetch()}
            className="self-start px-3 py-2 mt-3 rounded-full bg-rose-50"
          >
            <Text className="text-xs font-semibold text-rose-600">
              重新載入
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }

  const categories = categoriesQuery.data?.items ?? [];

  if (categories.length === 0) {
    return (
      <View className="px-5">
        <View className="p-4 bg-white border border-gray-100 rounded-3xl">
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
      {categories.map((item) => (
        <Pressable
          key={item.category}
          onPress={() =>
            router.push({
              pathname: "/(policy)/[category]",
              params: { category: item.category },
            })
          }
          className="p-4 bg-white border border-gray-100 w-52 rounded-3xl active:opacity-80"
        >
          <Text
            className="text-base font-bold text-gray-900"
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {getPolicyCategoryLabel(item.category)}
          </Text>

          <View className="self-start mt-3 px-2.5 py-1 rounded-full bg-rose-50">
            <Text className="text-xs font-semibold text-rose-600">
              {item.count} 篇
            </Text>
          </View>

          <Text className="mt-3 text-xs leading-5 text-gray-500">
            點擊查看此分類完整政策文件
          </Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}
