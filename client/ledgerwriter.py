"""ledgerwriter: the only service that writes money movements to ledger-db."""

import os
import uuid

import httpx

from client.base import BaseClient
from client.models import Auth, User

# kubernetes-manifests/config.yaml
LOCAL_ROUTING_NUM = os.getenv("LOCAL_ROUTING_NUM", "883745000")

# "some other bank" - a deposit from here is not balance-checked
EXTERNAL_ROUTING_NUM = os.getenv("EXTERNAL_ROUTING_NUM", "111111111")
EXTERNAL_ACCOUNT_NUM = os.getenv("EXTERNAL_ACCOUNT_NUM", "9099791699")


class LedgerWriterClient(BaseClient):
    """Client for ledgerwriter.

    Amounts are integers in cents. ``request_uuid`` is the idempotency key: ledgerwriter
    rejects a second request with the same uuid ("duplicate transaction uuid").
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        local_routing: str = LOCAL_ROUTING_NUM,
    ) -> None:
        """Remember this bank's routing number so transfers only need the account."""
        super().__init__(base_url, timeout)
        self.local_routing = local_routing

    def post_transaction(  # noqa: PLR0913 - mirrors the endpoint's JSON body
        self,
        *,
        from_account: str,
        from_routing: str,
        to_account: str,
        to_routing: str,
        amount_cents: int,
        request_uuid: str | None = None,
        token: Auth = None,
    ) -> httpx.Response:
        """POST /transactions.

        Args:
            from_account: 10-digit account number.
            from_routing: 9-digit routing number. Not the local one means "money from another bank":
                no balance check is done on the sender.
            to_account: 10-digit account number.
            to_routing: 9-digit routing number.
            amount_cents: Integer amount in cents, must be > 0.
            request_uuid: Idempotency key; a random uuid4 when omitted.
            token: Sender's ``User`` or raw JWT. For internal transfers ``from_account`` must
                equal its ``acct`` claim.

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

    def transfer(  # noqa: PLR0913 - a transfer needs every part of the destination
        self,
        sender: User,
        to_account: str | User,
        amount_cents: int,
        *,
        to_routing: str | None = None,
        request_uuid: str | None = None,
        token: Auth = None,
    ) -> httpx.Response:
        """Move money out of ``sender``'s own account - the common internal transfer.

        Args:
            sender: Whose account is debited; their token is used unless ``token`` is given.
            to_account: Recipient account number, or a ``User``.
            amount_cents: Integer amount in cents.
            to_routing: Recipient's routing number; this bank's when omitted.
            request_uuid: Idempotency key; a random uuid4 when omitted.
            token: Overrides the sender's token - how you test debiting someone else's account.
        """
        recipient = to_account.account if isinstance(to_account, User) else to_account
        return self.post_transaction(
            from_account=sender.account,
            from_routing=self.local_routing,
            to_account=recipient,
            to_routing=to_routing or self.local_routing,
            amount_cents=amount_cents,
            request_uuid=request_uuid,
            token=token if token is not None else sender,
        )

    def deposit(
        self,
        user: User,
        amount_cents: int,
        *,
        from_account: str = EXTERNAL_ACCOUNT_NUM,
        from_routing: str = EXTERNAL_ROUTING_NUM,
        request_uuid: str | None = None,
    ) -> httpx.Response:
        """Fund ``user`` from another bank.

        The only way to give a fresh user money: with a non-local ``from_routing``
        ledgerwriter does not check the sender's balance.
        """
        return self.post_transaction(
            from_account=from_account,
            from_routing=from_routing,
            to_account=user.account,
            to_routing=self.local_routing,
            amount_cents=amount_cents,
            request_uuid=request_uuid,
            token=user,
        )
