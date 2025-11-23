# OCW Discord Bot (v1.2.1 Online)

## 功能特色
- **成就系統**: 自動頒發成就徽章 (e.g., 🗣️ Chatterbox, ❤️ Supporter)。
- **自動週報**: 每週一凌晨 00:00 (UTC+8) 自動發送上週的統計報告與排行榜。
- **靈活查詢**: 支援 **週 (Week)**、**月 (Month)** 與 **自訂日期 (Custom Date)** 統計。
- **24/7 在線**: 內建 Web Server (Flask) 與 Render 部署設定，可配合 UptimeRobot 實現全天候運作。

## 檔案結構
- `bot.py`: 機器人核心程式碼 (v1.2.0)。
- `keep_alive.py`: 用於保持 Render 服務運作的網頁伺服器。
- `requirements.txt`: Python 套件需求清單。
- `render.yaml`: Render 部署設定檔。

## 部署教學
詳細部署步驟請參考 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)。

### 快速開始 (Render)
1. Fork 本專案或上傳至您的 GitHub。
2. 在 Render 建立 Web Service (Root Directory 設為 `OCW-discord-bot-online`)。
3. 設定環境變數 (參考下方表格)。
4. 使用 UptimeRobot 監控 Render 網址以防止休眠。

## 環境變數
| 變數名稱 | 說明 |
| --- | --- |
| `TOKEN` | Bot Token |
| `GUILD_ID` | 伺服器 ID |
| `FORUM_ID` | 論壇頻道 ID |
| `ANNOUNCEMENT_CHANNEL_ID` | 週報發送頻道 ID |
| `MONGO_URI` | MongoDB 連線字串 |
