<div align="center">

# 🌸 SakuraNavi — 青年局智慧導航平台 🌸

[![授權條款](https://img.shields.io/badge/授權-MIT-pink.svg)](LICENSE)
[![React Native](https://img.shields.io/badge/React%20Native-0.83-blue.svg)](https://reactnative.dev/)
[![Expo](https://img.shields.io/badge/Expo-55-black.svg)](https://expo.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org/)

**✨ 讓每一位青年都能輕鬆找到屬於自己的機會、補助與夢想起點 ✨**

</div>

---

## 😩 我們想解決的問題

**問題**：青年局官網資訊龐雜、散落各處，學生與青年往往不知道自己符合哪些補助、實習或創業計畫的申請資格，每次查詢都得在茫茫文件海中大海撈針。

**解決方案**：SakuraNavi 整合 RAG（檢索增強生成）技術，將青年局所有政策文件、補助公告與新聞資訊結構化，並透過對話式 AI 介面讓使用者用自然語言直接提問，系統精準回答。

**成果**：你只需要說出你的需求，SakuraNavi 就能即時給出相關補助方案、申請連結與重要截止日期，讓找機會從「搜尋苦差事」變成「輕鬆對話」。

---

## ✨ 功能特色

- 💬 **對話式 AI 查詢**：透過自然語言與 RAG 系統互動，即問即答
- 📋 **履歷草稿輔助**：內建履歷（Resume）草稿模組，協助青年整理個人經歷
- 🌐 **國際交流資訊**：整合海外實習、藝術家交流、獎學金等國際機會
- 💰 **青年補助總覽**：創業貸款、留學貸款、實習津貼等補助一站查詢
- 📢 **最新公告追蹤**：公部門工讀、職場體驗計畫即時推播
- 🔐 **帳號安全管理**：JWT 身份驗證、bcrypt 密碼加密保護個人資料
- 🤖 **智慧客服系統**：結合 LLM 與向量嵌入（Embeddings）的多輪對話支援
- 📱 **跨平台行動應用**：支援 iOS、Android 與 Web，一套程式碼全平台覆蓋

---

## 🚀 快速開始

本專案為 Monorepo 架構，包含兩個獨立子專案：

| 子專案 | 路徑 | 說明 |
|--------|------|------|
| 行動端應用 | `YTP_2026_Hackthon_SakuraNaviApp/` | React Native + Expo |
| 後端服務 | `YTP_2026_Hackthon_SakuraNaviBackend/` | FastAPI + Python |

---

### 後端服務啟動

**環境需求**：Python 3.11+、PostgreSQL

```bash
# 進入後端目錄
cd YTP_2026_Hackthon_SakuraNaviBackend

# 建立並啟動虛擬環境
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

# 安裝依賴套件
pip install -r requirements.txt

# 複製並設定環境變數
cp .env.example .env
# 請編輯 .env，填入資料庫連線字串與 LLM API 金鑰

# 執行資料庫遷移
alembic upgrade head

# 啟動開發伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

啟動後，API 文件可於 `http://localhost:8000/docs` 查閱（Swagger UI）。

---

### 行動端應用啟動

**環境需求**：Node.js LTS

```bash
# 進入應用目錄
cd YTP_2026_Hackthon_SakuraNaviApp

# 安裝依賴套件
npm install

# 啟動 Expo 開發伺服器
npm start
```

> **提示**：沒有安裝 Xcode 或 Android Studio 也沒關係！執行 `npm start` 後，終端機會顯示一組 QR Code，你只需在實體手機上安裝 **[Expo Go](https://expo.dev/go)**，掃描 QR Code 即可即時預覽。

你也可以針對特定平台啟動：

```bash
npm run ios       # 在 iOS 模擬器上運行（需安裝 Xcode）
npm run android   # 在 Android 模擬器上運行（需安裝 Android Studio）
npm run web       # 在網頁瀏覽器中預覽
```

---

## 📂 專案架構

### 後端（FastAPI）

```text
YTP_2026_Hackthon_SakuraNaviBackend/
├── app/
│   ├── application/          # 應用層：使用案例與業務邏輯
│   │   ├── admin/            # 管理員功能
│   │   ├── chat/             # 對話管理
│   │   ├── customer_service/ # 客服系統
│   │   ├── rag/              # RAG 查詢與文件處理
│   │   ├── resume/           # 履歷管理
│   │   ├── resume_draft/     # 履歷草稿
│   │   └── user/             # 使用者管理
│   ├── core/                 # 核心設定與例外處理
│   ├── domains/              # 領域模型（Domain Model）
│   ├── infrastructure/       # 基礎設施層
│   │   ├── auth/             # JWT 驗證
│   │   ├── db/               # 資料庫連線（PostgreSQL + SQLAlchemy）
│   │   ├── embeddings/       # 向量嵌入
│   │   ├── llm/              # 大型語言模型整合
│   │   ├── rag/              # RAG 管道
│   │   └── repositories/     # 資料存取層
│   ├── interfaces/
│   │   └── api/v1/           # REST API 路由（auth, chat, rag, users...）
│   └── main.py               # FastAPI 應用程式入口
├── rag_docs/                 # RAG 知識庫文件（Markdown）
├── rag_config.yaml           # RAG 標籤與分類規則設定
├── alembic/                  # 資料庫遷移腳本
└── requirements.txt
```

### 行動端（React Native + Expo）

```text
YTP_2026_Hackthon_SakuraNaviApp/
├── app/                      # Expo Router 頁面結構（檔案路由）
│   ├── (auth)/               # 認證相關頁面（登入、註冊、忘記密碼）
│   ├── (chat-detail)/        # 聊天室詳細頁面
│   ├── (knowledge)/          # 知識庫瀏覽頁面
│   ├── (policy)/             # 政策資訊頁面
│   ├── (tabs)/               # 底部導覽列主要頁面
│   ├── _layout.tsx           # 全域佈局設定
│   └── index.tsx             # 應用程式進入點
├── components/               # 可複用 UI 元件
├── hooks/                    # 自訂 React Hooks
├── services/                 # API 請求與後端整合邏輯
├── store/                    # 全域狀態管理（Zustand）
├── types/                    # TypeScript 型別定義與契約
├── docs/                     # 開發規範文件
└── assets/                   # 靜態資源（圖片、圖示）
```

---

## 🛠 技術堆疊

### 行動端

| 類別 | 技術 | 版本 |
|------|------|------|
| 框架 | React Native | 0.83 |
| 開發平台 | Expo | 55 |
| 路由 | Expo Router（檔案路由） | 55 |
| 狀態管理 | Zustand | 5.x |
| 資料請求 | TanStack Query | 5.x |
| UI 元件 | rn-primitives + NativeWind | — |
| 動畫 | React Native Reanimated | 4.x |
| 語言 | TypeScript | 5.9 |

### 後端

| 類別 | 技術 | 版本 |
|------|------|------|
| 框架 | FastAPI | 0.136 |
| ORM | SQLAlchemy | 2.0 |
| 資料庫 | PostgreSQL（psycopg3） | — |
| 資料庫遷移 | Alembic | 1.18 |
| 驗證 | python-jose（JWT）+ bcrypt | — |
| 機器學習 | PyTorch + Transformers（HuggingFace） | — |
| 排程 | APScheduler | 3.11 |
| 日誌 | Loguru | 0.7 |
| 語言 | Python | 3.11+ |

---

## 📚 RAG 知識庫

後端整合了臺北市政府青年局的官方文件，涵蓋以下五大類別：

| 標籤（Tag） | 顯示名稱 | 說明 |
|-------------|----------|------|
| `entrepreneurship` | 創業諮詢 | 青年創業補助、共享空間、創業相關計畫 |
| `international` | 國際交流 | 海外實習、藝術家交流、中文獎學金 |
| `youth_subsidy` | 青年補助 | 創業貸款、留學貸款、實習津貼、職涯培力 |
| `latest_news` | 最新公告 | 工讀生招募、職場體驗計畫錄取名單 |
| `policy_news` | 政策新聞 | 青年節公益活動、暑期工讀、青年學堂 |

文件儲存於 `rag_docs/` 目錄，系統依照 `rag_config.yaml` 中定義的分類規則（Metadata 優先、Filename Pattern 次之）進行自動標籤分類。

---

## 🧪 測試

### 行動端測試

```bash
cd YTP_2026_Hackthon_SakuraNaviApp

# 執行單元測試
npm test

# 監聽模式（開發時使用）
npm run test:watch

# TypeScript 型別檢查
npm run typecheck

# Lint 檢查
npm run lint

# E2E 測試（需安裝 Maestro）
npm run e2e:maestro
```

### 後端測試

```bash
cd YTP_2026_Hackthon_SakuraNaviBackend

# 執行所有測試
pytest

# 顯示詳細輸出
pytest -v

# 執行特定測試模組
pytest app/tests/test_rag.py
```

---

## 👥 開發團隊

| 成員 | GitHub |
|------|--------|
| yuzen9622 | [@yuzen9622](https://github.com/yuzen9622) |
| nangong5421 | [@nangong5421](https://github.com/nangong5421) |
| Yuchen9487 | [@Yuchen9487](https://github.com/Yuchen9487) |

本專案為 **YTP 2026 青年黑客松（Hackathon）** 參賽作品，三人協力開發完成。

---

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權。你可以自由使用、修改與散佈本專案，惟須保留原始著作權聲明。
