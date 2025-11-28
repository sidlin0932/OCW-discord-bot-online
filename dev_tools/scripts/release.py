import sys
import os
import subprocess

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, get_current_branch, check_gh_cli, get_tags

def main():
    print("--- Release Tool ---")
    
    if not check_gh_cli():
        print("Error: GitHub CLI (gh) is not installed or authenticated.")
        print("Please install it and run 'gh auth login' first.")
        return

    tags = get_tags()
    if not tags:
        print("No tags found. Please create a tag first.")
        return

    print(f"Recent tags: {', '.join(tags[:5])}...")
    tag_name = input("Enter tag to release: ").strip()
    
    if tag_name not in tags:
        print(f"Warning: Tag '{tag_name}' not found locally.")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return

    current_branch = get_current_branch()
    is_prerelease = False
    
    if current_branch == 'main':
        print("Detected 'main' branch. This will be a formal Release.")
    else:
        print(f"Detected '{current_branch}' branch. Defaulting to Prerelease.")
        is_prerelease = True
        
    # Allow override
    override = input(f"Is this a Prerelease? (current: {is_prerelease}) (y/n): ").lower()
    if override == 'y':
        is_prerelease = True
    elif override == 'n':
        is_prerelease = False

    cmd = ['gh', 'release', 'create', tag_name, '--generate-notes']
    if is_prerelease:
        cmd.append('--prerelease')
    
    print(f"Executing: {' '.join(cmd)}")
    confirm = input("Proceed? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        return

    try:
        subprocess.run(cmd, check=True)
        print("Release created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Release failed: {e}")

if __name__ == "__main__":
    main()
