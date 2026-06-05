# Sakura Navi App

這是一個基於 React Native 與 Expo 開發的 Sakura Navi 行動端應用程式。

## 🚀 如何啟動 (Getting Started)

### 先決條件

- [Node.js](https://nodejs.org/) (建議使用 LTS 版本)
- iOS 模擬器 (需安裝 Xcode) 或 Android 模擬器 (需安裝 Android Studio)

### 安裝依賴

請在專案根目錄下執行以下指令安裝所需套件：

```bash
npm install
```

### 啟動應用程式

專案使用 Expo CLI，你可以透過以下指令啟動開發伺服器或特定平台的模擬器：

- **啟動 Expo 開發伺服器**：

  ```bash
  npm start
  ```

  > **💡 提示：如果電腦沒有安裝 Xcode 怎麼辦？**  
  > 執行上述 `npm start` 指令後，終端機會顯示一組 QR Code。你只需在實體手機上（iOS 或 Android）安裝 **[Expo Go](https://expo.dev/go)** App，然後直接以手機掃描該 QR Code，就能即時預覽與測試應用程式，完全不需要安裝 Xcode 或 Android Studio！

- **在 iOS 模擬器上運行**：
  ```bash
  npm run ios
  ```
- **在 Android 模擬器上運行**：
  ```bash
  npm run android
  ```
- **在網頁瀏覽器中試作 (Web)**：
  ```bash
  npm run web
  ```

---

## 📂 專案架構 (Project Structure)

本專案採用 [Expo Router](https://docs.expo.dev/router/introduction/) 進行檔案路由 (File-based Routing)，主要目錄結構如下：

```text
sakura-navi-app/
├── app/                  # Expo Router 頁面結構
│   ├── (auth)/           # 認證相關頁面 (登入、註冊、忘記密碼)
│   ├── (onboarding)/     # 初始設定頁面 (建立個人檔案等)
│   ├── (tabs)/           # 底部導覽列切換的主要頁面 (首頁、探索、路徑、個人檔案)
│   ├── chat/             # 聊天室相關頁面
│   ├── _layout.tsx       # 全域佈局設定
│   └── index.tsx         # 應用程式進入點與重定向
├── assets/               # 靜態資源 (圖片、圖示、字體等)
├── components/           # 可複用的 UI 元件
│   ├── chat/             # 聊天室專用元件 (對話框、推薦標籤等)
│   ├── onboarding/       # 初始設定專用元件
│   └── shared/           # 共用元件 (Policy Card 等)
├── docs/                 # 專案文件與規格 (包含開發總則)
├── hooks/                # 自訂 React Hooks (處理聊天邏輯、使用者資料等)
├── ios/ & android/       # 原生專案目錄 (由 Expo Prebuild 生成)
├── services/             # API 請求與後端整合邏輯
├── store/                # 全域狀態管理 (Zustand)
└── types/                # TypeScript 型別定義與契約
```

---

## 🛠 開發指南 (Development Guidelines)

### 1. 技術堆疊

- **框架**：React Native + Expo
- **路由**：Expo Router (File-based routing)
- **狀態管理**：Zustand
- **API 請求**：Axios
- **語言**：TypeScript

### 2. 核心開發原則

- **不破壞既有成果**：修改現有檔案前必須理解上下文，依賴關係明確才可更動。
- **最小化改動**：只修改任務明確要求的功能，不隨意對無關的程式碼進行格式化或「順手重構」。
- **安全第一**：請勿在程式碼中硬編碼 (Hardcode) 機密資料（如 API Keys、Tokens 等），請統一使用環境變數 (`EXPO_PUBLIC_*`) 存取。

### 3. 型別契約保護 (`types/index.ts`)

`types/index.ts` 是一個重要的共用型別契約檔案，任何現存的 `interface` 或 `type` **禁止單方面修改或刪除欄位**。若需變更或擴充，需先評估並在 Commit 中註註明 `[TYPE CONTRACT CHANGE]`，避免影響前後端或 RAG 系統對接。

### 4. API 與狀態管理

- **API 呼叫**：所有的 API 請求必須統一透過 `services/api.ts` 的 `apiClient`（Axios instance）進行，不可在元件內隨意使用 `fetch`。
- **全域狀態 (Zustand)**：儲存使用者資訊 (Profile) 或 Session ID 等全域跨頁面需要的資訊。需持久化的資料應搭配 `AsyncStorage` 使用。
- **本地狀態 (useState)**：負責管理特定元件內部的載入中 (loading) 或彈出視窗 (modal) 的顯示狀態。

### 5. UI 與樣式規範

- 圖片呈現一律使用 `expo-image` 取代原生的 `<Image>`。
- 為了效能考量，請優先使用 `StyleSheet.create`，避免不必要的 Inline styles。
- 請遵守 `components/` 目錄結構，若需新增元件，優先確認 `components/shared/` 內是否已有現成可複用的元件。

> **更多詳細規範請參考：** [docs/DEVELOPMENT_GUIDELINES.md](./docs/DEVELOPMENT_GUIDELINES.md)
