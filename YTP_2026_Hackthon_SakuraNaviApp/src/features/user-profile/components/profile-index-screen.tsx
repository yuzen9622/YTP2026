import { useCallback } from "react";
import { Pressable, ScrollView, View, Alert } from "react-native";
import { router, Stack } from "expo-router";
import {
  BadgeCheck,
  Check,
  CircleHelp,
  FileText,
  Heart,
  Lock,
  ShieldCheck,
  User,
} from "lucide-react-native";
import { toast } from "sonner-native";
import { useUserStore } from "@/store/user-store";

import { Card } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { SettingsRow } from "./settings-row";
import { SectionContainer } from "./section-container";
import { Divider } from "./divider";

export function ProfileIndexScreen() {
  const user = useUserStore((state) => state.user);
  const clearSession = useUserStore((state) => state.clearSession);
  const tags = user?.tags || [];
  // Mock data for display based on design
  const savedCount = 14;

  const handleLogout = useCallback(() => {
    Alert.alert("登出", "確定要登出嗎？", [
      { text: "取消", style: "cancel" },
      {
        text: "確定",
        style: "destructive",
        onPress: () => {
          clearSession();
          toast("已登出...");
          router.replace("/(auth)/login-screen");
        },
      },
    ]);
  }, [clearSession]);

  const userName = user?.name || "未命名";

  return (
    <>
      <Stack.Screen
        options={{
          title: "我的",
          headerLargeTitle: false,
        }}
      />
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 bg-muted/30"
        contentContainerClassName="py-6 pb-24 gap-6"
      >
        {/* UserCard */}
        <Card className="flex-row items-center gap-4 p-4 mx-4 border shadow-sm border-border rounded-2xl">
          <View className="flex-1 gap-1">
            <View className="flex-row items-center gap-1.5">
              <Text className="text-xl font-bold text-foreground">
                {userName}
              </Text>
              <BadgeCheck size={14} color="#FF6B9D" />
            </View>
            {user?.bio && (
              <Text className="text-[14px] text-muted-foreground leading-tight">
                {user?.bio}
              </Text>
            )}
            {user?.location && (
              <Text className="text-[14px] text-muted-foreground leading-tight">
                ・{user?.location}
              </Text>
            )}

            {/* <View className="flex-row mt-1.5">
              <View className="flex-row items-center gap-1 px-2 py-1 rounded-full bg-primary/10">
                <Check size={10} color="#FF6B9D" />
                <Text className="text-[12px] font-medium text-primary">
                  已完成身份驗證
                </Text>
              </View>
            </View> */}
          </View>
        </Card>

        {/* InterestTagsCard */}
        <SectionContainer
          title="興趣標籤"
          rightAction={
            <Text className="text-[13px] text-muted-foreground">
              {tags.length} 個
            </Text>
          }
        >
          <View className="flex-row flex-wrap gap-2.5 p-4">
            {tags.length > 0 ? (
              tags.map((tag) => (
                <View
                  key={tag}
                  className="px-3.5 py-1.5 bg-primary/10 rounded-full border border-primary/20"
                >
                  <Text className="text-[14px] font-medium text-primary">
                    {tag}
                  </Text>
                </View>
              ))
            ) : (
              <Text className="text-[14px] text-muted-foreground">
                尚未設定興趣標籤
              </Text>
            )}
          </View>
        </SectionContainer>

        {/* 帳號與安全 */}
        <SectionContainer title="帳號與安全">
          <SettingsRow
            label="個人資料"
            subtitle="姓名、學校、聯絡方式"
            icon={User}
            iconColor="#64748B"
            iconBgColor="#F1F5F9"
            onPress={() => router.push("/(tabs)/profile/edit-profile-screen")}
          />
          <Divider />
          {/* <SettingsRow
            label="身份驗證"
            valueText="已驗證"
            valueColor="text-green-500"
            icon={ShieldCheck}
            iconColor="#22C55E"
            iconBgColor="#DCFCE7"
            onPress={() => {}}
          />
          <Divider /> */}
          <SettingsRow
            label="登入與密碼"
            icon={Lock}
            iconColor="#64748B"
            iconBgColor="#F1F5F9"
            onPress={() => {
              router.push("/(tabs)/profile/edit-auth-screen");
            }}
          />
        </SectionContainer>

        {/* 我的活動 */}
        <SectionContainer title="我的活動">
        
          <SettingsRow
            label="管理履歷"
            subtitle="新增、編輯、刪除與設定主要履歷"
            icon={FileText}
            iconColor="#3B82F6"
            iconBgColor="#DBEAFE"
            onPress={() => {
              router.push("/(tabs)/profile/manage-resumes-screen");
            }}
          />
        </SectionContainer>

        {/* 支援 */}
        <SectionContainer title="支援">
          <SettingsRow
            label="常見問題"
            icon={CircleHelp}
            iconColor="#64748B"
            iconBgColor="#F1F5F9"
            onPress={() => router.push("/(tabs)/profile/faq-screen")}
          />
          <Divider />

          <SettingsRow
            label="服務條款與隱私權"
            icon={FileText}
            iconColor="#64748B"
            iconBgColor="#F1F5F9"
            onPress={() => router.push("/(tabs)/profile/terms-privacy-screen")}
          />
        </SectionContainer>

        {/* LogoutButton */}
        <View className="mb-4">
          <Pressable
            onPress={handleLogout}
            className="items-center justify-center py-4 mx-4 border shadow-sm bg-background border-border rounded-2xl active:bg-muted/50"
          >
            <Text className="text-[17px] font-bold text-destructive">登出</Text>
          </Pressable>
          <Text className="text-center text-[12px] text-muted-foreground mt-4">
            版本 v1.4.2 · Build 2026.04.20
          </Text>
        </View>
      </ScrollView>
    </>
  );
}
