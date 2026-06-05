import { NativeTabs } from "expo-router/unstable-native-tabs";
import { colors } from "@/lib/colors.ios";
import { NoIndexHead } from "@/lib/seo";

export default function TabsLayout() {
  return (
    <>
      <NoIndexHead />
      <NativeTabs
        minimizeBehavior="onScrollDown"
        backgroundColor={colors.background}
        iconColor={{
          default: colors.mutedForeground,
          selected: colors.primary,
        }}
        labelStyle={{
          default: { color: colors.mutedForeground },
          selected: { color: colors.primary },
          fontSize: 11,
        }}
        shadowColor="rgba(0,0,0,0.08)"
      >
        <NativeTabs.Trigger name="index">
          <NativeTabs.Trigger.Icon
            sf={{ default: "house", selected: "house.fill" }}
            md="home"
          />
          <NativeTabs.Trigger.Label>首頁</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>

        <NativeTabs.Trigger name="chat">
          <NativeTabs.Trigger.Icon
            sf={{
              default: "bubble.right",
              selected: "bubble.right.fill",
            }}
            md="chat"
          />
          <NativeTabs.Trigger.Label>聊天</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>

        <NativeTabs.Trigger name="profile">
          <NativeTabs.Trigger.Icon
            sf={{ default: "person", selected: "person.fill" }}
            md="person"
          />
          <NativeTabs.Trigger.Label>我的</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="search" role="search">
          <NativeTabs.Trigger.Label>Search</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
      </NativeTabs>
    </>
  );
}
