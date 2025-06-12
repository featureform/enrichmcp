# Contributing to enrichmcp

We love your input! We want to make contributing to enrichmcp as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Pull Requests

1. Update the README.md with details of changes to the interface, if appropriate
2. Update the CHANGELOG.md with details of any changes
3. The PR should work for Python 3.11 and above
4. Ensure all tests pass and code is properly formatted

## Development Setup

```bash
# Setup development environment (uses uv and uv.lock)
make setup

# Create a virtual environment manually (optional)
make venv
source .venv/bin/activate  # On Unix/macOS

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

## Code Standards

- All code must be formatted with Ruff
- All code must pass Pyright type checking
- All public functions, classes, and methods must have docstrings
- Tests should be provided for new functionality

## License

By contributing, you agree that your contributions will be licensed under the project's Apache 2.0 License.
