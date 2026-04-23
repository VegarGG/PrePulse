.PHONY: bootstrap dev backend frontend test lint clean

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

bootstrap:
	python3.11 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install
	@echo "bootstrap complete — run 'make dev' to start both servers"

backend:
	$(VENV)/bin/uvicorn backend.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend on :8000 and frontend on :3000 …"
	@$(MAKE) -j 2 backend frontend

test:
	$(VENV)/bin/pytest -q

lint:
	$(VENV)/bin/ruff check backend/ tests/
	cd frontend && npm run lint

clean:
	rm -rf $(VENV) frontend/node_modules frontend/.next __pycache__ .pytest_cache
