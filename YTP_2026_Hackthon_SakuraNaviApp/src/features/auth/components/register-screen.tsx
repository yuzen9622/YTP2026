import { useCallback } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { Link, useRouter } from "expo-router";
import { Eye, EyeOff } from "lucide-react-native";
import { toast } from "sonner-native";
import { RegisterPayload } from "../api/auth-api";
import { useRegisterMutation } from "../hooks";
import { useAuthSubmit, useForm, usePasswordToggle } from "@/hooks";
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function RegisterScreen() {
  const router = useRouter();
  const { values: registerInfo, handleChange } = useForm<RegisterPayload>({
    account: "",
    email: "",
    password: "",
    name: "",
  });
  const { showPassword, toggle } = usePasswordToggle();
  const { handleAuthSuccess } = useAuthSubmit(router);
  const registerMutation = useRegisterMutation();

  const handleRegister = useCallback(async () => {
    const { account, email, password, name } = registerInfo;
    if (!email || !password) {
      toast.error("請輸入電子郵件和密碼");
      return;
    }
    if (password.length < 8) {
      toast.error("密碼至少需要 8 個字元");
      return;
    }
    try {
      const data = await registerMutation.mutateAsync({
        name,
        account,
        email,
        password,
      });
      toast.success("帳號建立成功！");

      await handleAuthSuccess(data, {
        successPath: "/(onboarding)/profile-setup-screen?from=register",
        missingTokenPath: "/(auth)/login-screen",
        navigateMethod: "replace",
        missingTokenMessage: "註冊成功但未取得授權憑證，請重新登入",
      });
    } catch {
      // 錯誤由 fetch client 統一 Toast 處理
    }
  }, [handleAuthSuccess, registerInfo, registerMutation]);

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      style={{ flex: 1 }}
      contentContainerStyle={{ padding: 24, paddingTop: 80, gap: 24 }}
    >
      <View className="flex items-center justify-center ">
        <Text className="text-5xl font-bold text-primary">Sakura Navi</Text>
        <Text className=" text-muted-foreground">你的青年職涯政策導航</Text>
      </View>
      <View style={{ gap: 8 }}>
        <Text className="text-3xl font-bold ">建立帳號</Text>
        <Text className="text-sm text-muted-foreground">加入 Sakura Navi</Text>
      </View>
      <View style={{ gap: 16 }}>
        <View style={{ gap: 6 }}>
          <View className="px-4 py-3 border border-border rounded-2xl">
            <Label
              htmlFor="display-name"
              nativeID="display-name"
              className="text-sm"
            >
              顯示名稱
            </Label>
            <Input
              id="display-name"
              value={registerInfo.name}
              onChangeText={(text) => handleChange("name", text)}
              placeholder="王小明"
              autoCapitalize="none"
              style={{ backgroundColor: "transparent" }}
              className="h-auto px-0 py-0 mt-1 bg-transparent border-0 shadow-none"
            />
          </View>
        </View>

        <View style={{ gap: 6 }}>
          <View className="px-4 py-3 border border-border rounded-2xl">
            <Label
              htmlFor="display-name"
              nativeID="display-name"
              className="text-sm"
            >
              帳號
            </Label>
            <Input
              id="display-name"
              value={registerInfo.account}
              onChangeText={(text) => handleChange("account", text)}
              placeholder="wang_0101"
              autoCapitalize="none"
              style={{ backgroundColor: "transparent" }}
              className="h-auto px-0 py-0 mt-1 bg-transparent border-0 shadow-none"
            />
          </View>
        </View>

        <View style={{ gap: 6 }}>
          <View className="px-4 py-3 border border-border rounded-2xl">
            <Label htmlFor="email" nativeID="email" className="text-sm">
              電子郵件
            </Label>
            <Input
              id="email"
              value={registerInfo.email}
              onChangeText={(text) => handleChange("email", text)}
              placeholder="name@example.com"
              keyboardType="email-address"
              style={{ backgroundColor: "transparent" }}
              autoCapitalize="none"
              className="h-auto px-0 py-0 mt-1 bg-transparent border-0 shadow-none"
            />
          </View>
        </View>

        <View style={{ gap: 6 }}>
          <View className="px-4 py-3 border border-border rounded-2xl">
            <Label nativeID="password" htmlFor="password" className="text-sm">
              密碼
            </Label>
            <View style={{ position: "relative", marginTop: 4 }}>
              <Input
                id="password"
                value={registerInfo.password}
                onChangeText={(text) => handleChange("password", text)}
                style={{ backgroundColor: "transparent" }}
                placeholder="至少 8 個字元"
                secureTextEntry={!showPassword}
                className="h-auto px-0 py-0 pr-10 bg-transparent border-0 shadow-none"
              />
              <Pressable
                onPress={toggle}
                style={{
                  position: "absolute",
                  right: 0,
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
        </View>

        <Button onPress={handleRegister} disabled={registerMutation.isPending}>
          <Text>{registerMutation.isPending ? "建立中..." : "建立帳號"}</Text>
        </Button>
      </View>
      <View className="flex flex-row items-center justify-center gap-1">
        <Text className="text-sm text-center">已有帳號？</Text>
        <Link href="/(auth)/login-screen" asChild>
          <Pressable>
            <Text className="text-sm text-pink-400">登入</Text>
          </Pressable>
        </Link>
      </View>
    </ScrollView>
  );
}
