import { View, Text, ScrollView } from "react-native";

// internal components
import { HeroCard } from "./hero-card";

import { RankingSection } from "./ranking-section";
import { ActivityRail } from "./activity-rail";
import { AnnouncementSection } from "./announcement-section";
import { PolicyCategoriesSection } from "@/features/policy";

import { User } from "@/types";
import { useUserStore } from "@/store/user-store";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function HomeScreen() {
  const user = useUserStore.getState().user;
  return (
    <ScrollView showsVerticalScrollIndicator={false}>
      <Header user={user} />
      

      <View className="mb-10">
        <SectionTitle title="政策分類" />
        <PolicyCategoriesSection />
      </View>

      <View className="px-5 mb-10">
        <SectionTitle title="為您推薦的補助" />
        <RankingSection />
      </View>
      <View className="mb-10">
        <SectionTitle title="近期活動" />
        <ActivityRail />
      </View>
      <View className="px-5 mb-10">
        <SectionTitle title="公告通知" />
        <AnnouncementSection />
      </View>
      {/* Footer */}
      <View className="items-center justify-center px-5 ">
        <Text className="text-sm font-medium text-gray-400">
          Sakura Navi · AI青年就業領航員
        </Text>
      </View>
    </ScrollView>
  );
}

function Header({ user }: { user: User | null }) {
  return (
    <View className="flex-row items-center justify-between px-5 pt-2 mb-8">
      <View className="flex-row items-center flex-1">
        {/* avatar */}
        <View className="items-center justify-center w-10 h-10 rounded-full bg-rose-100">
          <Avatar
            alt={user?.name || "使用者頭像"}
            className="size-[40px] border-[3px] border-white bg-[#EEE2D9]"
          >
            <AvatarImage
              source={user?.avatar_url ? { uri: user.avatar_url } : undefined}
            />
            <AvatarFallback>
              <Text className="text-[24px] font-semibold text-[#7B5F4B]">
                {(user?.name?.trim()?.[0] || "履").toUpperCase()}
              </Text>
            </AvatarFallback>
          </Avatar>
        </View>
        {/* info */}
        <View className="ml-3">
          <Text className="text-sm font-medium text-gray-500">Sakura Navi</Text>
          {user && (
            <Text className="text-base font-bold text-gray-900 mt-0.5">
              嗨，{user.name}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

function SectionTitle({ title }: { title: string }) {
  return (
    <View className="flex-row items-center justify-between px-5 mb-4">
      <Text className="text-xl font-bold tracking-tight text-gray-900">
        {title}
      </Text>
    </View>
  );
}
