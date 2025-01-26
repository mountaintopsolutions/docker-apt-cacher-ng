#!/usr/bin/env python3
"""Push version updates to git repository."""

import subprocess
from pathlib import Path
from typing import List
import argparse


def run_git_command(cmd: List[str]) -> None:
    """Execute a git command and handle errors."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {' '.join(cmd)}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        raise Exception(f"Git command failed: {' '.join(cmd)}")


def commit_and_push(version_file: Path, version: str) -> None:
    """Commit version file changes and push to repository.

    Args:
        version_file: Path to the version file
        version: New version string
    """
    commands = [
        ["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"],
        ["git", "config", "--global", "user.name", "github-actions[bot]"],
        ["git", "add", str(version_file)],
        ["git", "commit", "-m", f"chore: update available upstream version to {version}"],
        ["git", "push", "origin", "main"],
    ]

    for cmd in commands:
        run_git_command(cmd)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Commit and push version file updates")
    parser.add_argument("version_file", type=Path, help="Path to the version file to commit")
    return parser.parse_args()


def main() -> None:
    """Main function to commit and push version updates."""
    args = parse_args()
    version_file = args.version_file

    if not version_file.exists():
        print(f"Version file not found: {version_file}")
        exit(1)

    version = version_file.read_text().strip()
    commit_and_push(version_file, version)
    print("Changes committed and pushed")


if __name__ == "__main__":
    main()
