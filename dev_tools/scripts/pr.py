import sys
import os
import subprocess

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import check_gh_cli, get_current_branch

def main():
    print("--- Pull Request Tool ---")
    
    if not check_gh_cli():
        print("Error: GitHub CLI (gh) is not installed or authenticated.")
        return

    current = get_current_branch()
    print(f"Current branch: {current}")
    
    title = input("PR Title (default: last commit message): ").strip()
    body = input("PR Body (optional): ").strip()
    
    cmd = ['gh', 'pr', 'create']
    if title:
        cmd.extend(['--title', title])
    else:
        cmd.append('--fill') # Use commit info
        
    if body:
        cmd.extend(['--body', body])
        
    # Interactive web mode option
    web = input("Open in web browser? (y/n): ").lower()
    if web == 'y':
        cmd.append('--web')

    print(f"Executing: {' '.join(cmd)}")
    confirm = input("Proceed? (y/n): ").lower()
    if confirm != 'y':
        return

    try:
        subprocess.run(cmd, check=True)
        print("PR created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"PR creation failed: {e}")

if __name__ == "__main__":
    main()
