# 更新日誌 (Changelog)

## [1.2.2 Online] - 2025-11-24 00:12:00
### 新增功能
- **趨勢圖儀表板**:
    - 新增 `/trends` 頁面，使用 Chart.js 顯示學生歷史得分折線圖。
    - 支援學生多選篩選功能（可同時比較多位學生的進步曲線）。
- **歷史數據自動計算**:
    - Bot 啟動時自動計算從第 40 週（2025-10-01）到當前週的所有歷史數據。
    - 已存在的週次會自動跳過，避免重複計算。

## [1.2.1 Online] - 2025-11-23 23:45:08
### 新增功能
- **DEPLOY_GUIDE 自動回覆**:
    - Bot 啟動時會自動在 README 論壇貼文下方以**文件附件**形式發布 `DEPLOY_GUIDE.md`。
    - 避免長文占用版面，點擊即可查看完整部署指南。
### 改進項目
- **文件完善**:
    - 新增詳細的 `DEPLOY_GUIDE.md`，包含 MongoDB 設定與環境變數說明。
    - 更新 `README.md`，明確標註 Render Root Directory 設定重點。
    - 優化 `ROADMAP.md`，聚焦實用 OCW 社群功能 (讀書會、資源庫、Office Hours)。

## [1.2.0 Online] - 2025-11-23 23:21:28
### 新增功能
- **資料庫整合 (MongoDB Integration)**:
    - 將 `bonus_points` (加分) 與 `weekly_reports` (週報) 遷移至 MongoDB Atlas。
    - 確保資料在 Bot 重啟後不會遺失 (持久化)。
- **網頁儀表板 (Web Dashboard)**:
    - 在 Bot 的 Render 網址新增了網頁介面。
    - 顯示最新的週報與加分排行榜。
- **歷史查詢指令 (History Command)**:
    - 新增 `/history <week> <year>` 指令，可從資料庫查詢過去的週報。

## [1.1.2 Online] - 2025-11-23 22:35:25
### 變更項目
- **增強自動發布 (Enhanced Auto-Publish)**:
    - `README` & `ROADMAP`: 改用 **Embeds** 顯示，並以顏色區分最新版 (綠色) 與歷史版 (灰色)。
    - `RELEASE_NOTE`: 新增版本號檢查機制，避免重複發布。
    - `CHANGELOG`: 持續支援智慧歷史補齊功能。
- **設定優化 (Configuration)**: 將 Thread IDs 改從 `.env` 讀取，提升安全性。

## [1.1.1 Online] - 2025-11-23 22:19:18
### 變更項目
- **重構 (Refactor)**: 將主程式重新命名為 `bot.py` 以利部署。
- **Render 設定**: 更新 `render.yaml` 以執行 `python bot.py`。
- **文件**: 新增 `ROADMAP.md` 並更新 `README.md`。

## [1.1.0 Online] - 2025-11-23 17:49:20
### 新增功能
- **月報與自訂範圍**: `/compute` 現在支援 `month` (如 `month:11`) 與自訂日期範圍 (`start_date`, `end_date`)。
- **日期範圍顯示**: 所有統計指令 (`leaderboard`, `matrix` 等) 現在都會明確顯示計算的日期範圍 (例如 "2025-11-01 ~ 2025-11-30")。
- **自動發布文件**: Bot 啟動時會自動將 `README`, `ROADMAP`, `CHANGELOG`, `RELEASE_NOTE` 更新至對應的論壇貼文。

## [1.0 Online] - 2025-11-23 15:12:49
### 新增功能
- **24/7 在線支援**: 整合 Flask 網頁伺服器 (`keep_alive.py`) 以支援雲端託管。
- **安全性**: 將敏感資料 (Token, IDs) 遷移至環境變數。
- **自動化**: 新增 `weekly_report_task`，每週一 00:00 (UTC+8) 自動產生報告。
- **時區**: 將所有時間標準化為台灣時間 (UTC+8)。
- **部署設定**: 新增 `render.yaml` 與 `requirements.txt` 供 Render 部署使用。

## [1.3] - 2025-11-23 04:09:36
### 變更項目
- **動態成員獲取**: 將硬編碼的 `USER_IDS` 改為自動獲取所有伺服器成員。
- **週次計算**: 更新 `/compute` 接受週數並預設為當前週 (週一至週日)。

## [1.2] - 2025-11-21 14:18:25
### 修正項目
- **Slash Commands**: 修復 `trycompute` 等指令的註冊問題。
- **權限**: 為老師專用指令新增權限檢查。

## [1.1] - 2025-11-09 12:00:00
- 初始版本，包含基本的追蹤與評分邏輯。
