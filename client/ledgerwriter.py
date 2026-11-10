"""ledgerwriter: the only service that writes money movements to ledger-db."""

import uuid

import httpx

from client.base import BaseClient


class LedgerWriterClient(BaseClient):
    """Client for ledgerwriter.

    Amounts are integers in cents. ``request_uuid`` is the idempotency key: ledgerwriter
    rejects a second request with the same uuid ("duplicate transaction uuid").
    """

    def post_transaction(  # noqa: PLR0913 - mirrors the endpoint's JSON body
        self,
        token: str | None,
        *,
        from_account: str,
        from_routing: str,
        to_account: str,
        to_routing: str,
        amount_cents: int,
        request_uuid: str | None = None,
    ) -> httpx.Response:
        """POST /transactions.

        Args:
            token: Sender's JWT. For internal transfers ``from_account`` must equal its ``acct`` claim.
            from_account: 10-digit account number.
            from_routing: 9-digit routing number. Not the local one means "money from another bank":
                no balance check is done on the sender.
            to_account: 10-digit account number.
            to_routing: 9-digit routing number.
            amount_cents: Integer amount in cents, must be > 0.
            request_uuid: Idempotency key; a random uuid4 when omitted.

        Returns:
            201 written; 400 with a reason in the body (insufficient balance, invalid amount,
            can't send to self, sender not authenticated, invalid account details,
            duplicate transaction uuid); 401 bad token; 500 balancereader unavailable.
        """
        body = {
            "fromAccountNum": from_account,
            "fromRoutingNum": from_routing,
            "toAccountNum": to_account,
            "toRoutingNum": to_routing,
            "amount": amount_cents,
            "uuid": request_uuid or str(uuid.uuid4()),
        }
        return self.request("POST", "/transactions", token, json=body)
