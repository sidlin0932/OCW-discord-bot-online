import sys
import os
import datetime

# Add parent directory to path to allow importing core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.git_utils import run_git_cmd, validate_semver, get_tags

def main():
    print("--- Tagging Tool ---")
    
    # Show recent tags
    tags = get_tags()
    print(f"Recent tags: {', '.join(tags[:5])}..." if tags else "No tags found.")
    
    tag_name = input("Enter new tag name (e.g., v1.0.0): ").strip()
    
    if not validate_semver(tag_name):
        print("Error: Tag name does not follow SemVer format (e.g., v1.0.0, v1.0.0-beta.1).")
        return

    # Check for prerelease
    if '-' in tag_name:
        add_metadata = input("Prerelease detected. Add build metadata (timestamp)? (y/n): ").lower()
        if add_metadata == 'y':
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            if '+' in tag_name:
                tag_name += f".{timestamp}"
            else:
                tag_name += f"+{timestamp}"
            print(f"New tag name with metadata: {tag_name}")

    confirm = input(f"Create tag '{tag_name}' at HEAD? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        return

    try:
        run_git_cmd(['tag', tag_name])
        print(f"Tag '{tag_name}' created successfully!")
        print("Remember to run the Push tool to sync tags to remote.")
    except Exception as e:
        print(f"Tag creation failed: {e}")

if __name__ == "__main__":
    main()
