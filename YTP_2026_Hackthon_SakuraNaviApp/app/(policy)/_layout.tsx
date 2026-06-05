import { Stack } from "expo-router";
import { NoIndexHead } from "@/lib/seo";

export default function PolicyLayout() {
  return (
    <>
      <NoIndexHead />
      <Stack
        screenOptions={{
          headerTransparent: false,
          headerBackButtonDisplayMode: "minimal",
        }}
      >
        <Stack.Screen name="[category]" options={{ title: "政策分類" }} />
        <Stack.Screen
          name="document/[documentId]"
          options={{ title: "政策文件" }}
        />
      </Stack>
    </>
  );
}
