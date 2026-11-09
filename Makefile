RUFF := $(shell command -v ruff || echo .venv/bin/ruff)
SECRETS := $(shell command -v detect-secrets-hook || echo .venv/bin/detect-secrets-hook)

.PHONY: check lint secrets secrets-baseline fmt test hooks

check: lint secrets

lint:
	$(RUFF) check .
	$(RUFF) format --check .

secrets:
	git ls-files -z | xargs -0 $(SECRETS) --baseline .secrets.baseline  # pragma: allowlist secret

secrets-baseline:
	detect-secrets scan --baseline .secrets.baseline --exclude-files '^\.venv/'  # pragma: allowlist secret

fmt:
	$(RUFF) check --fix .
	$(RUFF) format .

test:
	.venv/bin/pytest

hooks:
	git config core.hooksPath .githooks
