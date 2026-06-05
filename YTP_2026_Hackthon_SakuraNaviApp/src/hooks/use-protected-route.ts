import { useEffect } from "react";
import { useRouter } from "expo-router";
import { useUserStore } from "@/store/user-store";

export function useProtectedRoute(redirectTo = "/(auth)/login-screen") {
  const router = useRouter();
  const userId = useUserStore((state) => state.user?.id);
  const token = useUserStore((state) => state.token);

  const isAuthorized = Boolean(userId && token);

  useEffect(() => {
    if (!isAuthorized) {
      router.replace(redirectTo);
    }
  }, [isAuthorized, redirectTo, router]);

  return isAuthorized;
}
