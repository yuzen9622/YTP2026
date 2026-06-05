import { Conversation } from "@/types";

export function groupChatConversationsByDate(
  conversations: Conversation[],
): { title: string; data: Conversation[] }[] {
  const pinned = conversations.filter((c) => c.pinned);
  const unpinned = conversations.filter((c) => !c.pinned);

  const today: Conversation[] = [];
  const yesterday: Conversation[] = [];
  const older: Conversation[] = [];

  const now = new Date();
  const todayStart = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const yesterdayStart = todayStart - 86400000;

  unpinned.forEach((c) => {
    const updatedAt = new Date(c.updatedAt).getTime();
    if (updatedAt >= todayStart) {
      today.push(c);
    } else if (updatedAt >= yesterdayStart) {
      yesterday.push(c);
    } else {
      older.push(c);
    }
  });

  const sections = [];
  if (pinned.length > 0) {
    sections.push({ title: "已置頂", data: pinned });
  }
  if (today.length > 0) {
    sections.push({ title: "今天", data: today });
  }
  if (yesterday.length > 0) {
    sections.push({ title: "昨天", data: yesterday });
  }
  if (older.length > 0) {
    sections.push({ title: "較早之前", data: older });
  }

  return sections;
}