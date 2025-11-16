#!/usr/bin/env python3
"""Update version references in README.md based on Dockerfile Ubuntu base image."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_date_from_dockerfile(dockerfile_path: Path) -> str:
    """Extract the YYYYMMDD date from the Ubuntu base image in Dockerfile.

    Args:
        dockerfile_path: Path to the Dockerfile

    Returns:
        The date string in YYYYMMDD format

    Raises:
        ValueError: If the date pattern is not found in the Dockerfile
    """
    content = dockerfile_path.read_text()

    # Match pattern: FROM ubuntu:jammy-YYYYMMDD
    pattern = r"FROM\s+ubuntu:jammy-(\d{8})"
    match = re.search(pattern, content)

    if not match:
        raise ValueError("Could not find Ubuntu base image with date pattern in Dockerfile")

    return match.group(1)


def update_readme_versions(readme_path: Path, old_date: str, new_date: str) -> int:
    """Update all version references in README.md with the new date.

    Args:
        readme_path: Path to the README.md file
        old_date: The old date to replace
        new_date: The new date to use

    Returns:
        Number of replacements made
    """
    content = readme_path.read_text()

    # Replace pattern: v3.7.4-YYYYMMDD with v3.7.4-<new_date>
    pattern = r"(v3\.7\.4-)(\d{8})"

    # Count matches before replacement
    matches = re.findall(pattern, content)

    # Perform replacement
    updated_content = re.sub(pattern, rf"\g<1>{new_date}", content)

    # Write back to file
    readme_path.write_text(updated_content)

    return len(matches)


def main() -> int:
    """Main entry point."""
    dockerfile_path = Path("Dockerfile")
    readme_path = Path("README.md")

    # Validate files exist
    if not dockerfile_path.exists():
        print(f"Error: {dockerfile_path} not found", file=sys.stderr)
        return 1

    if not readme_path.exists():
        print(f"Error: {readme_path} not found", file=sys.stderr)
        return 1

    try:
        # Extract date from Dockerfile
        new_date = extract_date_from_dockerfile(dockerfile_path)
        print(f"Found Ubuntu base image date: {new_date}")

        # Update README.md
        num_replacements = update_readme_versions(readme_path, "", new_date)

        if num_replacements > 0:
            print(f"Updated {num_replacements} version reference(s) in {readme_path}")
            print(f"All versions now reference: v3.7.4-{new_date}")
        else:
            print("No version references found to update")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
