"""transactionhistory: recent transactions per account, read from ledger-db (eventually consistent)."""

import httpx

from client.base import BaseClient


class TransactionHistoryClient(BaseClient):
    """Client for transactionhistory."""

    def get_history(self, token: str | None, account: str) -> httpx.Response:
        """GET /transactions/{account}.

        Returns:
            200 with a list of ``{transactionId, fromAccountNum, fromRoutingNum, toAccountNum,
            toRoutingNum, amount, timestamp}``, newest first; 401 for another account's history.
        """
        return self.request("GET", f"/transactions/{account}", token)
