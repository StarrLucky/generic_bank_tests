RUFF := $(shell command -v ruff || echo .venv/bin/ruff)

.PHONY: lint fmt test hooks

lint:
	$(RUFF) check .
	$(RUFF) format --check .

fmt:
	$(RUFF) check --fix .
	$(RUFF) format .

test:
	.venv/bin/pytest

hooks:
	git config core.hooksPath .githooks
