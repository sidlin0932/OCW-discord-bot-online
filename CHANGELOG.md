# Changelog

## [1.1.1 Online] - 2025-11-23
### Changed
- **Refactor**: Renamed main bot file to `bot.py` for easier deployment.
- **Documentation**: Added `ROADMAP.md` and announcement commands.

## [1.1.0 Online] - 2025-11-23
### Added
- **Month & Custom Range**: `/compute` now supports `month` (e.g., `month:11`) and custom date ranges (`start_date`, `end_date`).
- **Date Range Display**: All statistics commands (`leaderboard`, `matrix`, etc.) now explicitly show the calculated date range (e.g., "2025-11-01 ~ 2025-11-30").
- **Announce Docs**: Added `/announce_release_note`, `/announce_changelog`, `/announce_readme`, `/announce_roadmap` for admins to post documentation.

## [1.0 Online] - 2025-11-23
### Added
- **24/7 Online Support**: Integrated Flask web server (`keep_alive.py`) for cloud hosting.
- **Security**: Migrated sensitive data (Token, IDs) to environment variables.
- **Automation**: Added `weekly_report_task` to auto-generate reports every Monday at 00:00 (UTC+8).
- **Timezone**: Standardized all times to Taiwan Time (UTC+8).
- **Deployment Config**: Added `render.yaml` and `requirements.txt` for Render deployment.

## [1.3] - 2025-11-23
### Changed
- **Dynamic Member Fetching**: Replaced hardcoded `USER_IDS` with automatic fetching of all guild members.
- **Week-based Calculation**: Updated `/compute` to accept week numbers and default to the current week (Mon-Sun).

## [1.2] - 2025-11-21
### Fixed
- **Slash Commands**: Fixed registration issues for `trycompute` and other commands.
- **Permissions**: Added checks for teacher-only commands.

## [1.1] - 2025-11-09
- Initial release with basic tracking and grading logic.
