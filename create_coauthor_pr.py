import subprocess
import os
import sys
import uuid
from git import Repo

# Define the path to your Git repository
REPO_PATH = "."

def run_git_and_pr():
    # 1. Open the repository
    try:
        repo = Repo(REPO_PATH)
    except Exception as e:
        print(f"Error opening Git repository at '{REPO_PATH}': {e}")
        sys.exit(1)

    # Ensure repository is clean before we start
    if repo.is_dirty(untracked_files=True):
        print("Error: Your repository has uncommitted changes. Please stash, commit, or discard them before running this script.")
        sys.exit(1)

    # 2. Pull latest main branch
    print("Checking out main branch and pulling latest updates...")
    try:
        repo.git.checkout('main')
        repo.git.pull('origin', 'main')
    except Exception as e:
        print(f"Error updating main branch: {e}")
        sys.exit(1)

    # Detect the co-author trailer from the last commit to preserve it
    co_author_trailer = ""
    try:
        if repo.head.is_valid():
            last_commit = repo.head.commit
            last_message = last_commit.message
            co_author_lines = [line for line in last_message.split('\n') if line.strip().startswith('Co-authored-by:')]
            if co_author_lines:
                co_author_trailer = '\n\n' + '\n'.join(co_author_lines)
    except Exception as e:
        print(f"Could not read last commit co-author: {e}")

    # Fallback default co-author if none is found in the last commit
    if not co_author_trailer:
        co_author_trailer = "\n\nCo-authored-by: Soumyajit Behera <ashish454570@gmail.com>"

    # Generate a unique branch name and filename to avoid conflict
    unique_suffix = uuid.uuid4().hex[:8]
    branch_name = f"pair-extraordinaire-{unique_suffix}"
    filename = f"achievement_update_{unique_suffix}.txt"
    file_path = os.path.join(REPO_PATH, filename)

    print(f"\nCreating new branch: {branch_name}")
    try:
        repo.git.checkout('-b', branch_name)
    except Exception as e:
        print(f"Error creating branch: {e}")
        sys.exit(1)

    # Write a small change
    print(f"Creating file: {filename}")
    with open(file_path, 'w') as f:
        f.write(f"Pair programming contribution recorded on branch {branch_name}.\n")

    # Stage and commit with the co-author trailer
    print("Staging and committing...")
    try:
        repo.index.add([filename])
        commit_message = f"Add {filename} for Pair Extraordinaire badge" + co_author_trailer
        repo.index.commit(commit_message)
        print(f"Committed locally with message:\n{commit_message}")
    except Exception as e:
        print(f"Error committing: {e}")
        sys.exit(1)

    # Push branch
    print(f"Pushing branch {branch_name} to remote...")
    try:
        repo.git.push('origin', branch_name)
    except Exception as e:
        print(f"Error pushing branch to remote: {e}")
        sys.exit(1)

    # Create the PR via GitHub CLI
    print("\nCreating Pull Request via GitHub CLI...")
    pr_title = f"Pair Extraordinaire contribution {unique_suffix}"
    pr_body = "This PR contains a co-authored commit for the Pair Extraordinaire achievement."
    
    pr_create_cmd = [
        "gh", "pr", "create",
        "--title", pr_title,
        "--body", pr_body,
        "--head", branch_name,
        "--base", "main"
    ]
    res_create = subprocess.run(pr_create_cmd, capture_output=True, text=True)
    print("GitHub CLI Output:")
    print(res_create.stdout)
    if res_create.stderr:
        print("GitHub CLI Error:")
        print(res_create.stderr)

    if res_create.returncode != 0:
        print("Error: Pull request creation failed. Make sure you are logged in to the GitHub CLI (run 'gh auth login').")
        sys.exit(1)

    # Merge the PR via GitHub CLI
    print("\nMerging Pull Request...")
    pr_merge_cmd = [
        "gh", "pr", "merge",
        "--merge",
        "--delete-branch"
    ]
    res_merge = subprocess.run(pr_merge_cmd, capture_output=True, text=True)
    print("GitHub CLI Merge Output:")
    print(res_merge.stdout)
    if res_merge.stderr:
        print("GitHub CLI Merge Error:")
        print(res_merge.stderr)

    # Switch back to main and update
    print("\nReturning to main and pulling latest changes...")
    try:
        repo.git.checkout('main')
        repo.git.pull('origin', 'main')
        print("Done! Everything updated successfully.")
    except Exception as e:
        print(f"Warning: Could not return to main branch cleanly: {e}")

if __name__ == "__main__":
    run_git_and_pr()
