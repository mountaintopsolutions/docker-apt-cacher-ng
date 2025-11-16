# Project Guidelines: docker-apt-cacher-ng

## Repository Overview

This is a maintained fork of [sameersbn/docker-apt-cacher-ng](https://github.com/sameersbn/docker-apt-cacher-ng) with enhanced automation and modern CI/CD practices.

**Purpose**: Provides a containerized apt-cacher-ng proxy cache for Debian/Ubuntu packages, reducing bandwidth and installation time for repeated package downloads.

**Current Version**: apt-cacher-ng v3.7.4 with Ubuntu Jammy base image (date-versioned, e.g., v3.7.4-20251013)

**Distribution**: Published to GitHub Container Registry at `ghcr.io/mountaintopsolutions/apt-cacher-ng`

**Multi-Architecture Support**: amd64, arm64, armv7

## Key Project Files

### Core Application Files

- **Dockerfile**: Ubuntu Jammy base image with apt-cacher-ng v3.7.4 installation
  - Base image format: `FROM ubuntu:jammy-YYYYMMDD` (e.g., `ubuntu:jammy-20251013`)
  - Configures ForeGround mode (enabled) and PassThroughPattern (allow all)
  - Exposes port 3142/tcp
  - Includes health check endpoint: `/acng-report.html`

- **entrypoint.sh**: Container startup script with critical functionality
  - Creates directories: `/run/apt-cacher-ng`, cache dir, log dir
  - Handles custom config directory mounting at `APT_CACHER_NG_CONFIG_DIR=/etc/apt-cacher-ng/user-config`
  - Supports custom command arguments (anything starting with `-` or `apt-cacher-ng` is passed as args)
  - **Log Aggregation** (critical feature): Tails three log files in background
    - `/var/log/apt-cacher-ng/apt-cacher.log` - main activity log
    - `/var/log/apt-cacher-ng/apt-cacher.err` - error log
    - `/var/log/apt-cacher-ng/apt-cacher.dbg` - debug log
  - Uses `tail -f` on available log files to stream logs to Docker stdout

### Python Automation

- **update-version.py**: Synchronizes version references between Dockerfile and README.md
  - Extracts YYYYMMDD date from `FROM ubuntu:jammy-YYYYMMDD` pattern in Dockerfile
  - Updates all version references in README.md matching pattern `v3.7.4-YYYYMMDD`
  - Uses pathlib for file operations and regex for pattern matching
  - Type hints throughout with `from __future__ import annotations`
  - Exit code 0 on success, 1 on error
  - Called automatically by `update-version.yml` GitHub Actions workflow

### GitHub Actions Workflows

- **.github/workflows/build.yml**: Main CI/CD pipeline
  - Triggers: push to master/tags matching `v*.*.*`, pull requests, manual dispatch
  - Manual dispatch allows custom apt-cacher-ng version override
  - Jobs:
    1. **build-test-image**: Builds single-platform (amd64) test image with caching
       - Runs Trivy security scan for HIGH/CRITICAL CVEs
       - Uploads SARIF results to GitHub Security tab
       - Does not block on vulnerabilities (exit-code: 0)
    2. **test-integration**: Docker Compose integration tests (requires build-test-image)
       - 6 comprehensive tests:
         1. Service accessibility via `/acng-report.html`
         2. Package download through cache (downloads curl package)
         3. Log file creation and tailing verification
         4. Health check validation
         5. Cache directory functionality
         6. Configuration reload capability
  - **Publish job** (on version tags): Builds multi-platform images (amd64, arm64, armv7)
    - Pushes to ghcr.io with semantic versioning tags
    - Uses Docker buildx for multi-architecture builds

- **.github/workflows/update-version.yml**: Auto-versioning workflow
  - Triggers: Dockerfile changes on pull requests and master branch
  - Purpose: Keep README.md version strings synchronized with Dockerfile
  - Flow on master branch:
    1. Runs `update-version.py` script
    2. Extracts version from Dockerfile
    3. Checks if README.md changed
    4. If changed: commits, creates annotated tag, pushes both
    5. Tag format: `v3.7.4-YYYYMMDD` (triggers `build.yml` publish job)
  - Flow on pull requests: validates that script runs without errors
  - Uses `github-actions[bot]` for automated commits/tags

### Dependency Management

- **.github/dependabot.yml**: Automated dependency updates
  - Docker updates: Ubuntu base image (scheduled daily)
  - GitHub Actions updates: all action dependencies (monthly)
  - Creates PRs that are automatically tested and merged

- **.github/workflows/dependabot-auto-merge.yml**: Automated Dependabot PR handling
  - **Auto-Approval**: Automatically approves PRs from dependabot[bot]
  - **Test Validation**: Waits for build.yml workflow to complete successfully
    - Polls every 30 seconds with 30-minute timeout
    - Verifies all CI checks pass (build, security scan, integration tests)
  - **Auto-Merge**: Merges PR automatically after successful tests
    - Uses merge commit strategy (preserves Dependabot PR history)
    - Only merges if all status checks pass
  - **Security**: Uses pull_request_target with strict verification
    - Verifies PR author is dependabot[bot] before any action
    - Minimal permissions per job (least privilege principle)
  - **Concurrency Control**: Prevents race conditions on the same PR

- **.github/workflows/scripts/**: Utility scripts
  - `tag-and-release.sh`: Manual tagging utility (alternative to auto-tagging)
  - `release-notes.sh`: Generate release notes from commit history

## Automation Flow and Version Management

### Complete Release Pipeline

```
1. Dependabot PR: ubuntu:jammy base image update (or GitHub Actions update)
   ↓
2. dependabot-auto-merge.yml workflow triggers:
   - Auto-approves the PR
   - Waits for build.yml tests to complete
   - Auto-merges if all tests pass
   ↓
3. Dockerfile change detected in master branch (if ubuntu update)
   ↓
4. update-version.yml runs:
   - Extracts new date from Dockerfile
   - Updates all v3.7.4-YYYYMMDD refs in README.md
   - Creates commit with message "chore: update version to v3.7.4-YYYYMMDD"
   - Creates annotated tag v3.7.4-YYYYMMDD
   ↓
5. Tag push triggers build.yml:
   - Builds multi-arch images (amd64, arm64, armv7)
   - Runs all 6 integration tests
   - Runs Trivy security scan
   - Publishes to ghcr.io with tags:
     * v3.7.4-20251013 (specific date)
     * v3.7.4 (latest stable)
     * latest (newest)
```

### Version Format Specification

- **Semantic Version**: v3.7.4 (apt-cacher-ng upstream version)
- **Full Version Tag**: v3.7.4-YYYYMMDD (includes Ubuntu base image date)
- **YYYYMMDD**: Extracted from `FROM ubuntu:jammy-YYYYMMDD` in Dockerfile
- **Example**: v3.7.4-20251013 means apt-cacher-ng 3.7.4 with Ubuntu Jammy from 2025-10-13

## Environment Variables

The following environment variables are set in the Dockerfile and used by scripts:

- `APT_CACHER_NG_VERSION=3.7.4` - Built-in version (match with Dockerfile tag when updating)
- `APT_CACHER_NG_CACHE_DIR=/var/cache/apt-cacher-ng` - Package cache location
- `APT_CACHER_NG_LOG_DIR=/var/log/apt-cacher-ng` - Log directory (tailed by entrypoint)
- `APT_CACHER_NG_CONFIG_DIR=/etc/apt-cacher-ng/user-config` - Custom config mount point
- `APT_CACHER_NG_USER=apt-cacher-ng` - Service user account

## Code Style Guidelines

### Python Code

- Use type hints on ALL functions, methods, and class attributes
- Import `from __future__ import annotations` for forward compatibility
- Use `pathlib.Path` instead of string paths
- Use f-strings for string formatting
- Validate inputs at module boundaries
- Import order: stdlib, third-party, local
- Error handling: Use descriptive exceptions with sys.stderr messages
- Keep functions focused and single-purpose

**Example style** (from update-version.py):
```python
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
    pattern = r"FROM\s+ubuntu:jammy-(\d{8})"
    match = re.search(pattern, content)

    if not match:
        raise ValueError("Could not find Ubuntu base image with date pattern in Dockerfile")

    return match.group(1)
```

### Bash/Shell Scripts

- Use `set -e` for error exit on failure
- Quote all variables: `"${VAR}"` not `$VAR`
- Use descriptive function names: `create_cache_dir()` not `create_dir()`
- Add comments for non-obvious logic
- Use shellcheck-compliant syntax (available via `shellcheck` tool)
- Prefer explicit conditions: `[[ -f "$file" ]]` over `[ -f "$file" ]`

### YAML (GitHub Actions)

- Use descriptive job names: `build-test-image` (kebab-case)
- Use descriptive step names: clear action description starting with verb
- Add comments for complex logic or non-obvious configuration
- Organize jobs by dependency: build, test, publish
- Use step IDs for output: `id: check`, reference as `${{ steps.check.outputs.changed }}`

**Example convention**:
```yaml
jobs:
  build-test-image:
    name: Build Image for Testing & Scan Image
    runs-on: ubuntu-latest
    permissions:
      packages: write
      security-events: write

    steps:
      - name: Checkout git repo
        uses: actions/checkout@v5

      - name: Build test image with caching
        uses: docker/build-push-action@v6
        with:
          load: true
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Docker

- Multi-stage builds when appropriate
- Minimize layer count: combine RUN commands with `&&`
- Use non-root user: `APT_CACHER_NG_USER=apt-cacher-ng`
- Always include HEALTHCHECK for services
- Expose ports explicitly
- Document all environment variables

## Testing Requirements

All changes must pass the following validation:

### 1. Integration Tests (6 tests in build.yml)

Tests run in Docker Compose with isolated containers:

- **Test 1 - Service Accessibility**: HTTP GET to `/acng-report.html` returns content with "apt-cacher"
- **Test 2 - Package Download**: Client can download package through cache (e.g., `apt-get download curl`)
- **Test 3 - Log File Creation**: All three log files created and tailable
  - Validates: apt-cacher.log, apt-cacher.err, apt-cacher.dbg exist
  - Validates: `tail -f` produces output
- **Test 4 - Health Check**: Docker health check succeeds
- **Test 5 - Cache Functionality**: Cached files persist in volume
- **Test 6 - Configuration**: Custom config directory mounting works

### 2. Security Scanning

- **Trivy**: Scans image for HIGH and CRITICAL CVEs
- **Exit Code**: 0 (non-blocking, but results uploaded to GitHub Security tab)
- **Frequency**: Every build (pull requests and master)

### 3. Multi-Architecture Build

- Must succeed for: amd64, arm64, armv7
- Only on version tags matching `v*.*.*`
- Uses Docker buildx for cross-platform building

## Updating Dockerfile

### When to Update

- Dependabot creates PR with new Ubuntu base image date
- Manual update required for apt-cacher-ng version bump

### How to Update

1. Update the FROM line in Dockerfile:
   ```dockerfile
   FROM ubuntu:jammy-YYYYMMDD
   ```
   Replace YYYYMMDD with new date (e.g., 20251013)

2. Optionally update APT_CACHER_NG_VERSION if upgrading package:
   ```dockerfile
   ARG APT_CACHER_NG_VERSION=3.7.4
   ```

3. Commit with conventional commit message:
   ```
   chore: update ubuntu base image to 20251013
   ```
   OR
   ```
   feat: upgrade apt-cacher-ng to 3.7.5
   ```

4. Push to master branch

5. `update-version.yml` will automatically:
   - Detect Dockerfile change
   - Extract new date
   - Update README.md
   - Create commit with new version
   - Create and push version tag (v3.7.4-YYYYMMDD)
   - Trigger `build.yml` to build and publish

### Important Notes

- **DO NOT** manually create version tags; let `update-version.yml` handle this
- **DO** ensure Dockerfile has format: `FROM ubuntu:jammy-YYYYMMDD` (exactly)
- **DO** update version references in README.md manually only if script fails
- Version tags should only be created when Ubuntu base image date changes

## Working with Git and Commits

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature (e.g., "feat: add cache warming script")
- `fix:` - Bug fix (e.g., "fix: log tailing timeout issue")
- `chore:` - Maintenance (e.g., "chore: update version to v3.7.4-20251013")
- `build:` - Build/CI changes (e.g., "build(deps): update actions")
- `docs:` - Documentation (e.g., "docs: update README with examples")
- `test:` - Test additions (e.g., "test: add cache persistence test")

### Branch Strategy

- **master**: Production-ready code only
- Feature branches: `feature/descriptive-name` or `fix/issue-number`
- All changes via pull request with successful build + test run

### Tags

- Version tags: `v3.7.4-YYYYMMDD` (automatic, created by update-version.yml)
- Release tags: Annotated tags with commit message describing changes
- Do not manually create version tags (workflow automates this)

## Maintenance and Troubleshooting

### Common Issues

1. **update-version.yml not triggered**
   - Ensure Dockerfile change is committed to master (not just local)
   - Check workflow permissions: `permissions: { contents: write }`
   - Verify Dockerfile has exact pattern: `FROM ubuntu:jammy-YYYYMMDD`

2. **Tests failing**
   - Check log output in GitHub Actions
   - Verify image builds locally: `docker build -t apt-cacher-ng:test .`
   - Run docker-compose tests locally: `docker compose -f docker-compose.test.yml up`

3. **Multi-arch build failing**
   - Ensure tag matches `v*.*.*` pattern (only tags trigger publish job)
   - Check buildx platform support: `docker buildx ls`
   - Verify registry credentials are set (ghcr.io token)

4. **Trivy scan showing vulnerabilities**
   - Review scan results in GitHub Security tab
   - Update Ubuntu base image to latest patch (Dependabot handles this)
   - Check if vulnerability is marked as unfixed (might be expected)

### Manual Version Tagging (Emergency Only)

If automatic tagging fails, manually tag and push:

```bash
# Extract version from Dockerfile
VERSION=$(grep -oP 'FROM ubuntu:jammy-\K\d{8}' Dockerfile)

# Create annotated tag
git tag -a "v3.7.4-${VERSION}" -m "Release v3.7.4-${VERSION}"

# Push tag
git push origin "v3.7.4-${VERSION}"
```

## Development Workflow

### Making Changes

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following style guidelines
3. Test locally: `docker build .` and run integration tests
4. Commit with conventional commits
5. Push and create pull request
6. Wait for build.yml to complete (tests + security scan)
7. Merge after approval

### Testing Changes Locally

```bash
# Build test image
docker build -t apt-cacher-ng:test .

# Run docker-compose tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Or test individual functionality
docker run -d -p 3142:3142 apt-cacher-ng:test
curl http://localhost:3142/acng-report.html
```

### Python Script Development

For changes to `update-version.py`:

```bash
# Run script locally
python update-version.py

# View changes
git diff README.md

# Test with dry-run (create copy of README first)
cp README.md README.md.bak
python update-version.py
git diff README.md
mv README.md.bak README.md
```

## Configuration and Customization

### Runtime Configuration

Users can mount custom apt-cacher-ng config at container start:

```bash
docker run -v /path/to/config:/etc/apt-cacher-ng/user-config \
           ghcr.io/mountaintopsolutions/apt-cacher-ng:v3.7.4-20251013
```

The entrypoint.sh will copy files from user-config to main config directory.

### Logging

All three log files are tailed and streamed to stdout:
- `apt-cacher.log` - Standard activity log
- `apt-cacher.err` - Errors and warnings
- `apt-cacher.dbg` - Debug information (if enabled in config)

Logs can be accessed via `docker logs <container>`.

### Port Configuration

Default port is 3142/tcp (standard apt-cacher-ng port). To use custom port:

```bash
docker run -p 8080:3142 ghcr.io/mountaintopsolutions/apt-cacher-ng:latest
```

## Performance Considerations

- Cache volume should be on fast storage (SSD preferred)
- Health check interval: 10s (configurable in docker-compose)
- Log tailing uses `tail -f` (minimal overhead)
- No explicit memory limits configured (can be set at container runtime)

## Security Notes

- Service runs as non-root user: `apt-cacher-ng`
- Cache and log directories owned by service user
- Health check validates endpoint accessibility
- Regular Trivy scans in CI/CD catch vulnerabilities
- Dependabot automatically updates base image
- PassThroughPattern enabled to allow all packages through (customize as needed)

## References

- **Upstream Project**: https://github.com/sameersbn/docker-apt-cacher-ng
- **apt-cacher-ng Documentation**: https://wiki.debian.org/AptCacherNg
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Conventional Commits**: https://www.conventionalcommits.org/
