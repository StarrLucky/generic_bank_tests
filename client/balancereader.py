"""balancereader: current balance per account, computed from ledger-db.

It polls ledger-db on a timer, so a fresh transaction shows up after a delay (eventual consistency).
"""

import httpx

from client.base import BaseClient


class BalanceReaderClient(BaseClient):
    """Client for balancereader."""

    def get_balance(self, token: str | None, account: str) -> httpx.Response:
        """GET /balances/{account}.

        Returns:
            200 with a bare integer (cents); 401 when the token's ``acct`` claim is another account.
        """
        return self.request("GET", f"/balances/{account}", token)
