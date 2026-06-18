import yaml
from datetime import datetime, timedelta
from git import Repo
from time import sleep
from random import randint

FILE_TO_COMMIT_NAME = 'update_me.yaml'


def update_file_to_commit(commit_datetime=None):
    """Update the YAML file with the number of times it has been committed and the last update timestamp."""
    if commit_datetime is None:
        commit_datetime = datetime.now()
    try:
        with open(FILE_TO_COMMIT_NAME, 'r') as file:
            current_data = yaml.safe_load(file)
            if current_data and 'UPDATE_TIMES' in current_data:
                update_times = int(current_data['UPDATE_TIMES']) + 1
            else:
                update_times = 1
    except (FileNotFoundError, KeyError, TypeError, ValueError):
        # Fallback if file doesn't exist or is empty
        update_times = 1

    last_update = commit_datetime.strftime("%A %B %d %Y at %X%p")
    updated_data = {
        'UPDATE_TIMES': update_times,
        'LAST_UPDATE': last_update
    }
    with open(FILE_TO_COMMIT_NAME, 'w') as file:
        yaml.dump(updated_data, file, default_flow_style=False, sort_keys=True)
    return updated_data


def fill_commits_for_past_365_days(repo):
    """
    Check the commit history for the last 365 days.
    If any day has fewer than 70 commits, generate additional commits
    on that day to reach a random count between 70 and 80.
    """
    # 1. Detect Co-authored-by footer from last commit (if HEAD exists)
    co_author_trailer = ""
    try:
        if repo.head.is_valid():
            last_commit = repo.head.commit
            last_message = last_commit.message
            co_author_lines = [line for line in last_message.split('\n') if line.strip().startswith('Co-authored-by:')]
            if co_author_lines:
                co_author_trailer = '\n\n' + '\n'.join(co_author_lines)
    except Exception as e:
        print(f"Error detecting co-author trailer: {e}")

    # 2. Retrieve the count of existing commits per day
    print("Analyzing commit history...")
    commit_counts = {}
    try:
        for commit in repo.iter_commits():
            c_date = datetime.fromtimestamp(commit.authored_date).date()
            commit_counts[c_date] = commit_counts.get(c_date, 0) + 1
    except Exception as e:
        print(f"No commits found or error reading log: {e}")

    # 3. Calculate target range: previous 365 days up to today
    today = datetime.now().date()
    start_date = today - timedelta(days=365)
    
    total_commits_created = 0
    tz_offset = datetime.now().astimezone().strftime('%z')

    current_day = start_date
    days_to_process = []
    while current_day <= today:
        days_to_process.append(current_day)
        current_day += timedelta(days=1)

    print(f"Checking date range: {start_date} to {today} ({len(days_to_process)} days)")

    for day in days_to_process:
        current_count = commit_counts.get(day, 0)
        # Check if this day has fewer than 70 commits
        if current_count < 70:
            target_count = randint(70, 80)
            commits_to_make = target_count - current_count
            if commits_to_make > 0:
                print(f"Date {day}: currently has {current_count} commits. Making {commits_to_make} commits to reach target {target_count}...")
                
                # Generate sorted random times throughout the day
                times = []
                for _ in range(commits_to_make):
                    hour = randint(0, 23)
                    minute = randint(0, 59)
                    second = randint(0, 59)
                    times.append((hour, minute, second))
                times.sort()

                for hour, minute, second in times:
                    commit_datetime = datetime.combine(day, datetime.min.time()).replace(
                        hour=hour, minute=minute, second=second
                    )
                    # Update YAML file
                    updated_yaml_data = update_file_to_commit(commit_datetime)
                    
                    # Commit locally
                    if updated_yaml_data:
                        commit_message = f'Updated {updated_yaml_data["UPDATE_TIMES"]} times. Last update was on {updated_yaml_data["LAST_UPDATE"]}.'
                        if co_author_trailer:
                            commit_message += co_author_trailer
                        
                        unix_time = int(commit_datetime.timestamp())
                        git_date_str = f"{unix_time} {tz_offset}"
                        
                        repo.index.add([FILE_TO_COMMIT_NAME])
                        repo.index.commit(commit_message, author_date=git_date_str, commit_date=git_date_str)
                        total_commits_created += 1
                        
                        if total_commits_created % 500 == 0:
                            print(f"Created {total_commits_created} commits...")

    # 4. Push if any new commits were created
    if total_commits_created > 0:
        print(f"Successfully created {total_commits_created} commits locally. Pushing to origin...")
        try:
            origin = repo.remote('origin')
            origin.push()
            print("Successfully pushed commits to remote origin!")
        except Exception as e:
            print(f"Error pushing to remote origin: {e}")
    else:
        print("All dates already have 70-80 commits. No new commits needed.")


if __name__ == '__main__':
    repo = Repo('.')
    while True:
        # Check and fill commits for the last 365 days relative to today
        fill_commits_for_past_365_days(repo)
        
        # Sleep for 24 hours (86400 seconds) before checking again
        print("Sleeping for 24 hours...")
        sleep(86400)
