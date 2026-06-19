#!/usr/bin/env python3
"""Update version references in README.md and VERSION based on the Dockerfile.

The version tag is derived from two values declared in the Dockerfile:

  - the apt-cacher-ng version from ``ARG APT_CACHER_NG_VERSION=<version>``
  - the Ubuntu base image date from ``FROM ubuntu:jammy-<YYYYMMDD>``

producing a tag of the form ``v<version>-<YYYYMMDD>`` (for example
``v3.7.4-20260509``). This tag is written to the ``VERSION`` file and used to
refresh every matching version reference in ``README.md``.

This keeps the Dockerfile as the single source of truth: when Dependabot bumps
the Ubuntu base image date (or a maintainer bumps ``APT_CACHER_NG_VERSION``),
both ``README.md`` and ``VERSION`` are updated to match.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Files the script manages. VERSION is created if it does not yet exist.
DOCKERFILE_PATH = Path("Dockerfile")
README_PATH = Path("README.md")
VERSION_PATH = Path("VERSION")

# apt-cacher-ng version declared via ARG, e.g. ARG APT_CACHER_NG_VERSION=3.7.4
_VERSION_ARG_PATTERN = r"ARG\s+APT_CACHER_NG_VERSION\s*=\s*(\S+)"

# Ubuntu base image date, e.g. FROM ubuntu:jammy-20260509 -> 20260509
_BASE_IMAGE_PATTERN = r"FROM\s+ubuntu:jammy-(\d{8})"


def extract_version_from_dockerfile(dockerfile_path: Path) -> str:
    """Extract the apt-cacher-ng version (e.g. '3.7.4') from the Dockerfile.

    Args:
        dockerfile_path: Path to the Dockerfile

    Returns:
        The apt-cacher-ng version string

    Raises:
        ValueError: If the APT_CACHER_NG_VERSION ARG is not found
    """
    content = dockerfile_path.read_text()
    match = re.search(_VERSION_ARG_PATTERN, content)

    if not match:
        raise ValueError(
            "Could not find 'ARG APT_CACHER_NG_VERSION=...' in Dockerfile"
        )

    return match.group(1).strip()


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


def update_readme_versions(readme_path: Path, acng_version: str, new_date: str) -> int:
    """Update all version references in README.md with the new version tag.

    Replaces every ``v<acng_version>-<YYYYMMDD>`` occurrence with
    ``v<acng_version>-<new_date>`` so the date (and version prefix) always
    match the Dockerfile.

    Args:
        readme_path: Path to the README.md file
        acng_version: The apt-cacher-ng version (e.g. '3.7.4')
        new_date: The new date string in YYYYMMDD format

    Returns:
        Number of replacements made
    """
    content = readme_path.read_text()

    # Match any v<major>.<minor>.<patch>-<YYYYMMDD> tag so both the version
    # prefix and the date track the Dockerfile. This handles base-image date
    # bumps from Dependabot and manual APT_CACHER_NG_VERSION bumps alike.
    pattern = r"v\d+\.\d+\.\d+-\d{8}"
    full_version = f"v{acng_version}-{new_date}"

    # Count matches before replacement
    matches = re.findall(pattern, content)

    # Perform replacement
    updated_content = re.sub(pattern, full_version, content)

    # Write back only if something changed (avoids touching mtime needlessly)
    if updated_content != content:
        readme_path.write_text(updated_content)

    return len(matches)


def update_version_file(version_path: Path, full_version: str) -> bool:
    """Write the full version tag to the VERSION file.

    Creates the file if it does not exist. The file is written with a trailing
    newline to match the POSIX text-file convention used by the existing file.

    Args:
        version_path: Path to the VERSION file
        full_version: The full version tag, e.g. 'v3.7.4-20260509'

    Returns:
        True if the file was created or changed, False if it was already up to
        date
    """
    existing = version_path.read_text().strip() if version_path.exists() else ""
    desired = f"{full_version}\n"

    if existing == full_version:
        return False

    version_path.write_text(desired)
    return True


def main() -> int:
    """Main entry point."""
    dockerfile_path = DOCKERFILE_PATH
    readme_path = README_PATH
    version_path = VERSION_PATH

    # Validate required inputs exist
    if not dockerfile_path.exists():
        print(f"Error: {dockerfile_path} not found", file=sys.stderr)
        return 1

    if not readme_path.exists():
        print(f"Error: {readme_path} not found", file=sys.stderr)
        return 1

    # VERSION is optional on input: it is created if missing.

    try:
        # Extract version and date from Dockerfile
        acng_version = extract_version_from_dockerfile(dockerfile_path)
        new_date = extract_date_from_dockerfile(dockerfile_path)
        full_version = f"v{acng_version}-{new_date}"
        print(f"Derived version from Dockerfile: {full_version}")

        # Update README.md
        num_readme_updates = update_readme_versions(readme_path, acng_version, new_date)
        if num_readme_updates > 0:
            print(f"Updated {num_readme_updates} version reference(s) in {readme_path}")
        else:
            print(f"No version references found to update in {readme_path}")

        # Update VERSION file
        version_changed = update_version_file(version_path, full_version)
        if version_changed:
            print(f"Updated {version_path} -> {full_version}")
        else:
            print(f"{version_path} already up to date ({full_version})")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
