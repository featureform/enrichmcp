.PHONY: setup format lint test examples-test build clean docs docs-format install dev venv ci-setup ci-lint ci-test

# Local development (uses uv)
VENV_PYTHON = .venv/bin/python
VENV_ACTIVATE = source .venv/bin/activate

# CI/Production (uses system python)
PYTHON ?= python

# Detect if we're in CI
ifdef CI
    PYTHON_CMD = $(PYTHON)
else
    PYTHON_CMD = $(VENV_PYTHON)
endif

# Local development commands
setup: venv
	uv pip sync uv.lock -p $(VENV_PYTHON)
	uv pip install -p $(VENV_PYTHON) -e .[dev]
	$(VENV_PYTHON) -m pre_commit install
	@echo "Setup complete!"
	@echo "Your virtual environment is ready at .venv/"
	@echo "You can activate it with: $(VENV_ACTIVATE)"

venv:
	uv venv .venv
	@echo "Virtual environment created at .venv/"
	@echo "Activate with: $(VENV_ACTIVATE)"

format: docs-format
	$(PYTHON_CMD) -m ruff format .

docs-format:
	$(PYTHON_CMD) scripts/format_docs.py

lint:
	$(PYTHON_CMD) -m ruff check --fix .
	$(PYTHON_CMD) -m pyright

lint-check:
	$(PYTHON_CMD) -m ruff check .
	$(PYTHON_CMD) -m pyright

test:
	$(PYTHON_CMD) -m pytest --cov-report=term --cov-report=html --cov=src/enrichmcp

# Run only example tests
examples-test:
	$(PYTHON_CMD) -m pytest -o addopts='' -p no:cov tests/test_examples.py -m examples

build:
	$(PYTHON_CMD) -m build --no-isolation

# CI-specific commands (explicit, no guessing)
ci-setup:
	uv pip sync uv.lock --system --break-system-packages
	uv pip install --system --break-system-packages -e .[dev]

ci-lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pyright

ci-test:
	$(PYTHON) -m pytest -o addopts="" --cov=src/enrichmcp --cov-report=term --cov-report=xml --cov-report=html -m 'not examples'
	$(PYTHON) -m pytest -o addopts="" --cov=src/enrichmcp --cov-append --cov-report=xml --cov-report=html tests/test_examples.py -m examples

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__ htmlcov/ .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

docs:
	$(PYTHON_CMD) -m mkdocs serve

docs-build:
	$(PYTHON_CMD) -m mkdocs build

install:
	$(PYTHON_CMD) -m pip install .

dev:
	$(PYTHON_CMD) -m pip install -e .

.DEFAULT_GOAL := help
help:
	@echo "Available commands:"
	@echo "Local development:"
	@echo "  setup       - Create uv env and install dependencies and pre-commit hooks"
	@echo "  venv        - Create a project-specific uv virtual environment"
	@echo "  format      - Format code with ruff and docs with docs-format"
	@echo "  docs-format - Format Python code blocks in markdown files"
	@echo "  lint        - Run linters (ruff, pyright) with auto-fixing"
	@echo "  lint-check  - Run linters in check-only mode (no fixes)"
	@echo "  test        - Run tests with pytest"
	@echo "  examples-test - Run example smoke tests"
	@echo "  build       - Build the package"
	@echo "  clean       - Remove build artifacts"
	@echo "  docs        - Serve documentation locally"
	@echo "  docs-build  - Build documentation for production"
	@echo "  install     - Install the package"
	@echo "  dev         - Install the package in development mode"
	@echo "CI/Production:"
	@echo "  ci-setup    - Install dependencies (system python)"
	@echo "  ci-lint     - Run linters (system python)"
	@echo "  ci-test     - Run tests (system python)"
