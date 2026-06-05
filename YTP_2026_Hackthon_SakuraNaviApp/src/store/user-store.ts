import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import * as SecureStore from "expo-secure-store";
import type { User } from "@/types";
import {
  removeAuthToken,
  removeRefreshToken,
  setAuthToken,
  setRefreshToken,
} from "@/lib/auth/token-storage";

interface UserState {
  user: User | null;
  token: string | null;
}

interface UserAction {
  setUser: (user: User) => void;
  setUserProfile: (profile: User) => void;
  updateProfile: (updates: Partial<User>) => void;
  setToken: (
    token: string | null | undefined,
    refreshToken?: string | null | undefined,
  ) => Promise<void>;
  clearSession: () => void;
}

type UserStore = UserState & UserAction;

// 建立給 Zustand persist 使用的自訂 Secure Store 解析器
const secureStorage = {
  getItem: async (name: string): Promise<string | null> => {
    return await SecureStore.getItemAsync(name);
  },
  setItem: async (name: string, value: string): Promise<void> => {
    await SecureStore.setItemAsync(name, value);
  },
  removeItem: async (name: string): Promise<void> => {
    await SecureStore.deleteItemAsync(name);
  },
};

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,

      setUser: (user) => set({ user }),

      setUserProfile: (profile) =>
        set((state) => ({
          user: state.user
            ? {
                ...state.user,
                profile,
                userProfile: profile,
              }
            : null,
        })),

      updateProfile: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      setToken: async (token, refreshToken) => {
        try {
          await setAuthToken(token);
          if (refreshToken !== undefined) {
            await setRefreshToken(refreshToken);
          }
          set({ token: token ?? null });
        } catch (error) {
          console.error(error);
        }
      },

      clearSession: () => {
        void Promise.all([removeAuthToken(), removeRefreshToken()]);
        set({
          user: null,
          token: null,
        });
      },
    }),
    {
      name: "user-session-storage",
      storage: createJSONStorage(() => secureStorage),
    },
  ),
);
