import os
import sys
import argparse
from datetime import datetime, timedelta
from random import randint
from git import Repo

def main():
    parser = argparse.ArgumentParser(
        description="Create backdated Git commits for a specified number of previous days."
    )
    parser.add_argument(
        "--repo-path", 
        default=".", 
        help="Path to the Git repository (default: current directory)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=7, 
        help="Number of days to generate commits for (default: 7)"
    )
    parser.add_argument(
        "--min-commits", 
        type=int, 
        default=150, 
        help="Minimum commits per day (default: 150)"
    )
    parser.add_argument(
        "--max-commits", 
        type=int, 
        default=180, 
        help="Maximum commits per day (default: 180)"
    )
    parser.add_argument(
        "--file", 
        default="backdated_commits.txt", 
        help="Filename to modify and commit (default: backdated_commits.txt)"
    )
    parser.add_argument(
        "--push", 
        action="store_true", 
        help="Automatically push commits to remote origin after completion"
    )
    parser.add_argument(
        "--include-today", 
        action="store_true", 
        help="Include today in the days count (default: starts from yesterday and goes back)"
    )
    args = parser.parse_args()

    # Resolve absolute repository path
    repo_path = os.path.abspath(args.repo_path)
    
    # 1. Initialize repository
    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(f"Error: Could not open Git repository at '{repo_path}': {e}")
        sys.exit(1)

    # 2. Check repository status
    if repo.is_dirty(untracked_files=True):
        print("Error: The repository has uncommitted changes. Please clean, stash, or commit them first.")
        sys.exit(1)

    # 3. Detect co-author trailer (copied from active commits for contribution graph persistence)
    co_author_trailer = ""
    try:
        if repo.head.is_valid():
            last_commit = repo.head.commit
            last_message = last_commit.message
            co_author_lines = [
                line for line in last_message.split('\n') 
                if line.strip().startswith('Co-authored-by:')
            ]
            if co_author_lines:
                co_author_trailer = '\n\n' + '\n'.join(co_author_lines)
    except Exception as e:
        print(f"Warning: Could not detect co-author trailer from last commit: {e}")

    # 4. Calculate target date range
    # By default (exclude today): [today - 7, today - 6, ..., today - 1]
    # With --include-today: [today - 6, today - 5, ..., today]
    today = datetime.now().date()
    start_offset = 0 if args.include_today else 1
    
    target_dates = []
    for i in range(args.days):
        day = today - timedelta(days=i + start_offset)
        target_dates.append(day)
    
    # Sort dates chronologically (oldest first)
    target_dates.sort()

    print(f"Targeting {args.days} days: {target_dates[0]} to {target_dates[-1]}")
    print(f"Commits per day range: {args.min_commits} to {args.max_commits}")
    
    # Detect active branch
    try:
        active_branch = repo.active_branch.name
        print(f"Active branch: {active_branch}")
    except TypeError:
        print("Warning: HEAD is detached. Commits will not update any branch unless you checkout to one.")
        confirm = input("Do you want to proceed anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation aborted.")
            sys.exit(0)

    # Retrieve local timezone offset
    tz_offset = datetime.now().astimezone().strftime('%z')
    
    total_commits = 0
    file_path = os.path.join(repo_path, args.file)

    print("\nStarting commit generation...")
    for day in target_dates:
        commits_to_make = randint(args.min_commits, args.max_commits)
        print(f"Generating {commits_to_make} commits for {day}...")

        # Generate sorted random timestamps throughout the day
        times = []
        for _ in range(commits_to_make):
            hour = randint(0, 23)
            minute = randint(0, 59)
            second = randint(0, 59)
            times.append((hour, minute, second))
        times.sort()

        day_commits_count = 0
        for hour, minute, second in times:
            commit_datetime = datetime.combine(day, datetime.min.time()).replace(
                hour=hour, minute=minute, second=second
            )
            
            total_commits += 1
            day_commits_count += 1
            
            # Write unique content to the file
            content = (
                f"Date: {day}\n"
                f"Commit: {day_commits_count}/{commits_to_make}\n"
                f"Total Session Commits: {total_commits}\n"
                f"Timestamp: {commit_datetime.isoformat()}\n"
            )
            
            with open(file_path, "w") as f:
                f.write(content)
            
            # Prepare git commit variables
            unix_time = int(commit_datetime.timestamp())
            git_date_str = f"{unix_time} {tz_offset}"
            
            commit_message = f"Update backdated commits progress: {day} commit {day_commits_count}/{commits_to_make}"
            if co_author_trailer:
                commit_message += co_author_trailer
            
            try:
                repo.index.add([args.file])
                repo.index.commit(commit_message, author_date=git_date_str, commit_date=git_date_str)
            except Exception as e:
                print(f"Error during commit creation at {commit_datetime}: {e}")
                sys.exit(1)
        
        print(f"Successfully created {commits_to_make} commits for {day}.")

    print(f"\nFinished! Total commits created locally: {total_commits}")

    # 5. Push if requested
    if args.push:
        print("Pushing to remote origin...")
        try:
            origin = repo.remote('origin')
            branch_to_push = repo.active_branch.name
            origin.push(branch_to_push)
            print(f"Successfully pushed commits to remote origin on branch '{branch_to_push}'!")
        except Exception as e:
            print(f"Error pushing to remote origin: {e}")
            print("Please push manually when ready using: git push origin <branch>")
    else:
        print("\nTo push these commits to remote repository, run:")
        try:
            branch_to_push = repo.active_branch.name
            print(f"  git push origin {branch_to_push}")
        except Exception:
            print("  git push origin HEAD")

if __name__ == "__main__":
    main()
