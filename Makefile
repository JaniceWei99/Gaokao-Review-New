.PHONY: dev test test-unit test-cov migrate migrate-new seed lint format docker-up docker-down

# === Development ===
dev:
	cd server && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# === Testing ===
test:
	cd server && python -m pytest tests/ -v --tb=short

test-unit:
	cd server && python -m pytest tests/unit/ -v

test-cov:
	cd server && python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# === Database ===
migrate:
	cd server && alembic upgrade head

migrate-new:
	cd server && alembic revision --autogenerate -m "$(msg)"

migrate-down:
	cd server && alembic downgrade -1

seed:
	cd server && python seed.py

# === Code Quality ===
lint:
	cd server && ruff check app/ tests/ && ruff format --check app/ tests/

format:
	cd server && ruff format app/ tests/

typecheck:
	cd server && mypy app/ --ignore-missing-imports

# === Docker ===
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-reset:
	docker-compose down -v && docker-compose up -d

# === Shortcuts ===
setup: docker-up
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed
	@echo "Setup complete! Run 'make dev' to start the server."

fresh: docker-reset
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed
	@echo "Fresh setup complete!"
