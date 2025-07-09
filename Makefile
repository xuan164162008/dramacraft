.PHONY: help install install-dev test test-cov lint format type-check clean build publish docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install the package with development dependencies
	pip install -e ".[dev,test,docs]"

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=video_mcp --cov-report=html --cov-report=term-missing

test-unit:  ## Run unit tests only
	pytest -m unit

test-integration:  ## Run integration tests only
	pytest -m integration

lint:  ## Run linting
	ruff check src/ tests/

format:  ## Format code
	black src/ tests/
	isort src/ tests/

type-check:  ## Run type checking
	mypy src/

quality:  ## Run all quality checks
	make format
	make lint
	make type-check

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	python -m build

publish:  ## Publish to PyPI
	python -m twine upload dist/*

publish-test:  ## Publish to Test PyPI
	python -m twine upload --repository testpypi dist/*

docs:  ## Build documentation
	mkdocs build

docs-serve:  ## Serve documentation locally
	mkdocs serve

pre-commit:  ## Install pre-commit hooks
	pre-commit install

setup:  ## Setup development environment
	make install-dev
	make pre-commit
