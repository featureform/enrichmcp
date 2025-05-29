# GitHub Actions Workflows

This directory contains the automated workflows for enrichmcp.

## Workflows

### 1. `ci.yml` - Continuous Integration
- **Triggers**: On every push and pull request
- **Purpose**: Runs tests, linting, and type checking
- **Jobs**:
  - Run pytest
  - Run ruff linting
  - Run pyright type checking

### 2. `docs.yml` - Documentation
- **Triggers**: On push to main or manual trigger
- **Purpose**: Builds and deploys documentation to GitHub Pages
- **Note**: Currently configured but may need GitHub Pages setup

### 3. `release.yml` - PyPI Release
- **Triggers**: When you push a version tag (e.g., `v0.1.0`)
- **Purpose**: Builds and publishes the package to PyPI
- **Jobs**:
  1. Build the distribution packages
  2. Publish to PyPI (supports both trusted publishing and username/password)
  3. Create a GitHub release with changelog

### 4. `test-publish.yml` - Test PyPI Publishing
- **Triggers**: On pushes to main that modify source code
- **Purpose**: Tests the build and optionally publishes to TestPyPI
- **Jobs**:
  1. Build and test the package
  2. Publish to TestPyPI (only on main branch)

## Setup Instructions

### For PyPI Publishing (release.yml)

You have two options:

#### Option 1: Trusted Publishing (Recommended)
1. Go to https://pypi.org and log in
2. Go to your project page (after first manual upload)
3. Click "Manage" → "Publishing"
4. Add a new trusted publisher:
   - Owner: `featureform`
   - Repository: `enrichmcp`
   - Workflow: `release.yml`
   - Environment: `pypi`
5. In GitHub, go to Settings → Environments
6. Create an environment called `pypi`
7. Add a variable `USE_TRUSTED_PUBLISHING` with value `true`

#### Option 2: API Token (Classic Method)
1. Go to https://pypi.org and log in
2. Go to Account Settings → API tokens
3. Create a new token (scope to project after first upload)
4. In GitHub, go to Settings → Secrets and variables → Actions
5. Add secrets:
   - `PYPI_USERNAME`: `__token__`
   - `PYPI_PASSWORD`: Your PyPI API token

### For TestPyPI Publishing (test-publish.yml)

Similar to above but for test.pypi.org:
1. Create account at https://test.pypi.org
2. Set up trusted publishing for the `testpypi` environment
3. Or use API tokens

## How to Make a Release

1. Make sure you're on the main branch with all changes committed
2. Update `CHANGELOG.md` (change "Unreleased" to the version number)
3. Commit the changelog update
4. Tag the release:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin main
   git push origin v0.1.0
   ```
5. The `release.yml` workflow will automatically:
   - Build the package
   - Upload to PyPI
   - Create a GitHub release

## Manual Triggers

Some workflows support manual triggers via GitHub's UI:
1. Go to Actions tab
2. Select the workflow
3. Click "Run workflow"
4. Choose the branch and run

This is available for:
- `docs.yml` - To manually deploy docs
- `test-publish.yml` - To manually test publishing
