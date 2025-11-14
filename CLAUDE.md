# CLAUDE.md - AI Assistant Guide for docker-apt-cacher-ng

This document provides comprehensive guidance for AI assistants working with the docker-apt-cacher-ng repository. Last updated: 2025-11-14

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Key Files and Components](#key-files-and-components)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Build and Release Process](#build-and-release-process)
- [Conventions and Best Practices](#conventions-and-best-practices)
- [Common Tasks](#common-tasks)
- [Important Notes for AI Assistants](#important-notes-for-ai-assistants)

---

## Project Overview

**Project Name:** docker-apt-cacher-ng
**Purpose:** Docker container image for Apt-Cacher NG, a caching proxy for Linux package files
**Maintainer:** mountaintopsolutions (fork of sameersbn/docker-apt-cacher-ng)
**Current Version:** v3.7.4-20250819 (see VERSION file)
**License:** ISC
**Container Registry:** ghcr.io/mountaintopsolutions/apt-cacher-ng

### What This Project Does

This project containerizes **Apt-Cacher NG**, a specialized caching proxy that:
- Caches Debian and Debian-based distribution packages
- Reduces bandwidth usage and improves build times
- Serves cached packages to multiple clients (Docker containers, hosts, CI/CD pipelines)
- Provides a web-based management interface on port 3142

### Key Context

- This is an **actively maintained fork** pulling useful features from abandoned PRs
- The project has been modernized with updated base images and CI/CD infrastructure
- Only publishes to **GHCR.io** (GitHub Container Registry), not Docker Hub
- Supports **multi-platform** builds: linux/amd64, linux/arm64/v8, linux/arm/v7

---

## Repository Structure

```
docker-apt-cacher-ng/
├── .github/
│   └── workflows/
│       └── build.yml              # CI/CD pipeline (build, test, security scan, publish)
├── examples/                      # Client configuration examples
│   ├── 01proxy                    # APT proxy config file for client systems
│   └── host-proxy-detect.sh       # Dynamic proxy detection script
├── kubernetes/                    # Kubernetes deployment manifests
│   ├── pod.yml                    # Pod specification with resource limits
│   └── service.yml                # LoadBalancer service (port 3142)
├── scripts/                       # Release automation
│   ├── release-notes.sh           # Generate changelog between tags
│   └── tag-and-release.sh         # Create git tags and push
├── .dockerignore                  # Docker build exclusions
├── .gitignore                     # Git exclusions
├── Dockerfile                     # Container image definition (Ubuntu Jammy base)
├── docker-compose.yml             # Development/local deployment composition
├── entrypoint.sh                  # Container startup script (critical!)
├── LICENSE                        # ISC License
├── Makefile                       # Build automation (simple wrapper)
├── README.md                      # User-facing documentation
└── VERSION                        # Single source of truth for version (v3.7.4-20250819)
```

---

## Key Files and Components

### Critical Files

#### `Dockerfile`
- **Base Image:** `ubuntu:jammy-20251001` (Ubuntu 22.04 LTS, October 2025 security updates)
- **Installs:** apt-cacher-ng v3.7.4, ca-certificates, wget
- **Key Modifications:**
  - Enables ForeGround mode (required for Docker)
  - Enables PassThroughPattern wildcard (allows broader caching)
  - Runs `apt-get dist-upgrade` for security patches
- **Exposed Port:** 3142/TCP
- **Health Check:** Verifies `/acng-report.html` accessibility every 10s
- **User:** Runs as non-root `apt-cacher-ng` user

#### `entrypoint.sh` (CRITICAL - REVIEW CAREFULLY BEFORE MODIFYING)
This is the **most important runtime file**. It handles:

1. **Directory Setup:**
   - Creates `/run/apt-cacher-ng` (PID files)
   - Creates cache directory with proper permissions
   - Creates log directory with proper permissions

2. **User Config Injection:**
   - Copies files from `/etc/apt-cacher-ng/user-config` to main config dir
   - Allows runtime config customization without image rebuild

3. **Argument Handling:**
   - Supports pass-through of apt-cacher-ng command-line arguments
   - Detects `-` prefixed flags or `apt-cacher-ng` commands
   - Preserves `EXTRA_ARGS` for service startup

4. **Log Aggregation (IMPORTANT):**
   - Waits for log files to be created
   - Tails all log files: `apt-cacher.log`, `apt-cacher.err`, `apt-cacher.dbg`
   - Forwards logs to stdout for `docker logs` visibility
   - Uses `tail -f` with multiple files for aggregation headers

5. **Process Management:**
   - Uses `start-stop-daemon` for proper daemon handling
   - Runs apt-cacher-ng as dedicated user with correct permissions

**CRITICAL:** Changes to `entrypoint.sh` must be tested thoroughly with all CI tests.

#### `VERSION`
- Single-line file containing current version string
- Format: `v{apt-cacher-ng-version}-{base-image-date}`
- Example: `v3.7.4-20250819`
- Used by release scripts and documentation
- **MUST** be updated when creating new releases

#### `.github/workflows/build.yml`
Comprehensive CI/CD pipeline with **3 jobs**:

1. **build-test-image:** Builds test image + Trivy security scan
2. **test-integration:** 6 integration tests in Docker Compose
3. **build-and-push-docker-image:** Multi-platform build and push to GHCR.io

See [Testing Strategy](#testing-strategy) for details.

---

## Development Workflow

### Branch Strategy

- **Main Branch:** `master`
- **Feature Branches:** Use descriptive names (e.g., `feature/log-rotation`, `fix/entrypoint-permissions`)
- **Release Tags:** Follow pattern `v{version}-{date}` (e.g., `v3.7.4-20251001`)

### Making Changes

1. **For Dockerfile changes:**
   - Update base image tag when new Ubuntu releases are available
   - Maintain current apt-cacher-ng version unless upgrading
   - Ensure `ForeGround: 1` and `PassThroughPattern` remain enabled
   - Test health check functionality

2. **For entrypoint.sh changes:**
   - **CRITICAL:** This file controls all runtime behavior
   - Test with all 6 integration tests (see `.github/workflows/build.yml`)
   - Verify log aggregation still works (Test 6)
   - Ensure permissions are correctly set
   - Test argument pass-through functionality

3. **For CI/CD changes:**
   - Test with workflow_dispatch before merging
   - Verify all 3 jobs complete successfully
   - Check Trivy scan results in Security tab
   - Ensure multi-platform builds work

4. **For configuration changes:**
   - Test with user-config volume mount
   - Verify config files are copied correctly
   - Ensure no breaking changes to existing deployments

### Environment Variables

When working with the container, these are the key environment variables:

```bash
APT_CACHER_NG_CACHE_DIR=/var/cache/apt-cacher-ng  # Package cache storage
APT_CACHER_NG_LOG_DIR=/var/log/apt-cacher-ng      # Log files location
APT_CACHER_NG_CONFIG_DIR=/etc/apt-cacher-ng/user-config  # User config injection
APT_CACHER_NG_USER=apt-cacher-ng                   # Runtime user
```

**Note:** These are baked into the Dockerfile and should rarely need changes.

---

## Testing Strategy

### Local Testing

```bash
# Build test image
make build

# Run locally
docker run --name apt-cacher-ng-test --init --rm \
  -p 3142:3142 \
  ghcr.io/mountaintopsolutions/apt-cacher-ng

# Test with docker-compose
docker compose up -d
docker compose logs -f
```

### CI/CD Testing Pipeline

The GitHub Actions workflow (`.github/workflows/build.yml`) runs **3 jobs sequentially**:

#### Job 1: Build Test Image & Security Scan

**Purpose:** Build single-platform image and scan for vulnerabilities

**Steps:**
1. Checkout code
2. Setup Docker Buildx
3. Build for linux/amd64 with GitHub Actions cache
4. Run **Trivy vulnerability scanner**:
   - Scans for HIGH/CRITICAL CVEs
   - Checks OS and library vulnerabilities
   - Uploads results to GitHub Security tab (SARIF format)
   - **Does NOT block builds** (exit-code: 0) - informational only

#### Job 2: Integration Tests (MOST IMPORTANT)

**Purpose:** Validate all container functionality in realistic environment

Creates ephemeral docker-compose stack with:
- `apt-cacher-ng` service (production config)
- `test-client` service (Ubuntu client for testing)
- Named volumes for persistence
- Health checks with 30s startup grace period

**6 Integration Tests:**

1. **Service Accessibility Test**
   ```bash
   curl -f "http://localhost:3142/acng-report.html" | grep -i "apt-cacher"
   ```
   - Verifies web interface responds
   - Confirms service is running

2. **Package Download Test**
   ```bash
   docker exec test-client apt-get update && apt-get download curl
   ```
   - Downloads package through proxy
   - Validates basic apt-get functionality

3. **Log File Creation Test**
   ```bash
   ls -la /var/log/apt-cacher-ng/ | grep -E '(apt-cacher\.(log|err|dbg))'
   ```
   - Verifies all 3 log files exist
   - Confirms logging is configured

4. **Cache Functionality Test**
   ```bash
   # Download same package twice
   apt-get download curl
   # Verify .deb files in cache
   find /var/cache/apt-cacher-ng -name '*.deb'
   ```
   - **CRITICAL:** Validates caching actually works
   - Ensures not just pass-through mode

5. **Management Interface Test**
   ```bash
   curl -f "http://localhost:3142/acng-report.html"
   ```
   - Confirms web UI accessibility
   - Validates admin features

6. **Log Aggregation Test (CRITICAL FOR ENTRYPOINT CHANGES)**
   ```bash
   # Trigger activity
   apt-get update
   # Check for aggregation headers
   docker logs | grep -E "==>.*/var/log/apt-cacher-ng"
   # Check for successful cache operations
   docker logs | grep -E "^.*[0-9]{10}\|[IO]\|.*InRelease"
   ```
   - **CRITICAL:** Validates entrypoint log tailing
   - Confirms `tail -f` aggregation works
   - Verifies InRelease file caching (proves caching works)

**Important:** All tests must pass before proceeding to build-and-push job.

#### Job 3: Build and Push Docker Image

**Purpose:** Multi-platform build and publish to GHCR.io

**Only runs if:** Jobs 1 and 2 succeed

**Platforms Built:**
- linux/amd64 (Intel/AMD 64-bit)
- linux/arm64/v8 (ARM 64-bit - Raspberry Pi 4, Apple Silicon)
- linux/arm/v7 (ARM 32-bit - older Raspberry Pi)

**Tagging Strategy:**
- **Tag pushes** (e.g., `v3.7.4-20251001`):
  - `ghcr.io/mountaintopsolutions/apt-cacher-ng:v3.7.4-20251001`
  - `ghcr.io/mountaintopsolutions/apt-cacher-ng:latest`
- **Branch/PR pushes:**
  - `ghcr.io/mountaintopsolutions/apt-cacher-ng:sha-{commit}`
- **Pull requests:** Build only, no push

**Caching:**
- Uses GitHub Actions cache (type=gha, mode=max)
- Speeds up multi-platform builds significantly

---

## Build and Release Process

### Version Management

The **VERSION file** is the single source of truth for versioning:

```bash
# VERSION file format
v{apt-cacher-ng-version}-{base-image-date}

# Example
v3.7.4-20251001
```

This combines:
- Upstream apt-cacher-ng version (3.7.4)
- Base Ubuntu image date (20251001 = October 1, 2025)

### Creating a New Release

1. **Update VERSION file:**
   ```bash
   echo "v3.7.4-20251115" > VERSION
   ```

2. **Update base image in Dockerfile (if needed):**
   ```dockerfile
   FROM ubuntu:jammy-20251115
   ```

3. **Update README.md references** (search for old version):
   ```bash
   # Find all version references
   grep -n "v3.7.4-20250819" README.md
   # Update manually
   ```

4. **Commit changes:**
   ```bash
   git add VERSION Dockerfile README.md
   git commit -m "chore: bump to v3.7.4-20251115"
   ```

5. **Create and push tag using script:**
   ```bash
   ./scripts/tag-and-release.sh
   ```
   This script:
   - Reads VERSION file
   - Creates annotated git tag
   - Pushes to origin
   - Triggers CI/CD workflow

6. **Generate release notes (optional):**
   ```bash
   ./scripts/release-notes.sh v3.7.4-20251115
   ```

7. **Monitor CI/CD:**
   - Watch GitHub Actions workflow
   - Verify all 3 jobs succeed
   - Check GHCR.io for new image tags
   - Review Trivy security scan results

### Manual Build

```bash
# Simple build (uses Makefile)
make

# Build specific tag
docker build -t ghcr.io/mountaintopsolutions/apt-cacher-ng:test .

# Multi-platform build (requires buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64/v8,linux/arm/v7 \
  -t ghcr.io/mountaintopsolutions/apt-cacher-ng:test \
  .
```

---

## Conventions and Best Practices

### Code Conventions

1. **Shell Scripts (entrypoint.sh, *.sh):**
   - Use `#!/bin/bash` shebang
   - Include `set -e` for error handling
   - Use descriptive function names
   - Add comments for complex logic
   - **MUST** pass ShellCheck validation

2. **Dockerfile:**
   - Pin base image to specific date tag (e.g., `jammy-20251001`)
   - Pin apt-cacher-ng version with `ARG`
   - Use multi-line `RUN` commands with `\` continuation
   - Clean up with `rm -rf /var/lib/apt/lists/*`
   - Document any non-obvious changes with comments

3. **GitHub Actions:**
   - Pin action versions with `@v5` (major version)
   - Use descriptive job and step names
   - Add comments explaining complex logic
   - Use `if: failure()` for debugging steps
   - Always clean up with `if: always()`

### Git Conventions

1. **Commit Messages:**
   ```
   <type>: <description>

   <optional body>
   ```

   Types:
   - `feat:` New feature
   - `fix:` Bug fix
   - `chore:` Maintenance (version bumps, dependency updates)
   - `ci:` CI/CD changes
   - `docs:` Documentation only
   - `refactor:` Code refactoring

   Examples:
   ```
   chore: bump to 20251001 base image
   ci: enhance the second logging test to validate that cache is actually working
   fix: endpoint for test 1 of ci test
   ```

2. **Branching:**
   - Keep feature branches short-lived
   - Rebase on master before merging
   - Delete branches after merge

3. **Tags:**
   - Always use annotated tags: `git tag -a v3.7.4-20251001 -m "Release v3.7.4-20251001"`
   - Follow version format strictly
   - Use `scripts/tag-and-release.sh` for consistency

### Security Best Practices

1. **Vulnerability Scanning:**
   - Trivy scan runs on every build
   - Review HIGH/CRITICAL CVEs in GitHub Security tab
   - Update base image regularly for security patches

2. **Container Security:**
   - Always run as non-root user (`apt-cacher-ng`)
   - Use health checks for reliability
   - Minimize installed packages
   - Apply `dist-upgrade` during build

3. **Secrets Management:**
   - Never commit credentials or tokens
   - Use GitHub Secrets for CI/CD
   - Use `GITHUB_TOKEN` for GHCR.io authentication

### Performance Best Practices

1. **Docker Layer Caching:**
   - Order Dockerfile commands from least to most frequently changed
   - Use GitHub Actions cache for faster CI builds
   - Use `cache-from` and `cache-to` with `mode=max`

2. **Multi-platform Builds:**
   - Build for single platform during testing (faster)
   - Build for all platforms only on final push
   - Use QEMU for cross-platform builds

---

## Common Tasks

### Update Base Image

```bash
# 1. Find latest Ubuntu Jammy tag
# Visit: https://hub.docker.com/_/ubuntu/tags?name=jammy

# 2. Update Dockerfile
FROM ubuntu:jammy-YYYYMMDD

# 3. Update VERSION file
echo "v3.7.4-YYYYMMDD" > VERSION

# 4. Update README.md (replace all version references)

# 5. Test locally
make
docker run --rm -p 3142:3142 ghcr.io/mountaintopsolutions/apt-cacher-ng:latest

# 6. Commit and tag
git add Dockerfile VERSION README.md
git commit -m "chore: bump to YYYYMMDD base image"
./scripts/tag-and-release.sh
```

### Update Apt-Cacher-NG Version

```bash
# 1. Check available versions
docker run --rm ubuntu:jammy apt-cache policy apt-cacher-ng

# 2. Update Dockerfile
ARG APT_CACHER_NG_VERSION=3.X.Y

# 3. Update VERSION file
echo "v3.X.Y-$(date +%Y%m%d)" > VERSION

# 4. Update README.md

# 5. Test locally and commit
```

### Add New Integration Test

Edit `.github/workflows/build.yml`:

```yaml
- name: Test 7 - Your new test
  run: |
    echo "Testing new functionality..."
    # Add test commands
    docker compose -f docker-compose.test.yml exec apt-cacher-ng bash -c "
      # Your test logic here
    " || exit 1
    echo "✓ Test description"
```

### Troubleshoot CI Failures

```bash
# 1. Check workflow logs in GitHub Actions

# 2. Reproduce locally with docker-compose
docker compose -f .github/workflows/docker-compose.test.yml up -d

# 3. Check container logs
docker compose logs apt-cacher-ng

# 4. Debug interactively
docker compose exec apt-cacher-ng bash
```

### Test Log Aggregation

```bash
# Run container
docker run --name test --init -d -p 3142:3142 \
  ghcr.io/mountaintopsolutions/apt-cacher-ng:latest

# Trigger activity
docker run --rm -e http_proxy=http://172.17.0.1:3142 \
  ubuntu:jammy apt-get update

# Check logs for aggregation headers
docker logs test | grep "==>.*var/log"

# Should see:
# ==> /var/log/apt-cacher-ng/apt-cacher.log <==
# ==> /var/log/apt-cacher-ng/apt-cacher.err <==
```

### Update GitHub Actions

When Dependabot creates PRs for action updates:

1. Review changelog for breaking changes
2. Test with workflow_dispatch
3. Merge if tests pass

---

## Important Notes for AI Assistants

### Critical Files - Review Before Modifying

These files require **extra scrutiny** and comprehensive testing:

1. **entrypoint.sh:**
   - Controls ALL runtime behavior
   - Any change MUST be tested with all 6 integration tests
   - Log aggregation logic is complex - test thoroughly
   - Permission handling is critical for security

2. **Dockerfile:**
   - Base image changes affect security posture
   - `ForeGround: 1` is required - don't remove
   - `PassThroughPattern` enables broad caching - keep enabled
   - Health check is used by orchestrators - keep functional

3. **.github/workflows/build.yml:**
   - All 3 jobs must succeed for release
   - Multi-platform builds are expensive - test before pushing
   - Trivy scan results go to Security tab - check after changes

### Testing Requirements

**NEVER** merge changes that:
- Fail any of the 6 integration tests
- Break log aggregation (Test 6)
- Remove health check functionality
- Change user from `apt-cacher-ng` to root
- Disable security features

**ALWAYS** test:
- Locally with `make` before pushing
- With docker-compose for integration scenarios
- Multi-platform builds for platform-specific issues
- Log aggregation after entrypoint changes

### Understanding Log Aggregation

The entrypoint implements a sophisticated log tailing mechanism:

```bash
# 1. Wait for log files to exist
while true; do
  # Check for any log file
  if [[ -f /var/log/apt-cacher-ng/apt-cacher.log ]]; then
    break
  fi
  sleep 1
done

# 2. Tail all existing log files
tail -f /var/log/apt-cacher-ng/*.log *.err *.dbg

# This produces aggregated output with headers:
# ==> /var/log/apt-cacher-ng/apt-cacher.log <==
# [log entries]
# ==> /var/log/apt-cacher-ng/apt-cacher.err <==
# [error entries]
```

**Why this matters:**
- Enables `docker logs` to show all activity
- Provides visibility without volume mounts
- Critical for debugging in production
- Test 6 validates this works correctly

### Version Management Strategy

The project uses a **dual-version** approach:

```
v{upstream-version}-{base-image-date}
  ↓                  ↓
v3.7.4        -  20251001
```

**When to bump versions:**
- **Upstream version (3.7.4):** When upgrading apt-cacher-ng package
- **Date (20251001):** When updating Ubuntu base image for security patches

**Both should be updated when:**
- Doing regular maintenance (monthly/quarterly)
- Security vulnerabilities are found
- New Ubuntu LTS point release

### Multi-Platform Build Considerations

When making changes, consider impact on all platforms:

- **linux/amd64:** Most common, fastest builds
- **linux/arm64/v8:** Raspberry Pi 4, Apple Silicon - test performance
- **linux/arm/v7:** Older ARM boards - may have memory constraints

**Test on multiple platforms if:**
- Changing shell scripts (bash compatibility)
- Adding new dependencies (package availability)
- Modifying performance-sensitive code
- Changing memory or CPU usage patterns

### Client Configuration

When helping users configure clients, remember:

**For Docker containers:**
```dockerfile
RUN echo 'Acquire::HTTP::Proxy "http://172.17.0.1:3142";' >> /etc/apt/apt.conf.d/01proxy \
 && echo 'Acquire::HTTPS::Proxy "false";' >> /etc/apt/apt.conf.d/01proxy
```

**For host systems:**
```bash
# /etc/apt/apt.conf.d/01proxy
Acquire::HTTP::Proxy "http://{docker-host-ip}:3142";
Acquire::HTTPS::Proxy "false";
```

**Important:** HTTPS proxy MUST be `false` - apt-cacher-ng doesn't cache HTTPS.

### Deployment Patterns

Common deployment scenarios:

1. **Docker CLI (development):**
   ```bash
   docker run --init -d -p 3142:3142 \
     -v /srv/apt-cache:/var/cache/apt-cacher-ng \
     ghcr.io/mountaintopsolutions/apt-cacher-ng:latest
   ```

2. **Docker Compose (production):**
   - Use named volumes for persistence
   - Add `restart: always`
   - Use `init: true` for proper signal handling

3. **Kubernetes:**
   - Use PersistentVolumeClaim for cache
   - Set resource limits (64Mi memory, 500m CPU)
   - Configure health checks (liveness/readiness)
   - Use LoadBalancer or NodePort service

### Recent Development Focus

Based on git history, current priorities are:

1. **Base image updates:** Regular security patches via Ubuntu updates
2. **Testing improvements:** Expanding CI coverage for edge cases
3. **Entrypoint robustness:** Better error handling and logging
4. **Documentation:** Keeping README and examples up-to-date

### When to Ask for Clarification

Ask the user before:
- Changing version numbers
- Modifying security-related configuration
- Removing or disabling features
- Changing multi-platform build targets
- Altering CI/CD workflow significantly

### Common Pitfalls to Avoid

1. **Don't run as root:** Always preserve `APT_CACHER_NG_USER`
2. **Don't disable health checks:** Orchestrators depend on them
3. **Don't remove log aggregation:** It's a key feature
4. **Don't skip tests:** All 6 must pass
5. **Don't guess version numbers:** Always check VERSION file
6. **Don't hardcode versions in docs:** Use current VERSION value
7. **Don't push to Docker Hub:** Only GHCR.io is supported

---

## Additional Resources

- **Apt-Cacher NG Official Docs:** https://www.unix-ag.uni-kl.de/~bloch/acng/
- **Ubuntu Jammy Tags:** https://hub.docker.com/_/ubuntu/tags?name=jammy
- **GitHub Container Registry:** https://github.com/users/mountaintopsolutions/packages/container/package/apt-cacher-ng
- **Original Project:** https://github.com/sameersbn/docker-apt-cacher-ng
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

## Changelog

- **2025-11-14:** Initial CLAUDE.md creation based on repository analysis
- Updates to this file should be committed with `docs:` prefix

---

## Quick Reference

### Key Commands

```bash
# Build
make

# Test locally
docker compose up -d

# Check logs
docker compose logs -f

# Run integration test
./.github/workflows/build.yml  # Use GitHub Actions

# Create release
echo "v3.7.4-YYYYMMDD" > VERSION
./scripts/tag-and-release.sh

# Generate release notes
./scripts/release-notes.sh v3.7.4-YYYYMMDD
```

### Key Files Summary

| File | Purpose | Modify Carefully? |
|------|---------|-------------------|
| `entrypoint.sh` | Runtime initialization | ⚠️ YES - Test all 6 tests |
| `Dockerfile` | Image definition | ⚠️ YES - Security implications |
| `VERSION` | Version source of truth | ✓ Update for releases |
| `.github/workflows/build.yml` | CI/CD pipeline | ⚠️ YES - Breaks automation |
| `README.md` | User documentation | ✓ Keep in sync with VERSION |
| `Makefile` | Build helper | ✓ Simple wrapper |
| `docker-compose.yml` | Local deployment | ✓ Example file |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APT_CACHER_NG_CACHE_DIR` | `/var/cache/apt-cacher-ng` | Package cache |
| `APT_CACHER_NG_LOG_DIR` | `/var/log/apt-cacher-ng` | Log files |
| `APT_CACHER_NG_CONFIG_DIR` | `/etc/apt-cacher-ng/user-config` | User config |
| `APT_CACHER_NG_USER` | `apt-cacher-ng` | Runtime user |

---

**Last Updated:** 2025-11-14
**For Questions:** Open an issue at https://github.com/mountaintopsolutions/docker-apt-cacher-ng
