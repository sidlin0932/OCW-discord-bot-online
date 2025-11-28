import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts import commit, push, merge, branch, tag, release, pr, cicd_setup

def main():
    while True:
        print("\n=================================")
        print("   Dev Tools Automation v0.1.0   ")
        print("=================================")
        print("1. Commit (Local Record)")
        print("2. Tag (Milestone)")
        print("3. Push (Sync Remote)")
        print("4. Release (Publish)")
        print("5. Merge (Combine Branches)")
        print("6. Branch Manager")
        print("7. Create Pull Request")
        print("8. Setup CI/CD")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            commit.main()
        elif choice == '2':
            tag.main()
        elif choice == '3':
            push.main()
        elif choice == '4':
            release.main()
        elif choice == '5':
            merge.main()
        elif choice == '6':
            branch.main()
        elif choice == '7':
            pr.main()
        elif choice == '8':
            cicd_setup.main()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
