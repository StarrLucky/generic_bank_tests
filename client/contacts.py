"""contacts: a user's address book of internal and external accounts."""

import httpx

from client.base import BaseClient


class ContactsClient(BaseClient):
    """Client for contacts."""

    def get_contacts(self, token: str | None, username: str) -> httpx.Response:
        """GET /contacts/{username}.

        Returns:
            200 with ``[{label, account_num, routing_num, is_external}]``; 401 for another user.
        """
        return self.request("GET", f"/contacts/{username}", token)

    def add_contact(  # noqa: PLR0913 - mirrors the endpoint's JSON body
        self,
        token: str | None,
        username: str,
        label: str,
        account_num: str,
        routing_num: str,
        *,
        is_external: bool = False,
    ) -> httpx.Response:
        """POST /contacts/{username}.

        Args:
            token: Owner's JWT.
            username: Owner of the address book.
            label: 1-30 chars, letters/digits/spaces, must not start with a space.
            account_num: 10 digits.
            routing_num: 9 digits. External contacts must not use the local routing number.
            is_external: True for an account in another bank.

        Returns:
            201 added; 400 validation error; 401 bad token / another user; 409 duplicate label.
        """
        body = {
            "label": label,
            "account_num": account_num,
            "routing_num": routing_num,
            "is_external": is_external,
        }
        return self.request("POST", f"/contacts/{username}", token, json=body)
