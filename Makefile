.PHONY: up down logs test test-backend test-frontend

up: ## Build and start the whole stack (frontend :3000, backend :8000)
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example - add real keys to LLM_API_KEYS")
	docker compose up --build -d
	@echo "Frontend: http://localhost:3000   Backend: http://localhost:8000/health"

down: ## Stop the stack (the named volume with the SQLite file is kept)
	docker compose down

logs:
	docker compose logs -f

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -q

test-frontend:
	cd frontend && npm test
