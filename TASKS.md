# Tasks: Bank of Anthos QA

You write the tests yourself. The `solutions` branch holds my versions — open it only if you're
stuck (`git diff main solutions -- tests/api`).

## 0. Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
./scripts/port-forward.sh          # separate terminal, keep it open
.venv/bin/pytest tests/test_smoke.py
```

| Port | Service | What it does |
|---|---|---|
| 8080 | frontend | Flask, HTML pages, calls the backends server-side |
| 8081 | userservice | `POST /users` (form), `GET /login?username=&password=` → `{"token"}` |
| 8082 | contacts | `GET/POST /contacts/<username>` (JSON, Bearer required) |
| 8083 | ledgerwriter | `POST /transactions` (JSON, Bearer) → 201 |
| 8084 | balancereader | `GET /balances/<account>` → amount in **cents** |
| 8085 | transactionhistory | `GET /transactions/<account>` → list |

Sources to peek at when stuck: `../bank-of-anthos/src/`. Demo user: `testuser` / `bankofanthos`,
local routing number `883745000`.

Watch what happens inside while a test runs:
```bash
kubectl logs -f deploy/ledgerwriter
```

---

## 1. Foundation (do this before anything else)

1. **API client.** A class with a method per endpoint, returning the raw `httpx.Response`. Why raw
   and not `.json()` — think it through.
2. **Fixtures in `conftest.py`:** `api` (scope=session), `demo_user`, a `make_user` factory (every
   call creates a new user with a unique name), `funded_user` (new user + a $100 deposit).
   - Hint: the only way to fund a new user is "from another bank" — `fromRoutingNum` ≠ local, in
     which case ledgerwriter doesn't check the sender's balance.
   - Trap: if `funded_user` is built on top of `new_user`, then a test using both gets **the same**
     user twice.
3. **A `wait_until(probe, condition, timeout)` helper.** Without it the tests will be flaky — see
   task 2.4.

## 2. API integration tests (`tests/api/`)

**Auth**
- 2.1 Login returns a JWT. Check the algorithm (header) and the `user`, `acct`, `exp > iat` claims.
- 2.2 Wrong password, non-existent user — which status codes? Guess first, then check
  `userservice.py`.
- 2.3 Registration: duplicate, username validation (parametrize: too short, too long, space,
  special characters), passwords don't match, empty field.
- 2.5 Someone else's token: request another account's balance. Forge a token (change `acct` in the
  payload, leave the old signature).

**Transfers — the core of the domain**
- 2.4 Deposit → balance goes up. Run it 10 times without `wait_until` (`pytest --count` or a loop).
  Why does it sometimes fail? (`balancereader` polls the database on a timer — eventual
  consistency.)
- 2.6 Transfer A→B: A's balance goes down, B's goes up by **exactly** the amount, and the
  transaction shows up in both histories.
- 2.7 **Idempotency:** the same `uuid` twice. What comes back? How much money was debited? Why does
  this matter for a bank (network retries)?
- 2.8 Insufficient funds; a transfer of exactly the whole balance; one cent more than the balance.
- 2.9 Amount of 0, negative amount. Transfer to yourself. Debiting someone else's account with your
  own token.
- 2.10 Malformed account/routing numbers (length, letters) — parametrize.
- 2.11 ⭐ Race: two parallel $60 transfers out of a $100 balance (`ThreadPoolExecutor`). How many go
  through? What's the final balance? If it goes negative, you've found a real bug (check-then-write
  with no locking). Explain it from the `LedgerWriterController` code.

**Contacts**
- 2.12 Add an internal and an external contact, duplicate label, validation, other users' contacts.

## 3. Component tests of the frontend with mocks (`tests/component/`)

You run the Flask frontend **inside pytest** with no cluster, and mock all of its HTTP calls to the
backends with the `responses` library.

- 3.1 An `app` fixture: add `../bank-of-anthos/src/frontend` to `sys.path`, set the env vars
  (`*_API_ADDR`, `PUB_KEY_PATH`, `LOCAL_ROUTING_NUM`, `ENABLE_TRACING=false`), call `create_app()`.
  - Generate your own RSA key pair (`cryptography`), write the public key to the file for
    `PUB_KEY_PATH`, and sign tokens yourself with the private one — that's how you control "who is
    logged in".
- 3.2 `/home`: mock balances/history/contacts, check that `12345` cents renders as `$123.45`, and
  that a negative amount renders with a minus sign.
- 3.3 balancereader returned 500 → the page shows `$---` and doesn't blow up.
- 3.4 `POST /payment` with an amount of `"10.10"`: via `responses.calls`, check that ledgerwriter
  received `amount: 1010` (int). Try `"0.1"`, `"1e2"`, `"abc"`, `"10.999"` — what gets sent? Is
  there a rounding bug?
- 3.5 ledgerwriter answered 400 `insufficient balance` → redirect to
  `/home?msg=Payment failed: insufficient balance`.
- 3.6 Backend timeout (`responses` can raise an exception as the `body`).

## 4. Chaos: swapping one live service for WireMock (`tests/chaos/`)

The goal: the whole cluster is real except for one service, which you drive from the test.

- 4.1 Deploy `wiremock/wiremock` into the cluster (Deployment + Service, port 8080). The image is
  multi-arch, so it runs natively on arm64.
- 4.2 Add a low-priority WireMock mapping that proxies everything to
  `http://balancereader:8080` (`proxyBaseUrl`). WireMock is now transparent.
- 4.3 Point the frontend at it: `kubectl set env deploy/frontend BALANCES_API_ADDR=wiremock:8080`.
  Check the UI still works as before.
- 4.4 A fixture: `POST /__admin/mappings` before the test (port 8086), `POST /__admin/reset` after.
  Tests: a balance of 500; a 10s delay (`fixedDelayMilliseconds`) against `BACKEND_TIMEOUT=4`; a
  weird response (a string instead of a number).
- 4.5 Use `GET /__admin/requests` to check which requests the frontend actually sent (is the
  Authorization header there?).
- Question: ledgerwriter also calls balancereader before debiting. Does your swap affect it? Why?

## 5. Playwright UI (`tests/ui/`)

- 5.1 Page objects: `LoginPage`, `HomePage` (selectors: `#login-username`, `#current-balance`,
  `#transaction-list`, the `#sendPayment` and `#depositFunds` modals).
- 5.2 Log in as the demo user → Home is visible, the name is in the header. Log out.
- 5.3 Register through the UI → you land on Home with a balance of `$0.00`.
- 5.4 Deposit from a new external account → a `Deposit successful` message, the balance goes up, a
  row appears in the history.
- 5.5 Transfer to a new recipient → the contact appears in the dropdown.
- 5.6 Errors: a transfer larger than the balance (what does the `max` HTML attribute do, and how do
  you get around it to test the backend?), wrong password.
- 5.7 A `logged_in_page` fixture: log in via the API (`/login` → `token` cookie) and set the cookie
  with `context.add_cookies` — the test doesn't waste time on a UI login.
- 5.8 `page.route()`: mock `POST /payment` so it returns a redirect with an error. Why can you
  **not** swap out the balancereader response this way? (hint: who calls the backend — the browser
  or Flask?)
- 5.9 Turn on traces: `pytest --tracing retain-on-failure`, open with `playwright show-trace`.

## 6. Bonus
- `api`/`ui`/`chaos` markers, running by marker.
- `pytest-xdist` — a parallel run. What breaks if fixtures share users?
- An Allure report.
- GitHub Actions: kind in CI plus a test run.
