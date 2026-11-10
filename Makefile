RUFF := $(shell command -v ruff || echo .venv/bin/ruff)
SECRETS := $(shell command -v detect-secrets-hook || echo .venv/bin/detect-secrets-hook)
RUFF_OUTPUT_FORMAT ?= concise
export RUFF_OUTPUT_FORMAT

.PHONY: check lint lint_fix fmt secrets secrets-baseline test hooks

check: lint secrets

lint:
	$(RUFF) check .
	$(RUFF) format --check .

secrets:
	git ls-files -z | xargs -0 $(SECRETS) --baseline .secrets.baseline  # pragma: allowlist secret

secrets-baseline:
	detect-secrets scan --baseline .secrets.baseline --exclude-files '^\.venv/'  # pragma: allowlist secret

lint_fix:
	$(RUFF) check --fix --unsafe-fixes --exit-zero .
	$(RUFF) format .

fmt: lint_fix

test:
	.venv/bin/pytest

hooks:
	git config core.hooksPath .githooks
