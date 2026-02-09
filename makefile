.PHONY: help build run test lint clean deps docker-build docker-run dev check

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Go binary
	go build -o build/weeklyroulette ./cmd/weeklyroulette

run: ## Run the bot locally
	go run ./cmd/weeklyroulette

test: ## Run tests
	go test -v -race ./...

lint: ## Run Go linter
	golangci-lint run

clean: ## Clean build artifacts
	rm -rf build/
	go clean -cache

deps: ## Download Go dependencies
	go mod download
	go mod tidy

docker-build: ## Build Docker image
	docker build -t weeklyroulette-bot .

docker-run: ## Run Docker container
	docker run --env-file .env weeklyroulette-bot

dev: ## Run with auto-reload (requires air)
	air -c .air.toml

check: lint test ## Run all checks (lint, test)

deploy-check: ## Pre-deployment checks
	@echo "Running pre-deployment checks..."
	make check
	@echo "✅ All checks passed! Ready to deploy."

env-setup: ## Setup environment file
	cp .env.example .env
	@echo "📝 Edit .env file with your Slack tokens"
