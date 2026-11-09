# Задания: Bank of Anthos QA

Тесты пишешь сам. Ветка `solutions` — мои варианты: открывай, только если застрял (`git diff main solutions -- tests/api`).

## 0. Подготовка

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
./scripts/port-forward.sh          # отдельное окно терминала, держать открытым
.venv/bin/pytest tests/test_smoke.py
```

| Порт | Сервис | Что делает |
|---|---|---|
| 8080 | frontend | Flask, HTML-страницы, ходит в бэкенды со своей стороны |
| 8081 | userservice | `POST /users` (form), `GET /login?username=&password=` → `{"token"}` |
| 8082 | contacts | `GET/POST /contacts/<username>` (JSON, нужен Bearer) |
| 8083 | ledgerwriter | `POST /transactions` (JSON, Bearer) → 201 |
| 8084 | balancereader | `GET /balances/<account>` → число в **центах** |
| 8085 | transactionhistory | `GET /transactions/<account>` → список |

Исходники для подсказок: `../bank-of-anthos/src/`. Демо-юзер: `testuser` / `bankofanthos`, local routing `883745000`.

Смотреть, что происходит внутри, пока тест бежит:
```bash
kubectl logs -f deploy/ledgerwriter
```

---

## 1. Фундамент (сделай до остального)

1. **API-клиент.** Класс с методами на каждый эндпоинт, возвращает сырой `httpx.Response`. Почему сырой, а не `.json()` — подумай.
2. **Фикстуры в `conftest.py`:** `api` (scope=session), `demo_user`, фабрика `make_user` (каждый вызов — новый юзер с уникальным именем), `funded_user` (новый юзер + депозит $100).
   - Подсказка: деньги новому юзеру можно завести только «из другого банка» — `fromRoutingNum` ≠ local, тогда ledgerwriter не проверяет баланс отправителя.
   - Ловушка: если `funded_user` построен поверх `new_user`, то в тесте с обоими это **один и тот же** юзер.
3. **Хелпер `wait_until(probe, condition, timeout)`.** Без него тесты будут флаки — см. задание 2.4.

## 2. API-интеграционные (`tests/api/`)

**Auth**
- 2.1 Логин отдаёт JWT. Проверь алгоритм (header), claims `user`, `acct`, `exp > iat`.
- 2.2 Неверный пароль, несуществующий юзер — какие коды? Сначала угадай, потом проверь в `userservice.py`.
- 2.3 Регистрация: дубликат, валидация username (параметризуй: короткий, длинный, пробел, спецсимволы), пароли не совпадают, пустое поле.
- 2.5 Чужой токен: запроси баланс чужого счёта. Подделай токен (поменяй `acct` в payload, подпись оставь старую).

**Переводы — главное по домену**
- 2.4 Депозит → баланс вырос. Запусти без `wait_until` 10 раз (`pytest --count` или цикл). Почему иногда падает? (`balancereader` читает базу по таймеру — eventual consistency.)
- 2.6 Перевод A→B: баланс A уменьшился, B вырос **ровно** на сумму, транзакция видна в истории обоих.
- 2.7 **Идемпотентность:** тот же `uuid` дважды. Что вернётся? Сколько денег списалось? Почему это критично для банка (ретраи сети)?
- 2.8 Недостаточно средств; перевод ровно всего баланса; на 1 цент больше баланса.
- 2.9 Сумма 0, отрицательная. Перевод самому себе. Списание с чужого счёта своим токеном.
- 2.10 Битые номера счёта/routing (длина, буквы) — параметризуй.
- 2.11 ⭐ Гонка: два параллельных перевода по $60 с баланса $100 (`ThreadPoolExecutor`). Сколько пройдёт? Какой итоговый баланс? Если уйдёт в минус — ты нашёл реальный баг (check-then-write без блокировки). Объясни по коду `LedgerWriterController`.

**Contacts**
- 2.12 Добавить внутренний и внешний контакт, дубликат лейбла, валидация, чужие контакты.

## 3. Компонентные тесты фронта с моками (`tests/component/`)

Поднимаешь Flask-фронт **прямо в pytest** без кластера, а все его HTTP-вызовы в бэкенды мокаешь библиотекой `responses`.

- 3.1 Фикстура `app`: добавь `../bank-of-anthos/src/frontend` в `sys.path`, выставь env (`*_API_ADDR`, `PUB_KEY_PATH`, `LOCAL_ROUTING_NUM`, `ENABLE_TRACING=false`), вызови `create_app()`.
  - Сгенерируй свою пару RSA-ключей (`cryptography`), публичный положи в файл для `PUB_KEY_PATH`, приватным подписывай токены сам — так ты управляешь «кто залогинен».
- 3.2 `/home`: замокай balances/history/contacts, проверь, что сумма `12345` центов рендерится как `$123.45`, отрицательная — с минусом.
- 3.3 balancereader вернул 500 → на странице `$---`, страница не упала.
- 3.4 `POST /payment` с суммой `"10.10"`: через `responses.calls` проверь, что в ledgerwriter ушло `amount: 1010` (int). Попробуй `"0.1"`, `"1e2"`, `"abc"`, `"10.999"` — что уходит? Есть ли баг с округлением?
- 3.5 ledgerwriter ответил 400 `insufficient balance` → редирект на `/home?msg=Payment failed: insufficient balance`.
- 3.6 Таймаут бэкенда (`responses` умеет кидать исключение как `body`).

## 4. Хаос: подмена одного живого сервиса на WireMock (`tests/chaos/`)

Цель: весь кластер настоящий, кроме одного сервиса, которым ты управляешь из теста.

- 4.1 Задеплой `wiremock/wiremock` в кластер (Deployment + Service, порт 8080). Образ multi-arch, на arm64 пойдёт нативно.
- 4.2 Сделай в WireMock маппинг с низким приоритетом: проксировать всё в `http://balancereader:8080` (`proxyBaseUrl`). Теперь WireMock прозрачен.
- 4.3 Переключи фронт: `kubectl set env deploy/frontend BALANCES_API_ADDR=wiremock:8080`. Проверь, что UI работает как раньше.
- 4.4 Фикстура: перед тестом `POST /__admin/mappings` (порт 8086), после — `POST /__admin/reset`. Тесты: баланс 500, задержка 10с (`fixedDelayMilliseconds`) при `BACKEND_TIMEOUT=4`, странный ответ (строка вместо числа).
- 4.5 Через `GET /__admin/requests` проверь, какие запросы реально пришли от фронта (заголовок Authorization есть?).
- Вопрос: ledgerwriter тоже ходит в balancereader перед списанием. Влияет ли на него твоя подмена? Почему?

## 5. Playwright UI (`tests/ui/`)

- 5.1 Page Objects: `LoginPage`, `HomePage` (селекторы: `#login-username`, `#current-balance`, `#transaction-list`, модалки `#sendPayment`, `#depositFunds`).
- 5.2 Логин демо-юзером → видна Home, имя в шапке. Логаут.
- 5.3 Регистрация через UI → попал на Home с балансом `$0.00`.
- 5.4 Пополнение с нового внешнего счёта → сообщение `Deposit successful`, баланс вырос, строка в истории.
- 5.5 Перевод новому получателю → контакт появился в выпадающем списке.
- 5.6 Ошибки: перевод больше баланса (что делает HTML-атрибут `max` и как его обойти, чтобы проверить бэкенд?), неверный пароль.
- 5.7 Фикстура `logged_in_page`: логинься через API (`/login` → cookie `token`) и ставь cookie в `context.add_cookies` — тест не тратит время на UI-логин.
- 5.8 `page.route()`: замокай `POST /payment` так, чтобы вернулся редирект с ошибкой. Почему этим **нельзя** подменить ответ balancereader? (подсказка: кто ходит в бэкенд — браузер или Flask?)
- 5.9 Включи трейсы: `pytest --tracing retain-on-failure`, открой `playwright show-trace`.

## 6. Бонус
- Маркеры `api`/`ui`/`chaos`, запуск по маркеру.
- `pytest-xdist` — параллельный прогон. Что сломается, если фикстуры делят юзеров?
- Allure-отчёт.
- GitHub Actions: kind в CI + прогон.
