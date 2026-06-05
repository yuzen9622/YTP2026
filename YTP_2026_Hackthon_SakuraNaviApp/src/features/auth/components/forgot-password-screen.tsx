import { useState } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { MailCheck } from "lucide-react-native";
import { toast } from "sonner-native";
import { useForgotPasswordMutation } from "../hooks";

export function ForgotPasswordScreen() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const forgotPasswordMutation = useForgotPasswordMutation();

  async function handleSend() {
    if (!email) {
      toast.error("請輸入電子郵件");
      return;
    }
    try {
      await forgotPasswordMutation.mutateAsync(email);
      setSent(true);
      toast("重設連結已寄出，請檢查信箱");
    } catch {
      // 錯誤由 fetch client 統一 Toast 處理
    }
  }

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={{ padding: 24, gap: 24, paddingTop: 60 }}
    >
      <View style={{ gap: 8 }}>
        <Text style={{ fontSize: 26, fontWeight: "700", color: "#1a1a1a" }}>
          忘記密碼
        </Text>
        <Text className="text-sm text-muted-foreground">
          輸入你的帳號信箱，我們將寄送重設密碼連結給你
        </Text>
      </View>

      {!sent ? (
        <View style={{ gap: 16 }}>
          <View style={{ gap: 6 }}>
            <Text className="">電子郵件</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="name@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoFocus
              style={{
                borderWidth: 1,
                borderColor: "#E0E0E0",
                borderRadius: 12,
                borderCurve: "continuous",
                paddingHorizontal: 14,
                paddingVertical: 12,
                fontSize: 15,
                color: "#1a1a1a",
              }}
            />
          </View>

          <Pressable
            onPress={handleSend}
            disabled={forgotPasswordMutation.isPending}
            style={({ pressed }) => ({
              backgroundColor:
                pressed || forgotPasswordMutation.isPending
                  ? "#e8455a"
                  : "#FF6B9D",
              borderRadius: 14,
              borderCurve: "continuous",
              paddingVertical: 14,
              alignItems: "center",
            })}
          >
            <Text style={{ color: "#fff", fontSize: 16, fontWeight: "700" }}>
              {forgotPasswordMutation.isPending ? "寄送中..." : "寄送重設連結"}
            </Text>
          </Pressable>
        </View>
      ) : (
        <View
          style={{
            backgroundColor: "#FFF0F5",
            borderRadius: 16,
            borderCurve: "continuous",
            padding: 24,
            gap: 12,
            alignItems: "center",
          }}
        >
          <MailCheck size={48} color="#FF6B9D" />
          <Text
            style={{
              fontSize: 16,
              fontWeight: "600",
              color: "#1a1a1a",
              textAlign: "center",
            }}
          >
            重設連結已寄出
          </Text>
          <Text
            style={{
              fontSize: 14,
              color: "#666",
              textAlign: "center",
              lineHeight: 20,
            }}
          >
            已寄送至 {email}
            {"\n"}請查看信箱並點擊連結重設密碼
          </Text>
        </View>
      )}

      <Pressable onPress={() => router.replace("/(auth)/login-screen")}>
        <Text style={{ textAlign: "center", color: "#FF6B9D", fontSize: 14 }}>
          返回登入
        </Text>
      </Pressable>
    </ScrollView>
  );
}
