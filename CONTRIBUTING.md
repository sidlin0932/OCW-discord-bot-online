# Contributing Guide

歡迎來到 OCW Discord Bot 專案！即使這是個人專案，遵循規範也能讓開發更順暢。

## 開發流程 (Workflow)

1.  **分支策略**:
    - `main`: 正式發布版本，隨時可部署。
    - `develop`: 開發主幹，整合所有功能。
    - `feature/xxx`: 新功能開發 (從 `develop` 分出)。
    - `hotfix/xxx`: 緊急修復 (從 `main` 分出)。

2.  **Commit 規範**:
    - 格式: `type: description`
    - 範例: `feat: add new command`, `fix: resolve crash issue`

3.  **工具使用**:
    - 請使用 `python dev_tools/manage.py` 來進行 Commit, Tag, Push 等操作，確保流程一致。

## 環境設定

請參考 `BUILD.md` 進行環境建置。
