import requests
from datetime import datetimme

def github_user_activity(username: str) -> dict:
  base_url = "https://api.github.com"
  headers = {"Accept": "application/nvd.github.v3+json"}

  #fetching of user info
  user_data = requests.get(f"{base_url}/users/{username}", headers = headers).json();

  #fetch recent events
  events_url = f"{base_url}/users/{username}/events"
  events_data = requests.get(events_url, headers=headers).json()

  commit_counts = {}
  for event in events_data:
    if event.get("type") == "PushEvent":
      for commit in event.get("payload", {}).get("commits", []):
        commit_counts[commit["message"]] = commit_counts.get(commit["message"], 0) + 1
  
  repos = requests.get(f"{base_url}/users/{username}/repos", headers=headers).json()
  languages = {}
  for repo in repos:
    lang = repo.get("language")
    if lang:
      languages[lang] = languages.get(lang, 0) + 1

  return {
    "profile": user_data,
    "commit_counts": commit_counts,
    "languages": languages,
    "event_count": len(events_data)
  }

