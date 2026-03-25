#!/usr/bin/env python3
"""
Scan all git repos in a directory for recent commits by a specific author.
Used by the standup-prep Claude Code skill.

Usage:
    python3 git-commits.py ~/Development/Dfinitiv --author "Brian Via" --days 1
"""

import os
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def run_command(command: str, cwd: str = ".") -> str:
    """Run a shell command and return its output."""
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def find_git_repos(base: Path) -> list[tuple[str, Path]]:
    """Find all git repos in a directory, including conductor-workspaces subdirectories.

    Returns (display_name, path) tuples. Conductor worktrees get prefixed
    with their parent dir for clarity, e.g. "conductor/savvy-studio".
    """
    repos: list[tuple[str, Path]] = []

    for item in sorted(base.iterdir()):
        if not item.is_dir():
            continue

        # Direct git repo (or worktree — .git can be a file pointing to the real .git dir)
        git_marker = item / ".git"
        if git_marker.exists():
            repos.append((item.name, item))
            continue

        # Check known nested directories (conductor-workspaces, etc.)
        # Scan one level deeper for git repos inside these
        if item.name in ("conductor-workspaces",):
            for nested in sorted(item.iterdir()):
                if nested.is_dir() and (nested / ".git").exists():
                    repos.append((f"conductor/{nested.name}", nested))

    return repos


def scan_repos(directory: str, author: str, days: int) -> dict[str, list[str]]:
    """Scan all git repos in directory for recent commits by author."""
    base = Path(directory).expanduser().resolve()
    if not base.exists():
        print(f"Directory not found: {base}")
        return {}

    since = (datetime.now() - timedelta(days=days)).isoformat()
    results: dict[str, list[str]] = {}

    for display_name, repo_path in find_git_repos(base):
        # Get commits with hash, subject, and date
        log_fmt = '%h|%s|%ar'
        commits_raw = run_command(
            f'git log --author="{author}" --since="{since}" --format="{log_fmt}"',
            cwd=str(repo_path),
        )

        if commits_raw:
            commits = []
            for line in commits_raw.strip().split("\n"):
                parts = line.split("|", 2)
                if len(parts) == 3:
                    sha, subject, relative_time = parts
                    commits.append(f"  {sha} {subject} ({relative_time})")
                else:
                    commits.append(f"  {line}")
            results[display_name] = commits

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scan git repos for recent commits by author."
    )
    parser.add_argument("directory", help="Directory containing git repositories")
    parser.add_argument(
        "--author", default="Brian Via", help="Author name to filter (default: Brian Via)"
    )
    parser.add_argument(
        "--days", type=int, default=1, help="Days to look back (default: 1)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    args = parser.parse_args()

    results = scan_repos(args.directory, args.author, args.days)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
        return

    if not results:
        print(f"No commits by {args.author} in the last {args.days} day(s).")
        return

    total = sum(len(c) for c in results.values())
    print(f"Found {total} commit(s) across {len(results)} repo(s):\n")

    for repo, commits in results.items():
        print(f"📦 {repo} ({len(commits)} commits)")
        for commit in commits:
            print(commit)
        print()


if __name__ == "__main__":
    main()
