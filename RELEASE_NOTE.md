# Release Note: v1.1.1 Online

## 🚀 部署優化與文件發布

這個版本主要優化了部署流程，並新增了方便的文件發布指令。

### 🔄 部署優化
- **統一檔名**: 核心程式碼已改名為 `bot.py`。
- **自動更新**: Render 設定已更新，未來無論版本如何迭代，都會自動執行最新的 `bot.py`，無需再手動修改設定檔。

### 📚 文件發布指令
新增了一系列指令，讓管理員可以隨時將最新的文件發布到 Discord 頻道：
- `/announce_release_note`: 發布版本更新說明。
- `/announce_changelog`: 發布變更日誌。
- `/announce_readme`: 發布專案說明。
- `/announce_roadmap`: 發布未來規劃。

### 🛠️ 升級說明
- **Render 用戶**: 推送程式碼後，Render 會自動重新部署並執行新版程式。
