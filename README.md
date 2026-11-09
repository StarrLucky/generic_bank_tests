# Bank of Anthos — QA Autotests

[![lint](https://github.com/StarrLucky/generic_bank_tests/actions/workflows/lint.yml/badge.svg)](https://github.com/StarrLucky/generic_bank_tests/actions/workflows/lint.yml)
![python](https://img.shields.io/badge/python-3.13-blue)
![pytest](https://img.shields.io/badge/pytest-8.3-0A9EDC)
![playwright](https://img.shields.io/badge/playwright-chromium-2EAD33)
![ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64)

Autotests (pytest + Playwright) for [Bank of Anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos),
Google Cloud's microservice demo bank: API integration tests, component tests with mocked
backends, chaos tests via WireMock, and UI tests.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium

./scripts/port-forward.sh      # separate terminal, keep it open
make test                      # or: .venv/bin/pytest tests/test_smoke.py
```

Demo user — `testuser` / `bankofanthos`, local routing number — `883745000`.

## Services

`./scripts/port-forward.sh` forwards them all to localhost and restarts a forward if its pod dies.

| Port | Service | What it does |
|---|---|---|
| 8080 | frontend | Flask, HTML pages, calls the backends server-side |
| 8081 | userservice | `POST /users` (form), `GET /login?username=&password=` → `{"token"}` |
| 8082 | contacts | `GET/POST /contacts/<username>` (JSON, Bearer required) |
| 8083 | ledgerwriter | `POST /transactions` (JSON, Bearer) → 201 |
| 8084 | balancereader | `GET /balances/<account>` → amount in **cents** |
| 8085 | transactionhistory | `GET /transactions/<account>` → list |
| 8086 | wiremock | admin API, only when installed (`./scripts/wiremock.sh install`) |

## Layout

```
tests/
  config.py          service URLs and demo data, every value overridable via env
  test_smoke.py      checks the cluster is up and reachable
  api/               backend integration tests
  component/         Flask frontend inside pytest, backends mocked with `responses`
  chaos/             one live service swapped for WireMock
  ui/                Playwright, page objects
scripts/
  port-forward.sh    forwards every service to localhost
```

## Commands

| Command | What it does |
|---|---|
| `make check` | everything CI runs: lint + secret scan |
| `make test` | run pytest |
| `make lint` | `ruff check` + `ruff format --check` |
| `make secrets` | scan tracked files for committed secrets |
| `make secrets-baseline` | refresh `.secrets.baseline` after triaging findings |
| `make fmt` | autofix and format |
| `make hooks` | enable the pre-commit hook (`core.hooksPath .githooks`) |

Run by marker: `.venv/bin/pytest -m chaos`. Playwright traces:
`.venv/bin/pytest --tracing retain-on-failure`, then `playwright show-trace`.

## Code quality

Linter is [ruff](https://docs.astral.sh/ruff/), configured in `ruff.toml` (line-length 120,
strict rule set: pytest-style, bandit, annotations, docstrings, pathlib). Secret scanning is
[detect-secrets](https://github.com/Yelp/detect-secrets) against `.secrets.baseline`; mark a false
positive with a trailing `# pragma: allowlist secret`, or re-run `make secrets-baseline`.
Both run via `make check` and are enforced in three places:

- locally — `make check`
- on commit — the `.githooks/pre-commit` hook (one-time setup: `make hooks`)
- in CI — GitHub Actions on every PR into `main`

## Tasks

The tests are written from scratch — the task list, with hints and pitfalls, is in [TASKS.md](TASKS.md).
