import os

def main():
    print("--- CI/CD Setup Tool ---")
    
    workflow_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.github', 'workflows')
    os.makedirs(workflow_dir, exist_ok=True)
    
    release_yml_path = os.path.join(workflow_dir, 'release.yml')
    
    print(f"Target: {release_yml_path}")
    
    content = """name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
"""
    
    if os.path.exists(release_yml_path):
        print("Warning: release.yml already exists.")
        confirm = input("Overwrite? (y/n): ").lower()
        if confirm != 'y':
            return

    try:
        with open(release_yml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Created release.yml successfully!")
    except Exception as e:
        print(f"Error creating file: {e}")

if __name__ == "__main__":
    main()
