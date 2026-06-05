import { Stack } from "expo-router/stack";

export default function ProfileTabLayout() {
  return (
    <Stack
      screenOptions={{
        headerTransparent: true,
        headerBackButtonDisplayMode: "minimal",
      }}
    >
      <Stack.Screen
        name="index"
        options={{ title: "個人設定", headerLargeTitle: true }}
      />
      <Stack.Screen name="edit-profile-screen" options={{ title: "個人資料" }} />
      <Stack.Screen name="edit-auth-screen" options={{ title: "登入與密碼" }} />
      <Stack.Screen name="manage-resumes-screen" options={{ title: "管理履歷" }} />
      <Stack.Screen name="resume-detail-screen" options={{ title: "履歷詳情" }} />
      <Stack.Screen name="edit-resume-screen" options={{ title: "編輯履歷" }} />
      <Stack.Screen name="faq-screen" options={{ title: "常見問題" }} />
      <Stack.Screen
        name="terms-privacy-screen"
        options={{ title: "服務條款與隱私權" }}
      />
    </Stack>
  );
}
