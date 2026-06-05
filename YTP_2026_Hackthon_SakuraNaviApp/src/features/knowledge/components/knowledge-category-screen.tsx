import { useMemo } from "react";
import {
  Linking,
  Pressable,
  ScrollView,
  TouchableOpacity,
  View,
  Text,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { ChevronLeft } from "lucide-react-native";
import { toast } from "sonner-native";
import { colors } from "@/lib/colors.ios";
import { useKnowledgeCategoryQuery } from "../hooks/use-knowledge";

function formatDateTime(value: string | null): string {
  if (!value) {
    return "--";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

async function openArticleUrl(url: string) {
  try {
    const canOpen = await Linking.canOpenURL(url);
    if (!canOpen) {
      toast.error("無法開啟文章連結");
      return;
    }

    await Linking.openURL(url);
  } catch {
    toast.error("開啟文章失敗");
  }
}

export function KnowledgeCategoryScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ category?: string | string[] }>();
  const categoryParam = useMemo(() => {
    const raw = params.category;
    const first = Array.isArray(raw) ? raw[0] : raw;
    return first ?? "";
  }, [params.category]);

  const categoryQuery = useKnowledgeCategoryQuery(categoryParam);

  return (
    <>
      <Stack.Screen
        options={{
          title: categoryParam || "分類文章",
          headerLargeTitle: false,
          headerLeft: () => (
            <Pressable
              onPress={() => {
                if (router.canGoBack()) {
                  router.back();
                  return;
                }
                router.replace("/(tabs)");
              }}
              className="items-center justify-center rounded-full shadow-sm w-9 h-9 active:opacity-70"
            >
              <ChevronLeft
                size={20}
                className="text-foreground"
                color={colors.foreground}
              />
            </Pressable>
          ),
        }}
      />

      <ScrollView
        className="flex-1 bg-background"
        contentContainerClassName="px-5 py-5 pb-12 gap-3"
      >
        <View className="bg-white border border-gray-100 rounded-3xl p-4">
          <Text className="text-xs text-gray-500">分類</Text>
          <Text className="mt-1 text-xl font-bold text-gray-900">
            {categoryParam || "--"}
          </Text>
          {categoryQuery.data && (
            <Text className="mt-2 text-sm text-gray-500">
              共 {categoryQuery.data.article_count} 篇文章
            </Text>
          )}
        </View>

        {categoryQuery.isLoading && (
          <View className="bg-white border border-gray-100 rounded-3xl p-4">
            <Text className="text-sm text-gray-500">文章載入中...</Text>
          </View>
        )}

        {categoryQuery.isError && (
          <View className="bg-white border border-gray-100 rounded-3xl p-4">
            <Text className="text-sm text-rose-500">文章載入失敗，請稍後再試</Text>
            <TouchableOpacity
              onPress={() => categoryQuery.refetch()}
              className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
            >
              <Text className="text-xs font-semibold text-rose-600">重新載入</Text>
            </TouchableOpacity>
          </View>
        )}

        {!categoryQuery.isLoading &&
          !categoryQuery.isError &&
          (categoryQuery.data?.articles.length ?? 0) === 0 && (
            <View className="bg-white border border-gray-100 rounded-3xl p-4">
              <Text className="text-sm text-gray-500">此分類目前沒有文章</Text>
            </View>
          )}

        {categoryQuery.data?.articles.map((article) => (
          <View
            key={article.id}
            className="bg-white border border-gray-100 rounded-3xl p-4"
          >
            <Text className="text-base font-bold text-gray-900">{article.title}</Text>
            <Text className="mt-2 text-sm text-gray-600" numberOfLines={3}>
              {article.summary || "暫無摘要"}
            </Text>

            <View className="mt-3 gap-1">
              <Text className="text-xs text-gray-500">
                發布時間：{formatDateTime(article.published_at)}
              </Text>
              <Text className="text-xs text-gray-500">
                官方更新：{formatDateTime(article.official_updated_at)}
              </Text>
              <Text className="text-xs text-gray-500">
                同步狀態：{article.crawl_status}
              </Text>
            </View>

            <TouchableOpacity
              onPress={() => openArticleUrl(article.url)}
              className="mt-4 self-start px-3.5 py-2 rounded-full bg-primary active:opacity-80"
            >
              <Text className="text-xs font-semibold text-primary-foreground">
                查看原文
              </Text>
            </TouchableOpacity>
          </View>
        ))}
      </ScrollView>
    </>
  );
}
