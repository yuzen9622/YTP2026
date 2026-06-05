import { useMemo } from "react";
import { Alert, Pressable, ScrollView, View } from "react-native";
import { Stack, router } from "expo-router";
import { FileText } from "lucide-react-native";
import { toast } from "sonner-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Text } from "@/components/ui/text";

import {
  useDeleteResumeMutation,
  useResumesQuery,
  useSetPrimaryResumeMutation,
  useUnsetPrimaryResumeMutation,
} from "../hooks/use-resumes";

function formatUpdatedAt(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function ManageResumesScreen() {
  const resumesQuery = useResumesQuery();
  const deleteResumeMutation = useDeleteResumeMutation();
  const setPrimaryMutation = useSetPrimaryResumeMutation();
  const unsetPrimaryMutation = useUnsetPrimaryResumeMutation();

  const resumes = useMemo(() => resumesQuery.data ?? [], [resumesQuery.data]);

  const handleDelete = (resumeId: string, title: string) => {
    Alert.alert("刪除履歷", `確定要刪除「${title}」嗎？`, [
      { text: "取消", style: "cancel" },
      {
        text: "刪除",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteResumeMutation.mutateAsync(resumeId);
            toast.success("履歷已刪除");
          } catch {
            // API interceptor handles toasts
          }
        },
      },
    ]);
  };

  const handleTogglePrimary = async (resumeId: string, isPrimary: boolean) => {
    try {
      if (isPrimary) {
        await unsetPrimaryMutation.mutateAsync(resumeId);
        toast.success("已取消主要履歷");
        return;
      }

      await setPrimaryMutation.mutateAsync(resumeId);
      toast.success("已設定為主要履歷");
    } catch {
      // API interceptor handles toasts
    }
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: "管理履歷",
          headerLargeTitle: false,
        }}
      />

      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 bg-muted/30"
        contentContainerClassName="p-4 pb-10 gap-4"
      >
        <Card className="gap-3 border-border rounded-2xl p-4">
          <View className="flex-row items-center justify-between">
            <View className="gap-1">
              <Text className="text-lg font-bold text-foreground">我的履歷</Text>
              <Text className="text-sm text-muted-foreground">
                可新增、編輯、刪除並設定主要履歷
              </Text>
            </View>
            <View className="h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <FileText size={18} color="#FF6B9D" />
            </View>
          </View>

          <Button
            onPress={() => router.push("/(tabs)/profile/edit-resume-screen")}
            className="rounded-xl"
          >
            <Text>新增履歷</Text>
          </Button>
        </Card>

        {resumesQuery.isLoading && (
          <Card className="rounded-2xl border-border p-4">
            <Text className="text-muted-foreground">履歷載入中...</Text>
          </Card>
        )}

        {resumesQuery.isError && (
          <Card className="rounded-2xl border-border p-4">
            <Text className="text-destructive">載入履歷失敗，請稍後再試</Text>
          </Card>
        )}

        {!resumesQuery.isLoading && resumes.length === 0 && (
          <Card className="rounded-2xl border-border p-4 gap-2">
            <Text className="font-semibold text-foreground">尚未建立履歷</Text>
            <Text className="text-sm text-muted-foreground">
              建立第一份履歷後，你可以在這裡管理所有履歷版本。
            </Text>
          </Card>
        )}

        {resumes.map((resume) => (
          <Card key={resume.id} className="rounded-2xl border-border p-4 gap-3">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1 gap-1">
                <View className="flex-row items-center gap-2">
                  <Text className="text-base font-bold text-foreground">
                    {resume.title}
                  </Text>
                  {resume.is_primary && (
                    <View className="rounded-full bg-primary/10 px-2 py-0.5">
                      <Text className="text-xs font-semibold text-primary">
                        主要履歷
                      </Text>
                    </View>
                  )}
                </View>
                {resume.summary ? (
                  <Text className="text-sm text-muted-foreground" numberOfLines={2}>
                    {resume.summary}
                  </Text>
                ) : (
                  <Text className="text-sm text-muted-foreground">尚無簡述</Text>
                )}
              </View>
            </View>

            <Text className="text-xs text-muted-foreground">
              更新於 {formatUpdatedAt(resume.updated_at)}
            </Text>

            <View className="flex-row gap-2">
              <Button
                variant="secondary"
                className="flex-1"
                onPress={() =>
                  router.push({
                    pathname: "/(tabs)/profile/resume-detail-screen",
                    params: { resumeId: resume.id },
                  })
                }
              >
                <Text>查看完整履歷</Text>
              </Button>

              <Button
                variant="outline"
                className="flex-1"
                onPress={() =>
                  router.push({
                    pathname: "/(tabs)/profile/edit-resume-screen",
                    params: { resumeId: resume.id },
                  })
                }
              >
                <Text>編輯</Text>
              </Button>
            </View>

            <View className="flex-row gap-2">
              <Button
                variant={resume.is_primary ? "outline" : "secondary"}
                className={`flex-1 ${resume.is_primary ? "border-amber-500/40 bg-amber-50 active:bg-amber-100" : ""}`}
                disabled={setPrimaryMutation.isPending || unsetPrimaryMutation.isPending}
                onPress={() => handleTogglePrimary(resume.id, resume.is_primary)}
              >
                <Text className={resume.is_primary ? "text-amber-700" : ""}>
                  {resume.is_primary ? "取消主要" : "設為主要"}
                </Text>
              </Button>

              <Pressable
                className="h-10 items-center justify-center rounded-md border border-destructive/30 px-3 active:opacity-70"
                onPress={() => handleDelete(resume.id, resume.title)}
                disabled={deleteResumeMutation.isPending}
              >
                <Text className="text-sm font-medium text-destructive">刪除</Text>
              </Pressable>
            </View>
          </Card>
        ))}
      </ScrollView>
    </>
  );
}
