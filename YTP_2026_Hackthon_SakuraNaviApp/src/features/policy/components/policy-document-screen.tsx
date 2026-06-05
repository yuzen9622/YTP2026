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
import { ChevronLeft, ExternalLink } from "lucide-react-native";
import { toast } from "sonner-native";
import { colors } from "@/lib/colors.ios";
import { MarkdownText } from "@/features/chat/components/markdown/markdown-text";
import { usePolicyDocumentQuery } from "../hooks/use-policy";
import { buildPolicyMarkdownContent } from "../utils/policy-markdown";

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

export function PolicyDocumentScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ documentId?: string | string[] }>();

  const documentIdParam = useMemo(() => {
    const raw = params.documentId;
    const first = Array.isArray(raw) ? raw[0] : raw;
    return first ?? "";
  }, [params.documentId]);

  const documentQuery = usePolicyDocumentQuery(documentIdParam);

  const markdownContent = useMemo(() => {
    if (!documentQuery.data) {
      return "";
    }

    return buildPolicyMarkdownContent(documentQuery.data);
  }, [documentQuery.data]);

  return (
    <>
      <Stack.Screen
        options={{
          title: documentQuery.data?.title || "政策文件",
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
        contentContainerClassName=" pb-12 gap-3"
      >
        {documentQuery.isLoading ? (
          <View className="p-4 bg-white border border-gray-100 ">
            <Text className="text-sm text-gray-500">文件載入中...</Text>
          </View>
        ) : null}

        {documentQuery.isError ? (
          <View className="p-4 bg-white border border-gray-100 ">
            <Text className="text-sm text-rose-500">
              文件載入失敗，請稍後再試
            </Text>
            <TouchableOpacity
              onPress={() => documentQuery.refetch()}
              className="self-start px-3 py-2 mt-3 rounded-full bg-rose-50"
            >
              <Text className="text-xs font-semibold text-rose-600">
                重新載入
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {documentQuery.data ? (
          <>
            <View className="p-4 bg-white border border-gray-100 ">
              <Text className="mb-2 text-xs text-gray-500">文件內容</Text>
              <MarkdownText content={markdownContent} />
            </View>
          </>
        ) : null}
      </ScrollView>
    </>
  );
}
