.PHONY: help install dev-install format lint test clean run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	poetry install --only=main

dev-install: ## Install all dependencies including dev tools
	poetry install
	poetry run pre-commit install

format: ## Format code with black and isort
	poetry run black src/ tests/
	poetry run isort src/ tests/

lint: ## Run linting tools
	poetry run flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	poetry run mypy src/

test: ## Run tests
	poetry run pytest -v

test-watch: ## Run tests in watch mode
	poetry run pytest-watch -- -v --cov=src/

clean: ## Clean up cache files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete

run: ## Run the bot locally
	poetry run python -m src.weeklyroulette_bot.main

dev: ## Run with auto-reload (for development)
	poetry run watchmedo auto-restart --patterns="*.py" --recursive -- python -m src.weeklyroulette_bot.main

shell: ## Activate Poetry environment (Poetry 2.0+ compatible)
	@echo "Poetry 2.0+ doesn't have 'shell' command."
	@echo "Use: poetry run <command>"
	@echo "Or activate manually with:"
	@echo "source $(poetry env info --path)/bin/activate"

setup-db: ## Initialize database
	poetry run python -c "from src.weeklyroulette_bot.database.connection import init_database; init_database()"

check: format lint test ## Run all checks (format, lint, test)

deploy-check: ## Pre-deployment checks
	@echo "Running pre-deployment checks..."
	make check
	@echo "✅ All checks passed! Ready to deploy."

# Docker commands (optional)
docker-build: ## Build Docker image
	docker build -t weeklyroulette-bot .

docker-run: ## Run Docker container
	docker run --env-file .env weeklyroulette-bot

# Environment management
env-setup: ## Setup environment file
	cp .env.example .env
	@echo "📝 Edit .env file with your Slack tokens"

deps-update: ## Update dependencies
	poetry update
	poetry export -f requirements.txt --output requirements.txt --without-hashes
