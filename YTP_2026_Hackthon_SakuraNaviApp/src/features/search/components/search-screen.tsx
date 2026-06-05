import { useEffect, useMemo, useState } from "react";
import {
  Linking,
  ScrollView,
  TouchableOpacity,
  View,
  Text,
} from "react-native";
import { Stack } from "expo-router";
import { toast } from "sonner-native";
import { useKnowledgeSearchQuery } from "@/features/knowledge/hooks/use-knowledge";


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

export function SearchScreen() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  useEffect(() => {
    const timerId = setTimeout(() => {
      setDebouncedQuery(query);
    }, 350);

    return () => {
      clearTimeout(timerId);
    };
  }, [query]);

  const normalizedQuery = useMemo(
    () => debouncedQuery.trim(),
    [debouncedQuery],
  );
  const searchQuery = useKnowledgeSearchQuery(normalizedQuery, { top_k: 8 });
  const results = searchQuery.data?.hits ?? [];

  return (
    <>
      <Stack.Screen.Title>搜尋</Stack.Screen.Title>
      <Stack.SearchBar
        placement="automatic"
        placeholder="搜尋獎學金、學校、社團..."
        onChangeText={(event) => {
          const text =
            typeof event === "string"
              ? event
              : ((event.nativeEvent as { text?: string }).text ?? "");
          setQuery(text);
        }}
      />
      <ScrollView
        className="flex-1 bg-background"
        contentInsetAdjustmentBehavior="automatic"
        contentContainerClassName="px-5 py-5 pb-12 gap-3"
      >
        {normalizedQuery.length > 0 && searchQuery.isLoading && (
          <View className="p-4 bg-white border border-gray-100 rounded-3xl">
            <Text className="text-sm text-gray-500">搜尋中...</Text>
          </View>
        )}

        {normalizedQuery.length > 0 && searchQuery.isError && (
          <View className="p-4 bg-white border border-gray-100 rounded-3xl">
            <Text className="text-sm text-rose-500">搜尋失敗，請稍後再試</Text>
            <TouchableOpacity
              onPress={() => searchQuery.refetch()}
              className="self-start mt-3 px-3 py-1.5 rounded-full bg-rose-50"
            >
              <Text className="text-xs font-semibold text-rose-600">
                重新搜尋
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {normalizedQuery.length > 0 &&
          !searchQuery.isLoading &&
          !searchQuery.isError &&
          results.length === 0 && (
            <View className="p-4 bg-white border border-gray-100 rounded-3xl">
              <Text className="text-sm text-gray-500">沒有找到相關結果</Text>
            </View>
          )}

        {results.map((result: (typeof results)[number]) => (
          <View
            key={result.chunk_id}
            className="p-4 bg-white border border-gray-100 rounded-3xl"
          >
            <Text className="text-base font-bold text-gray-900">
              {result.title}
            </Text>

            {!!result.heading && (
              <Text className="mt-1 text-xs text-gray-500">
                小節：{result.heading}
              </Text>
            )}

            <Text className="mt-2 text-sm text-gray-600" numberOfLines={4}>
              {result.snippet}
            </Text>

            <View className="gap-1 mt-3">
              <Text className="text-xs text-gray-500">
                分類：{result.category || "--"}
              </Text>
              <Text className="text-xs text-gray-500">
                檔案：{result.filename}
              </Text>
              <Text className="text-xs text-gray-500">
                相似度：{(result.score * 100).toFixed(1)}%
              </Text>
            </View>

            {result.source_url ? (
              <TouchableOpacity
                onPress={() => openSourceUrl(result.source_url!)}
                className="mt-4 self-start px-3.5 py-2 rounded-full bg-primary active:opacity-80"
              >
                <Text className="text-xs font-semibold text-primary-foreground">
                  查看來源
                </Text>
              </TouchableOpacity>
            ) : null}
          </View>
        ))}
      </ScrollView>
    </>
  );
}
