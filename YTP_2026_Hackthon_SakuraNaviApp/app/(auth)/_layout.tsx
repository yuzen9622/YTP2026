import { Stack } from "expo-router";
import { NoIndexHead } from "@/lib/seo";

export default function AuthLayout() {
  return (
    <>
      <NoIndexHead />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="login-screen" />
        <Stack.Screen name="register-screen" />
        <Stack.Screen name="forgot-password-screen" />
      </Stack>
    </>
  );
}
