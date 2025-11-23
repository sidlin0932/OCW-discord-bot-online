# OCW Discord Bot (Online Version)

這是一個專為 OCW Discord 伺服器設計的自動化機器人，具備學生成績統計、出席率追蹤、排行榜以及自動週報功能。

## 功能特色
- **自動統計**: 追蹤使用者的訊息數與表情符號反應數。
- **成績計算**: 根據互動活躍度計算分數、等級 (A+, A, B...) 與 GPA。
- **成就系統**: 自動頒發成就徽章 (e.g., 🗣️ Chatterbox, ❤️ Supporter)。
- **自動週報**: 每週一凌晨 00:00 (UTC+8) 自動發送上週的統計報告與排行榜。
- **靈活查詢**: 支援 **週 (Week)**、**月 (Month)** 與 **自訂日期 (Custom Date)** 統計。
- **24/7 在線**: 內建 Web Server (Flask) 與 Render 部署設定，可配合 UptimeRobot 實現全天候運作。

## 檔案結構
- `emoji_online_1.1.0.py`: 機器人核心程式碼 (v1.1.0)。
- `keep_alive.py`: 用於保持 Render 服務運作的網頁伺服器。
- `requirements.txt`: Python 套件需求清單。
- `render.yaml`: Render 部署設定檔。

## 部署教學
詳細部署步驟請參考 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) (或參考本儲存庫中的說明)。

### 快速開始 (Render)
1. Fork 本專案或上傳至您的 GitHub。
2. 在 Render 建立 Web Service。
3. 設定環境變數 (`TOKEN`, `GUILD_ID` 等)。
4. 使用 UptimeRobot 監控 Render 網址以防止休眠。

## 環境變數
| 變數名稱 | 說明 |
| --- | --- |
| `TOKEN` | Discord Bot Token |
| `GUILD_ID` | 伺服器 ID |
| `FORUM_ID` | 論壇頻道 ID |
| `ANNOUNCEMENT_CHANNEL_ID` | 週報發送頻道 ID |
