# Changelog

All notable changes to the `dev_tools` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-28

### Added
- Initial release of the automation tools suite.
- **Core**: `git_utils.py` for git command wrapping and SemVer validation.
- **Scripts**:
    - `commit.py`: Automated local commit interface.
    - `tag.py`: Tag creation with SemVer checks and build metadata support.
    - `push.py`: Push commits and tags to remote.
    - `release.py`: GitHub Release creation (Main vs Prerelease logic).
    - `merge.py`: Interactive branch merging.
    - `branch.py`: Branch management (create, switch, delete).
    - `pr.py`: Pull Request creation via GitHub CLI.
    - `cicd_setup.py`: Generator for GitHub Actions workflows.
- **Entry Point**: `manage.py` interactive menu.
- **Documentation**: `README.md` for architecture and usage.
