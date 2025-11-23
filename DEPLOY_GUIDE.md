# 🚀 OCW Discord Bot 部署指南 (Render)

本指南將引導您將 Bot 部署至 **Render** 雲端平台，實現 24/7 全天候運作。

## 1. 準備工作
- 一個 [GitHub](https://github.com/) 帳號。
- 一個 [Render](https://render.com/) 帳號 (可直接用 GitHub 登入)。
- 一個 [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) 帳號 (用於資料庫)。
- 一個 [UptimeRobot](https://uptimerobot.com/) 帳號 (用於防止 Bot 休眠)。

## 2. 上傳程式碼
1. 將本專案的所有檔案 (包含 `OCW-discord-bot-online` 資料夾內的檔案) 推送 (Push) 到您的 GitHub Repository。
2. 確保 Repository 是 **Public (公開)** 或 **Private (私有)** 皆可。

## 3. 在 Render 建立服務
1. 登入 [Render Dashboard](https://dashboard.render.com/)。
2. 點擊 **"New +"** -> **"Web Service"**。
3. 選擇 **"Build and deploy from a Git repository"**。
4. 連結您的 GitHub 帳號，並選擇剛剛上傳的 Repository。

## 4. 設定服務參數
在建立頁面中，填寫以下資訊：
- **Name**: 給您的服務取個名字 (例如 `ocw-discord-bot`)。
- **Region**: 選擇離台灣較近的節點 (例如 `Singapore`)。
- **Branch**: 選擇 `main` (或您使用的分支)。
- **Root Directory**: `OCW-discord-bot-online` (⚠️ **重要**：因為我們的程式碼在這個資料夾內)。
- **Runtime**: `Python 3`.
- **Build Command**: `pip install -r requirements.txt`.
- **Start Command**: `python bot.py`.
- **Instance Type**: 選擇 **Free** (免費方案)。

## 5. 設定環境變數 (Environment Variables)
這是最重要的一步！Bot 需要這些變數才能運作。
在頁面下方的 **"Environment Variables"** 區域，點擊 **"Add Environment Variable"** 逐一加入：

| Key | Value (範例) | 說明 |
| --- | --- | --- |
| `TOKEN` | `MTE...` | 您的 Discord Bot Token |
| `GUILD_ID` | `123456789` | 伺服器 ID |
| `FORUM_ID` | `987654321` | 論壇頻道 ID |
| `ANNOUNCEMENT_CHANNEL_ID` | `1122334455` | 週報發送頻道 ID |
| `MONGO_URI` | `mongodb+srv://...` | MongoDB 連線字串 (含密碼) |
| `THREAD_ID_README` | `144...` | README 貼文 ID |
| `THREAD_ID_ROADMAP` | `144...` | ROADMAP 貼文 ID |
| `THREAD_ID_CHANGELOG` | `144...` | CHANGELOG 貼文 ID |
| `THREAD_ID_RELEASE_NOTE` | `144...` | RELEASE_NOTE 貼文 ID |

*注意：Thread ID 可以在 Bot 第一次執行並自動發布後，從 Discord 複製貼上回來更新。*

## 6. 部署與驗證
1. 點擊 **"Create Web Service"**。
2. Render 會開始自動建置 (Build) 與部署 (Deploy)。
3. 等待幾分鐘，直到看到 **"Build successful"** 和 **"Deploy successful"**。
4. 檢查 Logs (日誌)，確認看到 `✅ Bot 已登入` 和 `✅ MongoDB 連線設定完成`。

## 7. 設定 UptimeRobot (防止休眠)
Render 的免費版會在 15 分鐘無流量後休眠。我們需要用 UptimeRobot 定時「敲」它。
1. 登入 [UptimeRobot](https://uptimerobot.com/)。
2. 點擊 **"Add New Monitor"**。
3. **Monitor Type**: `HTTP(s)`.
4. **Friendly Name**: `OCW Bot`.
5. **URL (or IP)**: 貼上 Render 給您的網址 (例如 `https://ocw-discord-bot.onrender.com`)。
6. **Monitoring Interval**: `5 minutes`.
7. 點擊 **"Create Monitor"**。

恭喜！您的 Bot 現在已經是 24/7 全天候運作了！🎉
