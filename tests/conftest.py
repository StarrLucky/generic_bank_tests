from collections.abc import Callable, Iterator

import pytest

from client import BankApi, User
from tests import helpers


@pytest.fixture(scope="session")
def bank() -> Iterator[BankApi]:
    with BankApi() as api:
        yield api


@pytest.fixture
def make_user(bank: BankApi) -> Callable[..., User]:
    return bank.new_user


@pytest.fixture
def funded_user(bank: BankApi) -> User:
    user = bank.new_user()
    bank.ledger.deposit(user, 10_000).raise_for_status()
    helpers.wait_until(lambda: bank.balances.balance_cents(user), lambda b: b == 10_000)
    return user
