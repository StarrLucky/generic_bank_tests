"""transactionhistory: recent transactions per account, read from ledger-db (eventually consistent)."""

import httpx

from client.base import BaseClient
from client.models import Auth, User


class TransactionHistoryClient(BaseClient):
    """Client for transactionhistory."""

    def get_history(self, account: str | User, token: Auth = None) -> httpx.Response:
        """GET /transactions/{account}.

        Args:
            account: Account number, or a ``User`` (uses their account and token).
            token: Overrides the token - pass another user's to test 401.

        Returns:
            200 with a list of ``{transactionId, fromAccountNum, fromRoutingNum, toAccountNum,
            toRoutingNum, amount, timestamp}``, newest first; 401 for another account's history.
        """
        account, token = self.resolve(account, token, "account")
        return self.request("GET", f"/transactions/{account}", token)
