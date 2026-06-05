import { useCallback } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { Link, useRouter } from "expo-router";
import { Eye, EyeOff } from "lucide-react-native";
import { toast } from "sonner-native";
import { useLoginMutation } from "../hooks";
import { useAuthSubmit, useForm, usePasswordToggle } from "@/hooks";
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginScreen() {
  const router = useRouter();
  const { values: loginPayload, handleChange } = useForm({
    account: "",
    password: "",
  });
  const { showPassword, toggle } = usePasswordToggle();
  const { handleAuthSuccess } = useAuthSubmit(router);
  const loginMutation = useLoginMutation();

  const handleLogin = useCallback(async () => {
    const { account, password } = loginPayload;
    if (!account || !password) {
      toast.error("請輸入帳號和密碼");
      return;
    }
    try {
      const data = await loginMutation.mutateAsync({ account, password });
      await handleAuthSuccess(data, {
        successPath: "/(tabs)/chat",
        navigateMethod: "push",
        missingTokenMessage: "登入成功但未取得授權憑證，請稍後再試",
      });
    } catch (error) {
      console.error(error);
    }
  }, [handleAuthSuccess, loginMutation, loginPayload]);

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      style={{
        flex: 1,
        display: "flex",
      }}
      contentContainerStyle={{
        padding: 24,
        gap: 24,
        paddingTop: 80,
      }}
    >
      <View className="flex items-center justify-center ">
        <Text className="text-5xl font-bold text-primary">Sakura Navi</Text>
        <Text className=" text-muted-foreground">你的青年職涯政策導航</Text>
      </View>
      <View style={{ gap: 8 }}>
        <Text className="text-3xl font-bold ">登入</Text>
        <Text className="text-sm text-muted-foreground">開始你的職涯探索</Text>
      </View>
      <View style={{ gap: 16 }}>
        <View style={{ gap: 6 }}>
          <View className="px-4 py-3 border border-border rounded-2xl">
            <Label nativeID="account" htmlFor="account" className="text-sm">
              帳號
            </Label>
            <Input
              id="account"
              value={loginPayload.account}
              onChangeText={(text) => handleChange("account", text)}
              placeholder="wang_123"
              keyboardType="default"
              autoCapitalize="none"
              style={{ backgroundColor: "transparent" }}
              className="h-auto px-0 py-0 mt-1 bg-transparent border-0 shadow-none"
            />
          </View>
        </View>

        <View style={{ gap: 6 }}>
          <View style={{ alignItems: "flex-end" }}>
            <Link href="/(auth)/forgot-password-screen" asChild>
              <Pressable>
                <Text className="text-xs text-primary">忘記密碼？</Text>
              </Pressable>
            </Link>
          </View>
          <View className="relative px-4 py-3 border border-border rounded-2xl">
            <Label nativeID="password" htmlFor="password">
              密碼
            </Label>
            <View style={{ position: "relative", marginTop: 4 }}>
              <Input
                id="password"
                value={loginPayload.password}
                onChangeText={(text) => handleChange("password", text)}
                style={{ backgroundColor: "transparent" }}
                placeholder="請輸入密碼"
                secureTextEntry={!showPassword}
                className="h-auto px-0 py-0 pr-10 bg-transparent! border-0 shadow-none"
              />
            </View>
            <Pressable
              onPress={toggle}
              style={{
                position: "absolute",
                right: 8,
                top: 0,
                bottom: 0,
                justifyContent: "center",
              }}
            >
              {showPassword ? (
                <EyeOff size={20} color="#999" />
              ) : (
                <Eye size={20} color="#999" />
              )}
            </Pressable>
          </View>
        </View>

        <Button onPress={handleLogin} disabled={loginMutation.isPending}>
          <Text> 登入</Text>
        </Button>
      </View>

      <View className="flex flex-row items-center justify-center gap-1 ">
        <Text className="text-sm text-center ">還沒註冊 ？</Text>
        <Link href="/(auth)/register-screen" asChild>
          <Pressable>
            <Text className="text-sm text-pink-400 ">註冊</Text>
          </Pressable>
        </Link>
      </View>
    </ScrollView>
  );
}
