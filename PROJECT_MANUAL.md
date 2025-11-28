# 📘 專案架構與工作流手冊 (Project Manual)

> **給未來的自己**：
> 當你想要開啟一個新專案，並希望它具備擴展到 v2.0.0 甚至更大規模的潛力時，請參考這份指南。
> 這不僅是操作手冊，更是架構設計的哲學。

---

## 1. 為何要這樣設計？ (The Why)

在開始動手之前，先理解為什麼我們不直接在 `main` 上面改程式碼。

### 🛡️ 穩定性 (Stability)
- **問題**: 如果所有人都在 `main` 上開發，一旦有人推了壞掉的程式碼，整個專案就掛了，無法部署。
- **解法**: **Git Flow**。
    - `main` 是神聖的，永遠保持「可部署」狀態。
    - `develop` 是緩衝區，容許短暫的不穩定。
    - `feat/*` 是隔離區，你的實驗不會影響別人。

### 🔍 可追溯性 (Traceability)
- **問題**: `git log` 充滿了 "update", "fix bug", "aaaa" 這種無意義的訊息，三個月後根本看不懂改了什麼。
- **解法**: **Conventional Commits**。
    - 強制使用 `feat:`, `fix:` 等前綴，讓機器能讀懂你的 commit，甚至自動生成 Changelog。

### 🤖 自動化 (Automation)
- **問題**: 每次發布都要手動跑測試、手動檢查語法，容易忘記或偷懶。
- **解法**: **CI/CD (GitHub Actions)**。
    - 讓機器人幫你把關。只要 PR 一開，自動跑測試，不通過就不準合併。

---

## 2. 如何建立這套工作流？ (The How - Setup)

如果你開了一個全新的空專案，請照著做：

### Step 1: Git 初始化與分支建立
```bash
# 1. 初始化
git init
git checkout -b main
# (寫一些初始代碼...)
git add .
git commit -m "chore: initial commit"

# 2. 建立開發核心分支
git checkout -b develop
git push -u origin develop
```

### Step 2: 設定 GitHub 保護規則 (Branch Protection)
*這是關鍵！防止手滑直接 push 到 main。*
1.  去 GitHub Repo -> **Settings** -> **Branches**.
2.  Add rule for `main`:
    - [x] **Require a pull request before merging** (強制走 PR).
    - [x] **Require status checks to pass before merging** (強制 CI 通過).
3.  Add rule for `develop`:
    - 同上，保護開發分支不被壞代碼汙染。

### Step 3: 建立 CI 流程
在專案根目錄建立 `.github/workflows/ci.yml`：
*(內容請參考專案中的實際檔案)*

---

## 3. 如何使用這套工作流？ (The How - Usage)

### 🔄 日常開發循環 (The Daily Loop)
1.  **切換環境**: `git checkout develop` -> `git pull`
2.  **開新戰場**: `git checkout -b feat/新功能名稱`
3.  **存檔**: `git commit -m "feat: 實作了XXX功能"`
4.  **發送**: `git push origin feat/新功能名稱`
5.  **合併**: 在 GitHub 開 PR -> 等 CI 通過 -> Squash & Merge。

### 🚀 版本發布循環 (The Release Loop)
當 `develop` 累積了足夠功能，準備發布 v1.3.2 時：
1.  **建立發布分支**: `git checkout -b release/v1.3.2 develop`
2.  **最後調整**: 更新版本號、更新 CHANGELOG.md。
3.  **合併回 Main**: 發 PR 將 `release/v1.3.2` 合併進 `main`。
4.  **打標籤**: `git tag v1.3.2` -> `git push --tags`
5.  **同步回 Develop**: 將 `release/v1.3.2` 也合併回 `develop` (確保開發版也有版號變更)。

---

## 4. 檔案結構參考
一個成熟的專案應該包含這些管理文件：
- `README.md`: 專案介紹。
- `CHANGELOG.md`: 給人看的更新日誌。
- `CONTRIBUTING.md` (或本手冊): 給開發者看的工作流指南。
- `.github/workflows/*.yml`: 自動化腳本。
