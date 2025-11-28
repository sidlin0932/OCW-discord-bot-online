# Dev Tools Automation

這是一個模組化的 Python 自動化工具庫，旨在簡化 Git 與 GitHub 的日常操作流程。

## 架構設計 (Architecture)

本工具庫採用模組化設計，核心邏輯封裝於 `core/`，各項功能獨立於 `scripts/`，並透過 `manage.py` 提供統一入口。

```text
dev_tools/
├── core/
│   ├── git_utils.py       # 封裝 Git 指令與 SemVer 驗證
├── scripts/
│   ├── commit.py          # 1. 本地 Commit
│   ├── tag.py             # 2. 建立 Tag (含 SemVer 檢查)
│   ├── push.py            # 3. 推送 Commit 與 Tag
│   ├── release.py         # 4. GitHub Release 發布
│   ├── merge.py           # 5. 分支合併
│   ├── branch.py          # 6. 分支管理
│   ├── pr.py              # 7. 建立 Pull Request
│   └── cicd_setup.py      # 8. 生成 CI/CD Workflow
└── manage.py              # 主選單入口
```

## 使用方式 (Usage)

在專案根目錄下執行：

```bash
python dev_tools/manage.py
```

或者直接執行個別腳本：

```bash
python dev_tools/scripts/commit.py
```

## 功能說明

1.  **Commit**: 偵測變更並提交。
2.  **Tag**: 建立符合 SemVer 的標籤 (如 `v1.0.0`)，Prerelease 自動加上時間戳記。
3.  **Push**: 同步 Commits 與 Tags 到遠端。
4.  **Release**: 呼叫 GitHub API 發布 Release (需安裝 `gh` CLI)。
5.  **Merge**: 互動式合併分支。
6.  **Branch**: 建立、切換、刪除分支。
7.  **PR**: 快速建立 Pull Request。
8.  **CI/CD**: 生成 GitHub Actions 設定檔。

## 依賴 (Dependencies)

- Python 3.x
- Git
- GitHub CLI (`gh`) - 用於 Release 與 PR 功能
