# Changelog

## [1.2.0 Online] - 2025-11-23 23:21:28
### Added
- **MongoDB Integration**:
    - Migrated `bonus_points` and `weekly_reports` to MongoDB Atlas.
    - Data is now persistent across restarts.
- **Web Dashboard**:
    - Added a web interface at the bot's URL.
    - Displays the latest weekly report and bonus points leaderboard.
- **History Command**:
    - Added `/history <week> <year>` to query past weekly reports from the database.

## [1.1.2 Online] - 2025-11-23 22:35:25
### Changed
- **Enhanced Auto-Publish**:
    - `README` & `ROADMAP`: Now use **Embeds** with color highlighting (Green for Latest, Grey for History).
    - `RELEASE_NOTE`: Now checks for version string existence to avoid duplicates.
    - `CHANGELOG`: Continues to support smart history backfilling.
- **Configuration**: Thread IDs are now loaded from `.env` for better security.

## [1.1.1 Online] - 2025-11-23 22:19:18
### Changed
- **Refactor**: Renamed main bot file to `bot.py` for easier deployment.
- **Render**: Updated `render.yaml` to use `python bot.py`.
- **Docs**: Added `ROADMAP.md` and updated `README.md`.

## [1.1.0 Online] - 2025-11-23 17:49:20
### Added
- **Month & Custom Range**: `/compute` now supports `month` (e.g., `month:11`) and custom date ranges (`start_date`, `end_date`).
- **Date Range Display**: All statistics commands (`leaderboard`, `matrix`, etc.) now explicitly show the calculated date range (e.g., "2025-11-01 ~ 2025-11-30").
- **Auto-Publish Docs**: Bot now automatically updates `README`, `ROADMAP`, `CHANGELOG`, and `RELEASE_NOTE` in their respective Forum Threads on startup.

## [1.0 Online] - 2025-11-23 15:12:49
### Added
- **24/7 Online Support**: Integrated Flask web server (`keep_alive.py`) for cloud hosting.
- **Security**: Migrated sensitive data (Token, IDs) to environment variables.
- **Automation**: Added `weekly_report_task` to auto-generate reports every Monday at 00:00 (UTC+8).
- **Timezone**: Standardized all times to Taiwan Time (UTC+8).
- **Deployment Config**: Added `render.yaml` and `requirements.txt` for Render deployment.

## [1.3] - 2025-11-23 04:09:36
### Changed
- **Dynamic Member Fetching**: Replaced hardcoded `USER_IDS` with automatic fetching of all guild members.
- **Week-based Calculation**: Updated `/compute` to accept week numbers and default to the current week (Mon-Sun).

## [1.2] - 2025-11-21 14:18:25
### Fixed
- **Slash Commands**: Fixed registration issues for `trycompute` and other commands.
- **Permissions**: Added checks for teacher-only commands.

## [1.1] - 2025-11-09 12:00:00
- Initial release with basic tracking and grading logic.
