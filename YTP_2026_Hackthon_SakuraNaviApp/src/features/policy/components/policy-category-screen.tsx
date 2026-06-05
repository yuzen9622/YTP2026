import { useMemo } from "react";
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Pressable,
  TouchableOpacity,
  View,
  Text,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { ChevronLeft, ExternalLink } from "lucide-react-native";
import { toast } from "sonner-native";
import { colors } from "@/lib/colors.ios";
import { usePolicyDocumentsInfiniteQuery } from "../hooks/use-policy";
import type { PolicyDocumentResponse } from "../types/policy";
import { getPolicyCategoryLabel } from "../utils/policy-category-label";

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

async function openSourceUrl(url: string) {
  try {
    const canOpen = await Linking.canOpenURL(url);
    if (!canOpen) {
      toast.error("無法開啟來源連結");
      return;
    }

    await Linking.openURL(url);
  } catch {
    toast.error("開啟來源連結失敗");
  }
}

export function PolicyCategoryScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ category?: string | string[] }>();

  const categoryParam = useMemo(() => {
    const raw = params.category;
    const first = Array.isArray(raw) ? raw[0] : raw;
    return first ?? "";
  }, [params.category]);

  const categoryQuery = usePolicyDocumentsInfiniteQuery(categoryParam);
  const categoryLabel = useMemo(
    () => getPolicyCategoryLabel(categoryParam),
    [categoryParam],
  );

  const documents = useMemo(() => {
    return categoryQuery.data?.pages.flatMap((page) => page.items) ?? [];
  }, [categoryQuery.data]);

  const total = categoryQuery.data?.pages[0]?.total ?? documents.length;

  const renderDocumentItem = ({ item }: { item: PolicyDocumentResponse }) => (
    <Pressable
      onPress={() =>
        router.push({
          pathname: "/(policy)/document/[documentId]",
          params: { documentId: item.id },
        })
      }
      className="p-4 mx-4 mb-3 bg-white border border-gray-100 rounded-3xl active:opacity-80"
    >
      <Text className="text-base font-bold text-gray-900">{item.title}</Text>

      <View className="gap-1 mt-3">
        <Text className="text-xs text-gray-500">
          分類：{getPolicyCategoryLabel(item.category)}
        </Text>

        <Text className="text-xs text-gray-500">
          更新時間：{formatDateTime(item.updated_at)}
        </Text>
      </View>

      <View className="flex-row items-center gap-2 mt-4">
        {item.source_url ? (
          <TouchableOpacity
            onPress={() => openSourceUrl(item.source_url!)}
            className="px-3.5 py-2 rounded-full bg-rose-50 flex-row items-center active:opacity-80"
          >
            <ExternalLink size={14} color="#E11D48" />
            <Text className="ml-1 text-xs font-semibold text-rose-600">
              來源
            </Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </Pressable>
  );

  const loadMore = () => {
    if (!categoryQuery.hasNextPage || categoryQuery.isFetchingNextPage) {
      return;
    }

    void categoryQuery.fetchNextPage();
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: categoryLabel || "政策分類",
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

      <FlatList
        className="flex-1 bg-background"
        data={documents}
        keyExtractor={(item) => item.id}
        renderItem={renderDocumentItem}
        onEndReached={loadMore}
        onEndReachedThreshold={0.4}
        ListHeaderComponent={
          <View className="px-5 pt-5 pb-3">
            <View className="p-4 bg-white border border-gray-100 rounded-3xl">
              <Text className="text-xs text-gray-500">分類</Text>
              <Text className="mt-1 text-xl font-bold text-gray-900">
                {categoryLabel || "--"}
              </Text>
              <Text className="mt-2 text-sm text-gray-500">
                共 {total} 篇文件
              </Text>
            </View>

            {categoryQuery.isLoading ? (
              <View className="p-4 mt-3 bg-white border border-gray-100 rounded-3xl">
                <Text className="text-sm text-gray-500">文件載入中...</Text>
              </View>
            ) : null}

            {categoryQuery.isError ? (
              <View className="p-4 mt-3 bg-white border border-gray-100 rounded-3xl">
                <Text className="text-sm text-rose-500">
                  文件載入失敗，請稍後再試
                </Text>
                <TouchableOpacity
                  onPress={() => categoryQuery.refetch()}
                  className="self-start px-3 py-2 mt-3 rounded-full bg-rose-50"
                >
                  <Text className="text-xs font-semibold text-rose-600">
                    重新載入
                  </Text>
                </TouchableOpacity>
              </View>
            ) : null}
          </View>
        }
        ListEmptyComponent={
          !categoryQuery.isLoading && !categoryQuery.isError ? (
            <View className="px-5 pb-8">
              <View className="p-4 bg-white border border-gray-100 rounded-3xl">
                <Text className="text-sm text-gray-500">
                  此分類目前沒有文件資料
                </Text>
              </View>
            </View>
          ) : null
        }
        ListFooterComponent={
          <View className="px-5 pb-12">
            {categoryQuery.isFetchingNextPage ? (
              <View className="items-center py-4">
                <ActivityIndicator color={colors.primary} />
                <Text className="mt-2 text-xs text-gray-500">
                  載入更多文件...
                </Text>
              </View>
            ) : null}

            {categoryQuery.hasNextPage && !categoryQuery.isFetchingNextPage ? (
              <TouchableOpacity
                onPress={loadMore}
                className="self-center px-4 py-2 bg-white border border-gray-200 rounded-full"
              >
                <Text className="text-xs font-semibold text-gray-700">
                  載入更多
                </Text>
              </TouchableOpacity>
            ) : null}
          </View>
        }
      />
    </>
  );
}
