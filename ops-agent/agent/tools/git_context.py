import os
from datetime import datetime, timezone, timedelta
from github import Github, Auth

# Initialize GitHub client safely
_token = os.getenv("GITHUB_TOKEN", "").strip()
auth = Auth.Token(_token) if _token else None
github_client = Github(auth=auth) if auth else None

REPO_NAME = "samklin92/pyops"


def get_recent_changes(service: str, hours_back: int = 24) -> dict:
    """
    Fetch recent commits and PRs for a given service from GitHub.
    """
    if not github_client:
        return {
            "service": service,
            "error": "GITHUB_TOKEN not set",
            "recent_commits": [],
            "recent_prs": []
        }

    try:
        repo = github_client.get_repo(REPO_NAME)
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        commits = repo.get_commits(since=since)

        relevant_commits = []
        for commit in commits:
            files_changed = [f.filename for f in commit.files]
            service_files = [
                f for f in files_changed
                if service.lower().replace("-", "_") in f.lower()
                or service.lower() in f.lower()
            ]

            relevant_commits.append({
                "sha": commit.sha[:8],
                "message": commit.commit.message.split("\n")[0],
                "author": commit.commit.author.name,
                "timestamp": commit.commit.author.date.isoformat(),
                "files_changed": files_changed,
                "service_relevant": len(service_files) > 0
            })

        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
        recent_prs = []
        for pr in pulls:
            if pr.merged_at and pr.merged_at.replace(tzinfo=timezone.utc) >= since:
                recent_prs.append({
                    "number": pr.number,
                    "title": pr.title,
                    "author": pr.user.login,
                    "merged_at": pr.merged_at.isoformat(),
                    "labels": [l.name for l in pr.labels]
                })

        return {
            "service": service,
            "hours_back": hours_back,
            "repo": REPO_NAME,
            "recent_commits": relevant_commits[:5],
            "recent_prs": recent_prs[:3],
            "total_commits_found": len(relevant_commits)
        }

    except Exception as e:
        return {
            "service": service,
            "error": str(e),
            "recent_commits": [],
            "recent_prs": []
        }


GIT_CONTEXT_TOOL = {
    "name": "get_recent_changes",
    "description": (
        "Fetch recent commits and merged pull requests from GitHub for a given service. "
        "Use this to check if a recent deployment or code change correlates with an alert. "
        "Always call this after querying metrics to check for deployment-related causes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "description": "Service name to look up e.g. payments-api, auth-service"
            },
            "hours_back": {
                "type": "integer",
                "description": "How many hours back to search for changes. Default 24.",
                "default": 24
            }
        },
        "required": ["service"]
    }
}


if __name__ == "__main__":
    import json
    print("Script started")
    result = get_recent_changes("payments-api", hours_back=48)
    print(json.dumps(result, indent=2))