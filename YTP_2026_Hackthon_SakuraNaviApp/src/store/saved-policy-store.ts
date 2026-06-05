import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

const STORAGE_KEY = "sakura.saved-policies.v3";

interface SavedPolicyState {
  savedPolicyIds: string[];
}

interface SavedPolicyAction {
  setSavedPolicies: (policyIds: string[]) => void;
  toggleSavedPolicy: (policyId: string) => void;
  isPolicySaved: (policyId: string) => boolean;
}

type SavedPolicyStore = SavedPolicyState & SavedPolicyAction;

export const useSavedPolicyStore = create<SavedPolicyStore>()(
  persist(
    (set, get) => ({
      savedPolicyIds: [],

      setSavedPolicies: (policyIds) => {
        const uniquePolicyIds = Array.from(new Set(policyIds.filter(Boolean)));
        set({ savedPolicyIds: uniquePolicyIds });
      },

      toggleSavedPolicy: (policyId) => {
        if (!policyId) {
          return;
        }

        set((state) => {
          if (state.savedPolicyIds.includes(policyId)) {
            return {
              savedPolicyIds: state.savedPolicyIds.filter(
                (id) => id !== policyId,
              ),
            };
          }

          return {
            savedPolicyIds: [policyId, ...state.savedPolicyIds],
          };
        });
      },

      isPolicySaved: (policyId) => get().savedPolicyIds.includes(policyId),
    }),
    {
      name: STORAGE_KEY,
      version: 1,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({ savedPolicyIds: state.savedPolicyIds }),
    },
  ),
);
