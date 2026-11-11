#!/bin/bash
set -e

# Create directory structure
mkdir -p apps/worker/src/worker/workflows
mkdir -p apps/worker/src/worker/entrypoints
mkdir -p apps/worker/tests

# File 1: requirements.txt
cat > requirements.txt << 'EOF'
mistralai>=1.0.0
mistralai-workflows>=1.0.0
pydantic>=2.5.0
pyyaml>=6.0.1
aiohttp>=3.8.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
EOF

# File 2: apps/worker/Dockerfile
cat > apps/worker/Dockerfile << 'EOF'
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY src/ ./src/
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["python", "-m", "worker.entrypoints.worker"]
EOF

# File 3: Main workflow
cat > apps/worker/src/worker/workflows/github_catchup.py << 'WORKFLOW_EOF'
from datetime import datetime
from typing import List, Optional
import aiohttp
import mistralai.workflows as workflows
from pydantic import BaseModel, Field

class GitHubCatchUpInput(BaseModel):
    repo_handle: str = Field(..., description="GitHub repository (owner/repo)")
    since_date: str = Field(..., description="Date (YYYY-MM-DD or ISO)")
    slack_channel: Optional[str] = Field(default=None, description="Slack channel (optional)")

class PullRequest(BaseModel):
    title: str
    url: str
    number: int
    merged_at: Optional[str] = None
    created_at: str
    author: str
    state: str

class CatchUpResult(BaseModel):
    merged_since_date: List[PullRequest]
    awaiting_review: List[PullRequest]
    slack_message: str
    posted_to_slack: bool

@workflows.activity()
async def fetch_merged_prs(repo_handle: str, since_date: str) -> List[PullRequest]:
    owner, repo = repo_handle.split("/")
    try:
        since_iso = datetime.strptime(since_date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        since_iso = since_date
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc"
    async with aiohttp.ClientSession() as session:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Mistral-Workflow"}
        merged_prs = []
        page = 1
        while True:
            paginated_url = f"{url}&page={page}&per_page=100"
            async with session.get(paginated_url, headers=headers) as response:
                if response.status == 403:
                    break
                if response.status != 200:
                    raise Exception(f"GitHub API error: {response.status}")
                data = await response.json()
                if not data:
                    break
                for pr in data:
                    if pr.get("merged_at") and pr["merged_at"] >= since_iso:
                        merged_prs.append(PullRequest(
                            title=pr["title"], url=pr["html_url"], number=pr["number"],
                            merged_at=pr["merged_at"], created_at=pr["created_at"],
                            author=pr["user"]["login"], state="merged"
                        ))
                link_header = response.headers.get("Link", "")
                if "next" not in link_header:
                    break
                page += 1
        return merged_prs

@workflows.activity()
async def fetch_prs_awaiting_review(repo_handle: str) -> List[PullRequest]:
    owner, repo = repo_handle.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&sort=created&direction=desc"
    async with aiohttp.ClientSession() as session:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Mistral-Workflow"}
        open_prs = []
        page = 1
        while True:
            paginated_url = f"{url}&page={page}&per_page=100"
            async with session.get(paginated_url, headers=headers) as response:
                if response.status == 403:
                    break
                if response.status != 200:
                    raise Exception(f"GitHub API error: {response.status}")
                data = await response.json()
                if not data:
                    break
                for pr in data:
                    if not pr.get("draft", False):
                        open_prs.append(PullRequest(
                            title=pr["title"], url=pr["html_url"], number=pr["number"],
                            merged_at=None, created_at=pr["created_at"],
                            author=pr["user"]["login"], state="open"
                        ))
                link_header = response.headers.get("Link", "")
                if "next" not in link_header:
                    break
                page += 1
        return open_prs

@workflows.activity()
async def format_pr_digest(merged_prs: List[PullRequest], awaiting_review_prs: List[PullRequest]) -> str:
    lines = [":github: *GitHub Repository Catch-Up Digest*", ""]
    if merged_prs:
        lines.append("*:white_check_mark: Merged Since Date:*")
        for pr in merged_prs:
            title = pr.title[:60] + "..." if len(pr.title) > 60 else pr.title
            lines.append(f"  :small_blue_diamond: {title} - <{pr.url}|PR #{pr.number}>")
        lines.append("")
    else:
        lines.append("*No PRs merged since the specified date.*")
        lines.append("")
    if awaiting_review_prs:
        lines.append("*:hourglass: Awaiting Review:*")
        for pr in awaiting_review_prs:
            title = pr.title[:60] + "..." if len(pr.title) > 60 else pr.title
            lines.append(f"  :small_orange_diamond: {title} - <{pr.url}|PR #{pr.number}>")
        lines.append("")
    else:
        lines.append("*No PRs awaiting review.*")
        lines.append("")
    lines.append("---")
    lines.append(f"*Total: {len(merged_prs)} merged, {len(awaiting_review_prs)} awaiting review*")
    return "\\n".join(lines)

@workflows.activity()
async def post_to_slack(message: str, channel: Optional[str] = None) -> bool:
    import os
    slack_token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN")
    if slack_token:
        async with aiohttp.ClientSession() as session:
            url = "https://slack.com/api/chat.postMessage"
            headers = {"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"}
            target_channel = channel or os.environ.get("SLACK_CHANNEL", "#general")
            payload = {"channel": target_channel, "text": message, "mrkdwn": True, "unfurl_links": False}
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("ok", False)
    return False

@workflows.workflow.define(
    name="github-catchup",
    workflow_display_name="GitHub Repository Catch-Up",
    workflow_description="Fetches merged PRs since a date and PRs awaiting review, then posts to Slack.",
)
class GitHubCatchUpWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: GitHubCatchUpInput) -> CatchUpResult:
        merged_prs = await fetch_merged_prs(input.repo_handle, input.since_date)
        awaiting_review_prs = await fetch_prs_awaiting_review(input.repo_handle)
        message = await format_pr_digest(merged_prs, awaiting_review_prs)
        posted = await post_to_slack(message, input.slack_channel)
        return CatchUpResult(
            merged_since_date=merged_prs,
            awaiting_review=awaiting_review_prs,
            slack_message=message,
            posted_to_slack=posted
        )
WORKFLOW_EOF

# File 4: Worker entrypoint
cat > apps/worker/src/worker/entrypoints/worker.py << 'EOF'
import asyncio
import os
import mistralai.workflows as workflows
from mistralai.client import Mistral

async def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    workflows_client = Mistral(api_key=api_key) if api_key else Mistral()
    workflow_classes = workflows.discover_all_workflows_in_package("worker.workflows")
    await workflows_client.run_worker(workflow_classes)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# File 5: __init__ files
cat > apps/worker/src/worker/__init__.py << 'EOF'
# Worker package
EOF

cat > apps/worker/src/worker/workflows/__init__.py << 'EOF'
from worker.workflows.github_catchup import GitHubCatchUpWorkflow
__all__ = ["GitHubCatchUpWorkflow"]
EOF

cat > apps/worker/src/worker/entrypoints/__init__.py << 'EOF'
# Entrypoints package
EOF

cat > apps/worker/tests/__init__.py << 'EOF'
# Tests package
EOF

# File 6: pyproject.toml
cat > apps/worker/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "github-catchup-worker"
version = "1.0.0"
description = "Mistral Workflow worker for GitHub catch-up digest"
requires-python = ">=3.10"
dependencies = ["mistralai>=1.0.0", "pydantic>=2.5.0", "aiohttp>=3.8.0", "python-dotenv>=1.0.0"]
[tool.setuptools.packages.find]
where = ["src"]
include = ["worker*"]
EOF

# File 7: .gitignore
cat > apps/worker/.gitignore << 'EOF'
__pycache__/
*.py[cod]
.DS_Store
EOF

# Commit everything
git add -A
git commit -m "Add GitHub catch-up workflow for Mistral Cloud"

echo "✅ All files created and committed!"
echo "Now push to GitHub:"
echo "  git push origin main"
