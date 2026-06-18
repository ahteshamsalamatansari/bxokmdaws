import subprocess
import os
import sys
import uuid
import time
from git import Repo

# Define the path to your Git repository
REPO_PATH = "."
PROGRESS_FILE = ".pull_shark_progress"
TARGET_PRS = 1024

def get_current_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0

def save_progress(count):
    try:
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(count))
    except Exception as e:
        print(f"Warning: Could not save progress: {e}")

def run_git_and_prs():
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

    # Ensure we are on main branch
    print("Switching to main branch...")
    try:
        repo.git.checkout('main')
    except Exception as e:
        print(f"Error checking out main: {e}")
        sys.exit(1)

    start_idx = get_current_progress()
    if start_idx >= TARGET_PRS:
        print(f"Already completed {start_idx} PRs. Resetting target or exiting...")
        # Ask to restart
        confirm = input("Reset progress and start from 0? (y/n): ").strip().lower()
        if confirm == 'y':
            start_idx = 0
            save_progress(0)
        else:
            print("Exiting.")
            sys.exit(0)

    print(f"Resuming from PR #{start_idx + 1} of {TARGET_PRS}...")

    for i in range(start_idx + 1, TARGET_PRS + 1):
        print(f"\n=========================================")
        print(f"Processing PR {i} of {TARGET_PRS}...")
        print(f"=========================================")

        unique_suffix = f"shark-{i}-{uuid.uuid4().hex[:4]}"
        branch_name = f"shark-branch-{unique_suffix}"
        filename = f"shark_update_{unique_suffix}.txt"
        file_path = os.path.join(REPO_PATH, filename)

        # 1. Checkout new branch
        try:
            repo.git.checkout('-b', branch_name)
        except Exception as e:
            print(f"Error checking out branch {branch_name}: {e}")
            sys.exit(1)

        # 2. Write file
        with open(file_path, 'w') as f:
            f.write(f"Contribution for Pull Shark PR {i}.\n")

        # 3. Stage and commit
        try:
            repo.index.add([filename])
            repo.index.commit(f"Add {filename} for Pull Shark #{i}")
        except Exception as e:
            print(f"Error committing: {e}")
            # Clean up and exit
            repo.git.checkout('main')
            sys.exit(1)

        # 4. Push branch
        push_success = False
        for attempt in range(5):
            try:
                repo.git.push('origin', branch_name)
                push_success = True
                break
            except Exception as e:
                print(f"Push failed (attempt {attempt+1}/5): {e}. Retrying in 15s...")
                time.sleep(15)
        if not push_success:
            print("Failed to push branch after multiple attempts. Exiting.")
            repo.git.checkout('main')
            sys.exit(1)

        # 5. Create PR with retry on rate limit
        pr_url = None
        while True:
            pr_create_cmd = [
                "gh", "pr", "create",
                "--title", f"Pull Shark PR #{i}",
                "--body", f"Automated PR #{i} for the Pull Shark achievement.",
                "--head", branch_name,
                "--base", "main"
            ]
            res = subprocess.run(pr_create_cmd, capture_output=True, text=True)
            if res.returncode == 0:
                pr_url = res.stdout.strip()
                print(f"PR #{i} created successfully: {pr_url}")
                break
            else:
                stderr = res.stderr.lower()
                if "abuse detection" in stderr or "rate limit" in stderr or "403" in stderr or "429" in stderr:
                    print("Hit GitHub secondary rate limit/abuse detection during PR creation. Sleeping for 90s...")
                    time.sleep(90)
                else:
                    print(f"Error creating PR #{i}: {res.stderr.strip()}")
                    print("Retrying in 15 seconds...")
                    time.sleep(15)

        # 6. Merge PR with retry on rate limit
        while True:
            pr_merge_cmd = [
                "gh", "pr", "merge",
                "--merge",
                "--delete-branch"
            ]
            res = subprocess.run(pr_merge_cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"PR #{i} merged successfully.")
                break
            else:
                stderr = res.stderr.lower()
                if "abuse detection" in stderr or "rate limit" in stderr or "403" in stderr or "429" in stderr:
                    print("Hit GitHub rate limit during PR merge. Sleeping for 90s...")
                    time.sleep(90)
                else:
                    print(f"Error merging PR #{i}: {res.stderr.strip()}")
                    print("Retrying in 15 seconds...")
                    time.sleep(15)

        # 7. Go back to main and pull
        try:
            repo.git.checkout('main')
            repo.git.pull('origin', 'main')
        except Exception as e:
            print(f"Warning: error returning to main/pulling: {e}")

        # Save progress
        save_progress(i)

        # Delay to avoid abuse detection limits
        print("Waiting 2 seconds before the next PR...")
        time.sleep(2)

    print("\nAll 1024 PRs have been successfully created and merged!")

if __name__ == "__main__":
    run_git_and_prs()
