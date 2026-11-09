"""Smoke: is everything reachable? Run this first. The real tests are yours to write (see TASKS.md)."""

import httpx
import pytest

from tests import config

SERVICES = {
    "frontend": config.FRONTEND_URL,
    "userservice": config.USERSERVICE_URL,
    "contacts": config.CONTACTS_URL,
    "ledgerwriter": config.LEDGERWRITER_URL,
    "balancereader": config.BALANCEREADER_URL,
    "transactionhistory": config.HISTORY_URL,
}


@pytest.mark.parametrize("name", SERVICES)
def test_service_is_ready(name):
    try:
        resp = httpx.get(f"{SERVICES[name]}/ready", timeout=5)
    except httpx.ConnectError:
        pytest.fail(f"{name} unreachable at {SERVICES[name]}: is ./scripts/port-forward.sh running?")
    assert resp.status_code == 200
