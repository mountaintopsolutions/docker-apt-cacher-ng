#!/usr/bin/env python3
"""Check for new versions of apt-cacher-ng on Debian repository."""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from packaging import version
import argparse
import sys


def get_latest_tarball() -> Dict[str, any]:
    """Fetch and parse the latest version from Debian repository."""
    url = "https://ftp.debian.org/debian/pool/main/a/apt-cacher-ng/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tarballs = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.endswith(".orig.tar.xz"):
            ver_match = re.search(r"apt-cacher-ng_(.+)\.orig\.tar\.xz", href)
            if ver_match:
                ver_str = ver_match.group(1)
                date_str = link.find_parent("tr").find_all("td")[2].text.strip()
                date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                tarballs.append(
                    {"version": ver_str, "parsed_version": version.parse(ver_str), "date": date, "filename": href}
                )

    return sorted(tarballs, key=lambda x: x["parsed_version"], reverse=True)[0]


def get_current_version(version_file: Path) -> Optional[str]:
    """Read current version from version file.

    Args:
        version_file: Path to the version file

    Returns:
        The current version string or None if file doesn't exist
    """
    if version_file.exists():
        return version_file.read_text().strip()
    return None


def update_version(version_file: Path, new_version: str) -> None:
    """Write new version to version file.

    Args:
        version_file: Path to the version file
        new_version: Version string to write
    """
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(new_version)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Check for new versions of apt-cacher-ng")
    parser.add_argument("version_file", type=Path, help="Path to the version file to check and update")
    return parser.parse_args()


def main() -> None:
    """Main function to check and update version."""
    args = parse_args()
    version_file = args.version_file

    latest = get_latest_tarball()
    current = get_current_version(version_file)

    if not current or version.parse(latest["version"]) > version.parse(current):
        print(f"New version found: {latest['version']} (current: {current})")
        update_version(version_file, latest["version"])
        print(f"Version file updated: {version_file}")
        sys.exit(0)  # New version found
    else:
        print("Already at latest version")
        sys.exit(1)  # No new version


if __name__ == "__main__":
    main()
