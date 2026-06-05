# Sakura-Navi 開發總則

**版本：** v1.0.0  
**更新日期：** 2026-04-11  
**適用範圍：** 所有 AI 協作工具（Claude Code 等）及人工開發者

---

## 1. 核心原則

### 1.1 不破壞既有成果
- **禁止**在未明確授權的情況下刪除任何檔案、目錄或程式碼。
- 修改現有檔案前必須先 `Read` 完整內容，理解上下文後再進行精確 `Edit`。
- 重構或搬移程式碼前，需確認沒有其他模組依賴該檔案路徑。

### 1.2 最小化改動原則
- 只修改任務明確要求的部分，不附帶清理、重構或「順手改善」。
- 不增加未被要求的功能、設定選項、或彈性擴充點（YAGNI）。
- 不替未變動的程式碼加上 docstring、型別標注或 comment。

### 1.3 安全第一
- 不在程式碼中硬寫 API key、token、密碼等機密資料；一律使用環境變數（`EXPO_PUBLIC_*`）。
- 不生成含有 SQL Injection、XSS、Command Injection 等 OWASP Top 10 漏洞的程式碼。
- 若發現已有安全漏洞，立即修正並告知使用者。

---

## 2. 檔案與目錄規則

### 2.1 不得刪除的檔案
| 路徑 | 原因 |
|------|------|
| `docs/` 下所有 `*.md` | 規格文件，異動需人工確認 |
| `types/index.ts` | 三端共同型別契約，不得單方面修改欄位 |
| `.env` / `.env.local` | 環境設定，不得覆蓋或刪除 |
| `app.json` / `app.config.ts` | Expo 設定，須謹慎修改 |

### 2.2 新增檔案規範
- 嚴格遵循 `sakura-navi-frontend-spec.md` §1 所定義的目錄結構。
- 不在規格未定義的位置隨意建立 `utils/`、`lib/`、`helpers/` 等目錄。
- 新增元件前先確認 `components/shared/` 是否已有可複用元件。

### 2.3 禁止建立的檔案類型
- `*.md` 文件（除非使用者明確要求）
- `README.md`（除非使用者明確要求）
- 測試用 mock 資料檔案放在 `src/` 內（應放 `__mocks__/` 或 `fixtures/`）

---

## 3. 型別契約保護

`types/index.ts` 是前端、後端、RAG 三端共同契約：

- **禁止**單方面新增、刪除、或重命名任何 exported interface / type 的欄位。
- 若需變更，必須先在 `docs/` 新增變更提案，並在 commit message 中標明 `[TYPE CONTRACT CHANGE]`。
- 允許新增全新的 interface（不影響現有契約），但需告知使用者。

---

## 4. API 呼叫規範

- 所有 HTTP 請求必須透過 `services/api.ts` 的 `apiClient`（axios instance），不得在元件內直接使用 `fetch` 或另開 axios 實例。
- 錯誤處理一律依照 `sakura-navi-frontend-spec.md` §6 的對照表實作。
- SSE 串流（chat）使用 EventSource 或 fetch + ReadableStream，不得 polling。

---

## 5. 狀態管理規範

- 全域狀態（userId、userProfile、sessionId）使用 Zustand（`store/userStore.ts`）。
- 持久化使用 AsyncStorage，不得使用 localStorage（React Native 不支援）。
- 元件本地 UI 狀態（loading、modal open）用 `useState`，不要塞進 Zustand。

---

## 6. 開發流程規範

### 6.1 變更前確認
在執行任何可能影響多個模組的變更（如更名、搬移、刪除）之前，Claude Code 必須：
1. 列出受影響的檔案清單。
2. 向使用者說明影響範圍。
3. 取得使用者明確確認後才執行。

### 6.2 不可逆操作
以下操作屬於高風險，必須取得使用者明確授權：
- `git reset --hard`、`git push --force`
- 刪除目錄（`rm -rf`）
- 覆蓋 `.env` 等設定檔

### 6.3 Commit 規範
- 使用 Conventional Commits 格式：`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- 型別契約變更需加 `[TYPE CONTRACT CHANGE]` 標記
- 不在未經請求的情況下自動 commit 或 push

---

## 7. Expo / React Native 特定規範

- 遵循 Expo Router 的 file-based routing，不使用 React Navigation 直接配置。
- 使用 `expo-constants` 讀取環境變數，不直接存取 `process.env`（除 `EXPO_PUBLIC_*`）。
- 圖片資源放 `assets/`，並使用 `expo-image` 而非原生 `Image`。
- 樣式優先使用 StyleSheet.create，避免 inline style 物件（效能考量）。
- 不在 production build 中使用 `console.log`；使用條件式 `__DEV__` 控制。

---

## 8. 違規處理

若 Claude Code 判斷某項操作可能違反本總則，應：
1. 停止操作。
2. 向使用者說明衝突點。
3. 提出符合規範的替代方案。
4. 等待使用者指示後再繼續。
