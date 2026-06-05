import { useCallback } from "react";
import { toast } from "sonner-native";
import { getAuthTokens, me } from "@/features/auth/api/auth-api";
import type { AuthResponse } from "@/features/auth/api/auth-api";
import { useUserStore } from "@/store/user-store";

interface RouterLike {
  push: (path: string) => void;
  replace: (path: string) => void;
}

interface AuthSubmitOptions {
  successPath: string;
  missingTokenPath?: string;
  navigateMethod?: "push" | "replace";
  missingTokenMessage?: string;
}

export function useAuthSubmit(router: RouterLike) {
  const setToken = useUserStore((state) => state.setToken);
  const setUser = useUserStore((state) => state.setUser);

  const handleAuthSuccess = useCallback(
    async (data: AuthResponse, options: AuthSubmitOptions) => {
      const {
        successPath,
        missingTokenPath = "/(auth)/login-screen",
        navigateMethod = "replace",
        missingTokenMessage = "操作成功但未取得授權憑證，請重新登入",
      } = options;

      const { accessToken, refreshToken } = getAuthTokens(data);
      if (!accessToken || !refreshToken) {
        toast.error(missingTokenMessage);
        router.replace(missingTokenPath);
        return false;
      }

      await setToken(accessToken, refreshToken);
      const user = await me();
      console.log(user);
      setUser(user);
      if (navigateMethod === "push") {
        router.push(successPath);
      } else {
        router.replace(successPath);
      }

      return true;
    },
    [router, setToken, setUser],
  );

  return {
    handleAuthSuccess,
  };
}
