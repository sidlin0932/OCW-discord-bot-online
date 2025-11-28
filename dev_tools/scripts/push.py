import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, get_current_branch

def main():
    print("--- Push Tool ---")
    
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")
    
    confirm = input(f"Push commits on '{current_branch}' to origin? (y/n): ").lower()
    if confirm == 'y':
        try:
            run_git_cmd(['push', 'origin', current_branch])
            print("Push successful.")
        except Exception as e:
            print(f"Push failed: {e}")
            print("Tip: You might need to pull changes first.")

    push_tags = input("Push tags to origin? (y/n): ").lower()
    if push_tags == 'y':
        try:
            run_git_cmd(['push', 'origin', '--tags'])
            print("Tags pushed successfully.")
        except Exception as e:
            print(f"Push tags failed: {e}")

if __name__ == "__main__":
    main()
