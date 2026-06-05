import { Stack } from "expo-router";
import { NoIndexHead } from "@/lib/seo";

export default function KnowledgeLayout() {
  return (
    <>
      <NoIndexHead />
      <Stack
        screenOptions={{
          headerTransparent: false,
          headerBackButtonDisplayMode: "minimal",
        }}
      >
        <Stack.Screen name="[category]" options={{ title: "分類文章" }} />
      </Stack>
    </>
  );
}
