import { ScrollView, View } from "react-native";
import { Stack } from "expo-router";
import { CircleHelp } from "lucide-react-native";

import { Card } from "@/components/ui/card";
import { Text } from "@/components/ui/text";

const FAQ_ITEMS = [
  {
    question: "Sakura Navi 是做什麼的？",
    answer:
      "Sakura Navi 是提供日本升學、獎學金與在地生活資訊的整合服務，協助你快速找到可信來源與重點摘要。",
  },
  {
    question: "平台資訊多久更新一次？",
    answer:
      "我們會持續同步公開資訊，並在來源更新後盡快反映到系統。建議在申請前再次確認原始公告內容與截止日期。",
  },
  {
    question: "搜尋結果和官方資訊不一致怎麼辦？",
    answer:
      "請以政府機關、學校或主辦單位官網為準。若你發現差異，可透過客服信箱回報，我們會優先檢查。",
  },
  {
    question: "我的個人資料會被公開嗎？",
    answer:
      "不會。除非你明確授權，系統不會對外公開可識別個人資訊。我們僅在提供功能所需範圍內使用資料。",
  },
  {
    question: "可以刪除帳號與資料嗎？",
    answer:
      "可以。你可透過客服提出刪除申請，我們會在完成身份確認後，依流程處理帳號與關聯資料。",
  },
];

export function FaqScreen() {
  return (
    <>
      <Stack.Screen
        options={{
          title: "常見問題",
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
            <CircleHelp size={18} color="#2563EB" />
            <Text className="text-base font-bold text-foreground">
              使用說明
            </Text>
          </View>
          <Text className="text-sm leading-6 text-muted-foreground">
            這裡整理了常見問題，內容參考常見政府服務與大型平台說明格式，重點先說結論、再補充處理方式。
          </Text>
        </Card>

        {FAQ_ITEMS.map((item, index) => (
          <Card
            key={item.question}
            className="gap-2 p-4 rounded-2xl border-border"
          >
            <Text className="text-[15px] font-bold text-foreground">
              Q{index + 1}. {item.question}
            </Text>
            <Text className="text-[14px] leading-6 text-muted-foreground">
              A. {item.answer}
            </Text>
          </Card>
        ))}

        <Card className="gap-2 p-4 rounded-2xl border-border">
          <Text className="text-[15px] font-bold text-foreground">
            聯絡我們
          </Text>
          <Text className="text-[14px] leading-6 text-muted-foreground">
            若以上內容無法解決問題，請來信
            contact@sakura-cloud.com，並附上問題描述與截圖，我們會盡快回覆。
          </Text>
        </Card>
      </ScrollView>
    </>
  );
}
