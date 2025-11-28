## 🚀 快速 PR 指令（複製貼上即可）

### 選項 1：使用 GitHub CLI（推薦，最快）

```bash
# 完整流程（一次性執行所有步驟）
git push origin hotfix/v1.3.2 &amp;&amp; gh pr create --base main --head hotfix/v1.3.2 --title "Hotfix v1.3.2: Fix critical /compute bug" --body "修復 /compute 指令的成員過濾邏輯錯誤，詳見 CHANGELOG.md" &amp;&amp; gh pr merge --merge &amp;&amp; git checkout main &amp;&amp; git pull origin main
```

### 選項 2：沒有 GitHub CLI（手動網頁）

#### Step 1: Push 分支
```bash
git push origin hotfix/v1.3.2
```

#### Step 2: 訪問此連結創建 PR
```
https://github.com/sidlin0932/OCW-discord-bot-online/compare/main...hotfix/v1.3.2
```

#### Step 3: 在網頁上填寫
- **Title**: `Hotfix v1.3.2: Fix critical /compute bug`
- **Description**: 
  ```
  ## 🐛 Critical Bug Fix
  修復 `/compute` 指令無法執行的邏輯錯誤
  
  ### 變更內容
  - 修復 `_fetch_data` 函數成員過濾條件（bot.py line 149）
  - 原始錯誤：`if not member.bot or member.id == BOT_ID`
  - 修正為：`if not member.bot and member.id != BOT_ID`
  
  ### 影響
  此 bug 導致 `/compute` 無法統計任何學生數據
  
  詳見 CHANGELOG.md
  ```

#### Step 4: 點擊按鈕
1. **Create Pull Request**（綠色按鈕）
2. **Merge pull request**（審核後點擊）
3. **Confirm merge**

#### Step 5: 同步本地
```bash
git checkout main
git pull origin main
```

---

## 📝 備註
- GitHub **無法完全自動化** PR（需要手動點擊 merge）
- 使用 **GitHub CLI** 是最接近自動化的方式
- Push 後 GitHub 會在終端顯示快速 PR 連結
