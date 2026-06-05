import { useCallback } from "react";
import { router } from "expo-router";
import { toast } from "sonner-native";
import { Alert } from "react-native";

import { useUserStore } from "@/store/user-store";

interface UseProfileIndexReturn {
  userName: string;
  userBio: string | undefined;
  userLocation: string | undefined;
  tags: string[];
  handleLogout: () => void;
}

export function useProfileIndex(): UseProfileIndexReturn {
  const user = useUserStore((state) => state.user);
  const clearSession = useUserStore((state) => state.clearSession);

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

  return {
    userName: user?.name || "未命名",
    userBio: user?.bio,
    userLocation: user?.location,
    tags: user?.tags || [],
    handleLogout,
  };
}