"""balancereader: current balance per account, computed from ledger-db.

It polls ledger-db on a timer, so a fresh transaction shows up after a delay (eventual consistency).
"""

import httpx

from client.base import BaseClient
from client.models import Auth, User


class BalanceReaderClient(BaseClient):
    """Client for balancereader."""

    def get_balance(self, account: str | User, token: Auth = None) -> httpx.Response:
        """GET /balances/{account}.

        Args:
            account: Account number, or a ``User`` (uses their account and token).
            token: Overrides the token - pass another user's to test 401.

        Returns:
            200 with a bare integer (cents); 401 when the token's ``acct`` claim is another account.
        """
        account, token = self.resolve(account, token, "account")
        return self.request("GET", f"/balances/{account}", token)

    def balance_cents(self, account: str | User, token: Auth = None) -> int:
        """The balance as an int, raising on any non-2xx status."""
        resp = self.get_balance(account, token)
        resp.raise_for_status()
        return int(resp.text)
