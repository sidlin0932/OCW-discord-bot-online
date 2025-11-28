---
description: Standard Release Workflow (Commit & Merge to Main)
---

This workflow automates the process of committing changes to the current branch (usually `develop`) and merging them into `main`.

1.  **Check Status**
    // turbo
    `git status`

2.  **Add All Changes**
    // turbo
    `git add .`

3.  **Commit Changes**
    > [!IMPORTANT]
    > Please replace "Update" with a descriptive commit message.
    `git commit -m "Update"`

4.  **Switch to Main**
    // turbo
    `git checkout main`

5.  **Merge Develop**
    // turbo
    `git merge develop`

6.  **Push Main**
    // turbo
    `git push origin main`

7.  **Switch Back to Develop**
    // turbo
    `git checkout develop`
