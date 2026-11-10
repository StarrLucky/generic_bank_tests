"""One object holding a client per service, configured from env vars."""

import os
from types import TracebackType
from typing import Self

from client.balancereader import BalanceReaderClient
from client.contacts import ContactsClient
from client.ledgerwriter import LedgerWriterClient
from client.models import User
from client.transactionhistory import TransactionHistoryClient
from client.userservice import DEFAULT_PASSWORD, UserServiceClient


class BankApi:
    """Facade: ``bank.users.login(...)``, ``bank.ledger.post_transaction(...)`` etc.

    Defaults match ``scripts/port-forward.sh``.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        """Create all service clients; override any URL with its env var."""
        self.users = UserServiceClient(os.getenv("USERSERVICE_URL", "http://localhost:8081"), timeout)
        self.contacts = ContactsClient(os.getenv("CONTACTS_URL", "http://localhost:8082"), timeout)
        self.ledger = LedgerWriterClient(os.getenv("LEDGERWRITER_URL", "http://localhost:8083"), timeout)
        self.balances = BalanceReaderClient(os.getenv("BALANCEREADER_URL", "http://localhost:8084"), timeout)
        self.history = TransactionHistoryClient(os.getenv("HISTORY_URL", "http://localhost:8085"), timeout)

    def new_user(self, username: str | None = None, password: str = DEFAULT_PASSWORD, **overrides: str) -> User:
        """Register a user and log them in - ``bank.users.register`` under a shorter name."""
        return self.users.register(username, password, **overrides)

    def close(self) -> None:
        """Close every client."""
        for client in (self.users, self.contacts, self.ledger, self.balances, self.history):
            client.close()

    def __enter__(self) -> Self:
        """Use as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close on exit."""
        self.close()
