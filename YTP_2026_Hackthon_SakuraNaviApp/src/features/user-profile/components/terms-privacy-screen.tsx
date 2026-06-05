import { ScrollView, View } from "react-native";
import { Stack } from "expo-router";
import { Shield } from "lucide-react-native";

import { Card } from "@/components/ui/card";
import { Text } from "@/components/ui/text";

const TERMS_ITEMS = [
  {
    title: "服務使用原則",
    body: "你同意僅在合法且符合善意使用原則下使用本服務，不得進行干擾系統、偽造身分、或侵害他人權益之行為。",
  },
  {
    title: "資訊與免責聲明",
    body: "平台內容為資訊整理與輔助查找用途，實際申請資格、審核標準與公告內容仍以各主管機關、學校或主辦單位官方資料為準。",
  },
  {
    title: "帳號與安全責任",
    body: "你應妥善保管登入資訊，若發現帳號疑似遭未授權使用，請立即變更密碼並聯繫我們協助處理。",
  },
];

const PRIVACY_ITEMS = [
  {
    title: "蒐集資料類型",
    body: "我們可能蒐集你提供的基本資料（如姓名、電子郵件）與使用紀錄（如功能操作、裝置資訊），以提供與改善服務。",
  },
  {
    title: "資料使用目的",
    body: "資料主要用於帳號管理、功能提供、客服回覆、系統維運與安全防護，不會在未經同意下將個資販售給第三方。",
  },
  {
    title: "資料保存與刪除",
    body: "在符合法規與服務必要範圍內保存資料。你可依法提出查詢、更正或刪除申請，我們會於合理期間內處理。",
  },
];

export function TermsPrivacyScreen() {
  return (
    <>
      <Stack.Screen
        options={{
          title: "服務條款與隱私權",
          headerLargeTitle: false,
        }}
      />

      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 bg-muted/30"
        contentContainerClassName="px-4 py-4 pb-10 gap-4"
      >
        <Card className="gap-2 p-4 rounded-2xl border-border">
          <View className="flex-row items-center gap-2">
            <Shield size={18} color="#0F766E" />
            <Text className="text-base font-bold text-foreground">
              政策摘要
            </Text>
          </View>
          <Text className="text-sm leading-6 text-muted-foreground">
            以下為重點摘要版本，撰寫方式參考常見政府與公共服務軟體政策頁格式，幫助你先快速理解權利與義務。
          </Text>
          <Text className="text-xs text-muted-foreground">
            最後更新：2026 年 04 月 25 日
          </Text>
        </Card>

        <Card className="gap-3 p-4 rounded-2xl border-border">
          <Text className="text-[15px] font-bold text-foreground">
            服務條款
          </Text>
          {TERMS_ITEMS.map((item) => (
            <View key={item.title} className="gap-1">
              <Text className="text-[14px] font-semibold text-foreground">
                {item.title}
              </Text>
              <Text className="text-[14px] leading-6 text-muted-foreground">
                {item.body}
              </Text>
            </View>
          ))}
        </Card>

        <Card className="gap-3 p-4 rounded-2xl border-border">
          <Text className="text-[15px] font-bold text-foreground">
            隱私權政策
          </Text>
          {PRIVACY_ITEMS.map((item) => (
            <View key={item.title} className="gap-1">
              <Text className="text-[14px] font-semibold text-foreground">
                {item.title}
              </Text>
              <Text className="text-[14px] leading-6 text-muted-foreground">
                {item.body}
              </Text>
            </View>
          ))}
        </Card>

        <Card className="gap-2 p-4 rounded-2xl border-border">
          <Text className="text-[15px] font-bold text-foreground">
            申訴與聯絡
          </Text>
          <Text className="text-[14px] leading-6 text-muted-foreground">
            若你對條款或隱私權政策有疑問，可透過 contact@sakura-cloud.com
            與我們聯繫。我們會在合理期間內回覆並協助處理。
          </Text>
        </Card>
      </ScrollView>
    </>
  );
}
