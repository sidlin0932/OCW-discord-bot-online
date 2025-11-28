import subprocess
import re
import sys

def run_git_cmd(args, cwd=None):
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8' # Force UTF-8 encoding
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {' '.join(args)}")
        print(f"Error message: {e.stderr}")
        raise e

def get_current_branch():
    """Get the current active branch name."""
    return run_git_cmd(['rev-parse', '--abbrev-ref', 'HEAD'])

def is_working_tree_clean():
    """Check if the working tree is clean."""
    status = run_git_cmd(['status', '--porcelain'])
    return not status

def get_all_branches():
    """Get a list of all local branches."""
    output = run_git_cmd(['branch', '--format=%(refname:short)'])
    return output.split('\n')

def get_remote_branches():
    """Get a list of all remote branches."""
    output = run_git_cmd(['branch', '-r', '--format=%(refname:short)'])
    return [b.strip() for b in output.split('\n') if '->' not in b]

def get_tags():
    """Get all tags sorted by version if possible."""
    try:
        return run_git_cmd(['tag', '--sort=-v:refname']).split('\n')
    except:
        return run_git_cmd(['tag']).split('\n')

def validate_semver(tag):
    """
    Validate if a tag follows Semantic Versioning (vX.Y.Z or X.Y.Z).
    Allows optional 'v' prefix.
    """
    semver_pattern = r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    return bool(re.match(semver_pattern, tag))

def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        subprocess.run(['gh', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Check auth status
        result = subprocess.run(['gh', 'auth', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False
