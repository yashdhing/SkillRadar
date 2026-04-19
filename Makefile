PYTHON ?= python3
BACKEND_VENV := backend/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python
BACKEND_PIP := $(BACKEND_VENV)/bin/pip

.PHONY: backend-install backend-dev backend-test backend-lint frontend-dev frontend-build frontend-lint frontend-typecheck

backend-install:
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PIP) install --upgrade pip
	$(BACKEND_PIP) install -e backend[dev]

backend-dev:
	$(BACKEND_VENV)/bin/uvicorn skillradar_api.main:app --app-dir backend/src --reload

backend-test:
	$(BACKEND_VENV)/bin/pytest backend/tests

backend-lint:
	$(BACKEND_VENV)/bin/ruff check backend

frontend-dev:
	npm run frontend:dev

frontend-build:
	npm run frontend:build

frontend-lint:
	npm run frontend:lint

frontend-typecheck:
	npm run frontend:typecheck

