#!/bin/bash

# Function to find the VERSION file
find_version_file() {
  if [ "$(pwd)" == "$(dirname "$0")" ]; then
    # If in the scripts directory, look in ..
    if [ -f ../VERSION ]; then
      echo "../VERSION"
    fi
  else
    # If not in the scripts directory, look in . and ..
    if [ -f VERSION ]; then
      echo "VERSION"
    elif [ -f ../VERSION ]; then
      echo "../VERSION"
    fi
  fi
}

# Get the path to the VERSION file
VERSION_FILE=$(find_version_file)

# Check if the VERSION file was found
if [ -z "$VERSION_FILE" ]; then
  echo "Could not find version file, check your working directory."
  exit 1
fi

# Read the version from the VERSION file
VERSION=$(cat "$VERSION_FILE")

# Check if the version is not empty
if [ -z "$VERSION" ]; then
  echo "Version is empty. Please check the VERSION file."
  exit 1
fi

# Create a git tag
git tag "$VERSION"

# Push the tag to GitHub
git push origin "$VERSION"

echo "Tagged and pushed version $VERSION"