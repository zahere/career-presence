# Career Presence System - Makefile
# Common development tasks

.PHONY: help install install-dev install-all sync test lint format typecheck clean

# Default Python version
PYTHON := python3.11

# ═══════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════

help: ## Show this help
	@echo "Career Presence System - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ═══════════════════════════════════════════════════════════════════════════
# INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════

install: ## Install core dependencies with uv
	uv venv
	uv pip install -e .

install-dev: ## Install with dev dependencies
	uv venv
	uv pip install -e ".[dev]"

install-ai: ## Install with AI/LLM dependencies
	uv venv
	uv pip install -e ".[ai]"

install-all: ## Install all dependencies (core + ai + vectors + dev)
	uv venv
	uv pip install -e ".[all]"

sync: ## Sync dependencies from pyproject.toml
	uv pip sync

# ═══════════════════════════════════════════════════════════════════════════
# DEVELOPMENT
# ═══════════════════════════════════════════════════════════════════════════

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=scripts --cov-report=html

lint: ## Run linter (ruff)
	uv run ruff check scripts/ tests/

lint-fix: ## Run linter and fix issues
	uv run ruff check scripts/ tests/ --fix

format: ## Format code (ruff)
	uv run ruff format scripts/ tests/

typecheck: ## Run type checker (mypy)
	uv run mypy scripts/

check: lint typecheck test ## Run all checks (lint + typecheck + test)

# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

cli: ## Run CLI
	uv run cps

status: ## Show pipeline status
	uv run cps status

discover: ## Discover jobs (usage: make discover QUERY="AI Engineer remote")
	uv run cps discover "$(QUERY)"

# ═══════════════════════════════════════════════════════════════════════════
# BROWSER AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════

playwright-install: ## Install Playwright browsers
	uv run playwright install chromium

# ═══════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════

clean: ## Clean generated files
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf build/ dist/ *.egg-info/
	rm -rf htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean ## Clean everything including venv
	rm -rf .venv/

# ═══════════════════════════════════════════════════════════════════════════
# RESUME
# ═══════════════════════════════════════════════════════════════════════════

compile-resume: ## Compile master resume
	cd resume/base && pdflatex -interaction=nonstopmode master.tex && pdflatex -interaction=nonstopmode master.tex
