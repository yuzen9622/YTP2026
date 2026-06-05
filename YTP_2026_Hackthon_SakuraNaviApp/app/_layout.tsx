import "../global.css";
import { useEffect, useState } from "react";
import { Platform } from "react-native";
import { Stack, useRouter, useSegments } from "expo-router";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { useColorScheme } from "nativewind";
import { Toaster } from "sonner-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { PortalHost } from "@rn-primitives/portal";
import { Host, VStack, Text, ProgressView } from "@expo/ui/swift-ui";
import { font, foregroundStyle, tint } from "@expo/ui/swift-ui/modifiers";
import { colors } from "@/lib/colors.ios";
import { useUserStore } from "@/store/user-store";
import { me } from "@/features/auth/api/auth-api";

// Inner component that uses useQuery - must be inside QueryClientProvider
function AuthenticatedApp({
  isSignedIn,
  isHydrated,
}: {
  isSignedIn: boolean;
  isHydrated: boolean;
}) {
  const router = useRouter();
  const segments = useSegments();

  // Fetch user profile on mount when signed in
  const { data: profile } = useQuery({
    queryKey: ["user-profile"],
    queryFn: me,
    enabled: isSignedIn,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update user store when profile is fetched
  useEffect(() => {
    if (profile) {
      useUserStore.getState().setUser(profile);
    }
  }, [profile]);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    const root = segments[0] ?? "index";
    const inAuthGroup = root === "(auth)";
    const inOnboardingGroup = root === "(onboarding)";
    const inProtectedGroup =
      root === "(tabs)" ||
      root === "(chat-detail)" ||
      root === "(knowledge)" ||
      root === "(policy)";
    const inIndex = root === "index";
    const isWeb = Platform.OS === "web";

    if (!isSignedIn) {
      const shouldRedirectToLogin =
        inProtectedGroup || inOnboardingGroup || (inIndex && !isWeb);

      if (shouldRedirectToLogin) {
        router.replace("/(auth)/login-screen");
      }
      return;
    }

    if (inAuthGroup || (inIndex && !isWeb)) {
      router.replace("/(tabs)");
    }
  }, [isHydrated, isSignedIn, router, segments]);

  return (
    <>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="policy" />
        <Stack.Protected guard={!isSignedIn}>
          <Stack.Screen name="(auth)" />
        </Stack.Protected>
        <Stack.Protected guard={isSignedIn}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="(chat-detail)" />
          <Stack.Screen name="(knowledge)" />
          <Stack.Screen name="(policy)" />
        </Stack.Protected>
      </Stack>
      <Toaster />
    </>
  );
}

export default function RootLayout() {
  useColorScheme();
  const { user, token } = useUserStore();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 0,
          },
        },
      }),
  );
  const [isHydrated, setIsHydrated] = useState(() =>
    useUserStore.persist.hasHydrated(),
  );

  const isSignedIn = Boolean(user?.id && token);

  useEffect(() => {
    const unsubscribeHydrate = useUserStore.persist.onHydrate(() =>
      setIsHydrated(false),
    );
    const unsubscribeFinishHydration = useUserStore.persist.onFinishHydration(
      () => setIsHydrated(true),
    );

    if (!useUserStore.persist.hasHydrated()) {
      void useUserStore.persist.rehydrate();
    }

    return () => {
      unsubscribeHydrate();
      unsubscribeFinishHydration();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <GestureHandlerRootView className=" bg-background" style={{ flex: 1 }}>
        <SafeAreaProvider>
          {isHydrated ? (
            <AuthenticatedApp isSignedIn={isSignedIn} isHydrated={isHydrated} />
          ) : (
            <Host
              style={{
                flex: 1,
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: colors.background,
              }}
            >
              <VStack alignment="center" spacing={10}>
                <ProgressView modifiers={[tint(colors.primary)]} />
                <Text
                  modifiers={[
                    font({ size: 14 }),
                    foregroundStyle(colors.mutedForeground),
                  ]}
                >
                  初始化中...
                </Text>
              </VStack>
            </Host>
          )}
          <PortalHost />
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </QueryClientProvider>
  );
}
