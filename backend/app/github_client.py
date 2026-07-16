"""
Wraps PyGithub so the GitOps Agent can open real branches, commits, and Pull Requests.

If GITHUB_TOKEN / GITHUB_REPO aren't set in .env, all methods fall back to a "dry run"
mode that returns a fake PR URL and logs what *would* have happened. This means the demo
still works end-to-end even before you've wired up a real GitHub repo -- flip on the real
token whenever you're ready to show a genuine Pull Request being opened.
"""
import time
from typing import Optional

from .config import settings

try:
    from github import Github
except ImportError:  # pragma: no cover
    Github = None


class GitHubClient:
    def __init__(self):
        self.enabled = bool(settings.GITHUB_TOKEN and settings.GITHUB_REPO and Github is not None)
        self._gh = Github(settings.GITHUB_TOKEN) if self.enabled else None

    def open_repair_pr(
        self,
        branch_name: str,
        file_path: str,
        file_content: str,
        commit_message: str,
        pr_title: str,
        pr_body: str,
    ) -> str:
        if not self.enabled:
            return (
                f"[DRY RUN] No GITHUB_TOKEN/GITHUB_REPO configured. "
                f"Would have created branch '{branch_name}', committed '{file_path}', "
                f"and opened a PR titled '{pr_title}'. "
                f"Set GITHUB_TOKEN and GITHUB_REPO in backend/.env to open real PRs."
            )

        repo = self._gh.get_repo(settings.GITHUB_REPO)
        base = repo.get_branch(repo.default_branch)
        unique_branch = f"{branch_name}-{int(time.time())}"
        repo.create_git_ref(ref=f"refs/heads/{unique_branch}", sha=base.commit.sha)

        try:
            existing = repo.get_contents(file_path, ref=unique_branch)
            repo.update_file(file_path, commit_message, file_content, existing.sha, branch=unique_branch)
        except Exception:
            repo.create_file(file_path, commit_message, file_content, branch=unique_branch)

        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=unique_branch,
            base=repo.default_branch,
        )
        return pr.html_url


github_client = GitHubClient()
