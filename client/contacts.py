"""contacts: a user's address book of internal and external accounts."""

import httpx

from client.base import BaseClient
from client.models import Auth, User


class ContactsClient(BaseClient):
    """Client for contacts."""

    def get_contacts(self, user: str | User, token: Auth = None) -> httpx.Response:
        """GET /contacts/{username}.

        Args:
            user: Username, or a ``User`` (uses their username and token).
            token: Overrides the token - pass another user's to test 401.

        Returns:
            200 with ``[{label, account_num, routing_num, is_external}]``; 401 for another user.
        """
        username, token = self.resolve(user, token, "username")
        return self.request("GET", f"/contacts/{username}", token)

    def add_contact(  # noqa: PLR0913 - mirrors the endpoint's JSON body
        self,
        user: str | User,
        label: str,
        account_num: str,
        routing_num: str,
        *,
        is_external: bool = False,
        token: Auth = None,
    ) -> httpx.Response:
        """POST /contacts/{username}.

        Args:
            user: Owner of the address book: username, or a ``User`` (uses their token too).
            label: 1-30 chars, letters/digits/spaces, must not start with a space.
            account_num: 10 digits.
            routing_num: 9 digits. External contacts must not use the local routing number.
            is_external: True for an account in another bank.
            token: Overrides the token - pass another user's to test 401.

        Returns:
            201 added; 400 validation error; 401 bad token / another user; 409 duplicate label.
        """
        username, token = self.resolve(user, token, "username")
        body = {
            "label": label,
            "account_num": account_num,
            "routing_num": routing_num,
            "is_external": is_external,
        }
        return self.request("POST", f"/contacts/{username}", token, json=body)
