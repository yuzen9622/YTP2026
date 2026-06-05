# Frontend Expo Project Development Manual (Feature-Based Architecture)

This document provides the standard development guidelines and architectural patterns for the Sakura-Navi Expo React Native application, heavily emphasizing a **Feature-Based Architecture**.

## 1. 核心架構原則：Feature-Based (Feature-Sliced)

不按照技術分層（例如全部的 hooks 放一起、全部的 components 放一起），而是依照**業務功能（Feature）**來分群。一個 Feature 是一個自包含的模組，實作特定的業務能力（例如：`auth`, `chat`, `policy`, `onboarding`）。

### 優勢

- **高內聚**：與單一功能相關的所有程式碼都在同一個地方。
- **低耦合**：各 Feature 之間透過明確的公開 API (`index.ts`) 進行溝通。
- **可擴展性**：新加入的開發者可以專注理解單一 Feature，不需要在一開始就看懂整個專案。

---

## 2. 目錄結構

我們的專案預計逐漸向此結構靠攏：

```
sakura-navi-app/
├── app/                  # Expo Router 路由層 (僅負責路由和畫面膠水層)
│   ├── (auth)/
│   ├── (tabs)/
│   └── _layout.tsx
├── src/                  # 所有應用程式的原始碼
│   ├── features/         # 功能模組 (應用的核心)
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── onboarding/
│   │   └── policy/
│   ├── components/       # 共用的、笨的 UI 元件 (如客製化 Buttons, Inputs)
│   ├── hooks/            # 全域共用的 hooks
│   ├── lib/              # 第三方套件設定檔 (Axios, Zustand, Sentry)
│   ├── types/            # 全域型別定義
│   └── utils/            # 輔助函式 (格式化、驗證等)
```

### Feature 模組的內部結構

每一個放置於 `src/features/<feature-name>/` 下的功能模組，都應該遵循可預期的內部結構。以 `chat` 特徵為例：

```
src/features/chat/
├── api/                  # 專屬於此功能的 API 請求函式
│   └── send-message.ts
├── components/           # 專屬於此功能的元件
│   ├── message-bubble.tsx
│   └── suggest-chip.tsx
├── hooks/                # 專屬於此功能的 React hooks
│   └── use-chat.ts
├── store/                # 專屬於此功能的狀態 (Zustand slices)
│   └── chat-store.ts
├── types/                # 專屬於此功能的 TypeScript 型別
│   └── index.ts
└── index.ts              # 此功能模組的公開 API 入口
```

---

## 3. 嚴格的依賴規則

1. **模組隔離 (Feature Isolation)：** 一個 Feature 可以引入全域共用的資料夾（如 `src/components`, `src/lib`, `src/types`），但**絕對不能**直接引入其他 Feature 內部的檔案。
2. **公開 API (Public API)：** 如果 `Feature A` 需要用到 `Feature B` 的東西，必須透過 `Feature B` 的 `index.ts`（公開 API）來引入。
3. **路由層 (Routing Layer)：** 在 `app/` 目錄下的 Expo Router 檔案應保持**極少邏輯**。它們的主要作用是匯入 Feature 提供的畫面元件，並對應到特定的網址路由。

**模組公開 API 的範例 (`src/features/chat/index.ts`)：**

```typescript
export * from "./components/chat-screen";
export * from "./hooks/use-chat";
export type { ChatMessage, ChatSession } from "./types";
// 請勿匯出內部的輔助函式或私有元件
```

---

## 4. UI 元件 vs Feature 元件

- **共用 UI (`src/components/ui/`)**：可重複使用、與業務無關的元件（例如 `Button.tsx`, `TextInput.tsx`）。它們不處理業務邏輯或狀態。
- **Feature 元件 (`src/features/.../components/`)**：與業務邏輯緊密相連的智慧型元件。負責串接 Zustand store、發送 API 請求、重組 UI 呈現複雜視圖。

---

## 5. 狀態管理與 API 呼叫

- **全域狀態**：使用 **Zustand**。保持全域狀態輕量，僅儲存真正跨模組的資料（例如：使用者的 Token、User Profile）。
- **Feature 狀態**：如果需要，可以將 Zustand 拆分成多個與 Feature 相關的 slice，並置於 `features/<feature>/store/`。
- **API 呼叫**：放置於 `src/features/<feature>/api/` 中。這能讓我們未來更輕易地抽換底層的資料請求庫。
- **API 實體**：已設定好的 Axios `apiClient` 應統一放置於共用層（目前為 `services/api.ts`，未來建議移至 `src/lib/api.ts`）。

---

## 6. Expo Router 路由規劃

`app/` 目錄僅用於定義網址樹與導覽。
範例：`app/(tabs)/chat.tsx`

```tsx
import { ChatScreen } from "@/features/chat";

export default function ChatRoute() {
  return <ChatScreen />;
}
```

---

## 7. 漸進式重構方向 (Layer-Based -> Feature-Based)

目前專案使用的是 Layer-Based 架構（`components/`, `hooks/`, `services/`, `store/`）。在未來開發或重構時的步驟：

1. **辨識業務領域**：將一組相關檔案歸類為同一個 Feature（例如：`use-chat.ts`, `chat-service.ts`, `message-bubble.tsx`）。
2. **建立 Feature 目錄**：在 `src/features/chat/` 下建立對應結構。
3. **搬移檔案**：將這些檔案移至 `api/`, `hooks/`, `components/` 目錄。
4. **重新匯出**：在 `src/features/chat/index.ts` 匯出所需的 API。
5. **更新引入路徑**：修正路由層及其他地方的匯入路徑。

---

## 8. TypeScript 型別的安全契約

- 請保持全域型別層 `types/index.ts` 的穩定（根據後端與 RAG 的 API 規格）。
- 若某個型別僅限於單一 Feature 內部使用（例如某個 Component 的 Props），請將它定義在對應的 `src/features/<feature>/types/index.ts` 之中。

## 9. Store 寫法規範

- 定義store時，請採用`interface xxxState`定義store參數,`interface xxxAction` 定義store方法
- 使用store時，請使用 const {} = usexxxStore()寫法解耦寫法來使用store
