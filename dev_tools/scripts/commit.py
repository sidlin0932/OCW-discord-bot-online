import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, is_working_tree_clean

def main():
    print("--- Auto Commit Tool ---")
    
    if is_working_tree_clean():
        print("Working tree is clean. Nothing to commit.")
        return

    print("Changes detected.")
    run_git_cmd(['status'])
    
    confirm = input("\nStage all changes? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        return

    run_git_cmd(['add', '.'])
    
    message = input("Enter commit message: ").strip()
    if not message:
        print("Commit message cannot be empty. Aborted.")
        run_git_cmd(['reset']) # Unstage
        return

    try:
        run_git_cmd(['commit', '-m', message])
        print("Commit successful!")
    except Exception as e:
        print(f"Commit failed: {e}")

if __name__ == "__main__":
    main()
