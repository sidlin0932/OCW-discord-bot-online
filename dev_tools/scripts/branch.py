import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, get_all_branches, get_current_branch

def main():
    print("--- Branch Manager ---")
    
    while True:
        current = get_current_branch()
        print(f"\nCurrent branch: {current}")
        print("1. List Branches")
        print("2. Create New Branch")
        print("3. Switch Branch")
        print("4. Delete Branch")
        print("5. Exit")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            branches = get_all_branches()
            for b in branches:
                print(f"  {b}" + (" *" if b == current else ""))
                
        elif choice == '2':
            name = input("Enter new branch name: ").strip()
            if name:
                try:
                    run_git_cmd(['checkout', '-b', name])
                    print(f"Created and switched to '{name}'")
                except Exception as e:
                    print(f"Error: {e}")
                    
        elif choice == '3':
            branches = get_all_branches()
            for i, b in enumerate(branches):
                print(f"{i+1}. {b}")
            idx = input("Select branch number: ").strip()
            try:
                target = branches[int(idx)-1]
                run_git_cmd(['checkout', target])
                print(f"Switched to '{target}'")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '4':
            branches = get_all_branches()
            for i, b in enumerate(branches):
                print(f"{i+1}. {b}")
            idx = input("Select branch number to DELETE: ").strip()
            try:
                target = branches[int(idx)-1]
                if target == current:
                    print("Cannot delete current branch. Switch first.")
                    continue
                
                confirm = input(f"Are you sure you want to delete '{target}'? (y/n): ").lower()
                if confirm == 'y':
                    run_git_cmd(['branch', '-d', target])
                    print(f"Deleted '{target}'")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '5':
            break

if __name__ == "__main__":
    main()
