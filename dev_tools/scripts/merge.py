import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, get_all_branches, get_current_branch

def main():
    print("--- Merge Tool ---")
    
    branches = get_all_branches()
    current_branch = get_current_branch()
    
    print(f"Current branch: {current_branch}")
    print("Available branches:")
    for i, b in enumerate(branches):
        print(f"{i+1}. {b}")
        
    # Select Target
    print("\nTarget branch (where changes will be merged INTO):")
    print(f"Default: {current_branch}")
    target_idx = input("Select number (or press Enter for default): ").strip()
    
    target_branch = current_branch
    if target_idx:
        try:
            target_branch = branches[int(target_idx)-1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

    # Select Source
    print(f"\nSource branch (where changes come FROM) to merge into '{target_branch}':")
    source_idx = input("Select number: ").strip()
    
    try:
        source_branch = branches[int(source_idx)-1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    if source_branch == target_branch:
        print("Source and Target are the same. Nothing to merge.")
        return

    print(f"\nPlan: Merge '{source_branch}' -> '{target_branch}'")
    confirm = input("Proceed? (y/n): ").lower()
    if confirm != 'y':
        return

    try:
        if target_branch != current_branch:
            print(f"Switching to {target_branch}...")
            run_git_cmd(['checkout', target_branch])
            
        run_git_cmd(['merge', source_branch])
        print("Merge successful!")
    except Exception as e:
        print(f"Merge failed: {e}")
        print("Fix conflicts and commit manually.")

if __name__ == "__main__":
    main()
