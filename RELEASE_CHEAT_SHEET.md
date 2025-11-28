# 🚀 快速發布流程 (人類專用版)

這份文件是給 **你 (User)** 看的。
當你不想依賴 AI，或是想了解 AI 到底在後台執行了什麼指令時，請參考這份清單。

對應的 AI 自動化腳本位於：`.agent/workflows/release_workflow.md`

---

## 📋 操作步驟 (Cheatsheet)

在終端機 (Terminal) 依序執行以下指令：

### 1. 檢查狀態
確保目前在 `develop` 分支，且沒有未預期的檔案變更。
```bash
git status
```

### 2. 提交變更 (Commit)
將所有修改加入並提交。
```bash
git add .
git commit -m "你的提交訊息 (例如: Fix /compute bug)"
```

### 3. 合併到主分支 (Merge to Main)
切換到 `main` 並將 `develop` 的內容合併進來。
```bash
git checkout main
git merge develop
```

### 4. 推送上線 (Push)
將更新推送到 GitHub，這通常會觸發 Render 自動部署。
```bash
git push origin main
```

### 5. 回到開發模式 (Back to Develop)
**非常重要！** 發布完後，一定要切回 `develop` 才能繼續開發新功能。
```bash
git checkout develop
```

---

## 💡 常見問題

- **為什麼要切來切去？**
  - 因為 `main` 是正式版，`develop` 是開發版。我們在 `develop` 做好後，才「搬」到 `main` 上面去。
- **忘記切回 develop 會怎樣？**
  - 你會不小心直接在 `main` 上改程式碼，這違反了我們的工作流規定 (雖然 GitHub 會有保護機制擋住你推不上法，但在本地會很亂)。
