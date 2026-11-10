"""userservice: signup and login. Issues RS256 JWTs that every other service verifies."""

import uuid

import httpx

from client.base import BaseClient
from client.models import User

DEFAULT_PASSWORD = "Qa-passw0rd"  # noqa: S105 - test data  # pragma: allowlist secret

# Everything userservice requires on signup except username/password
# (see __validate_new_user in userservice.py).
DEFAULT_PROFILE = {
    "firstname": "Qa",
    "lastname": "Robot",
    "birthday": "1990-01-01",
    "timezone": "GMT+1",
    "address": "1 Test St",
    "state": "CA",
    "zip": "94000",
    "ssn": "000-00-0000",  # pragma: allowlist secret
}


def random_username(prefix: str = "qa") -> str:
    """Return a unique username within userservice's 2-15 chars of ``[a-zA-Z0-9_]``."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def signup_form(
    username: str | None = None,
    password: str = DEFAULT_PASSWORD,
    password_repeat: str | None = None,
    **overrides: str,
) -> dict[str, str]:
    """Build a valid signup form; override any field to make it invalid.

    Args:
        username: 2-15 chars of ``[a-zA-Z0-9_]``; a unique one when omitted.
        password: Also used for ``password-repeat``.
        password_repeat: Set it to make the two passwords differ.
        **overrides: Any other field, e.g. ``zip=""``.

    Returns:
        Form data for ``POST /users``.
    """
    return {
        "username": username or random_username(),
        "password": password,
        "password-repeat": password if password_repeat is None else password_repeat,
        **DEFAULT_PROFILE,
        **overrides,
    }


class UserServiceClient(BaseClient):
    """Client for userservice (accounts-db)."""

    def create_user(
        self,
        username: str | None = None,
        password: str = DEFAULT_PASSWORD,
        password_repeat: str | None = None,
        **overrides: str,
    ) -> httpx.Response:
        """POST /users (form-encoded). Builds the form for you; override any field.

        Args:
            username: 2-15 chars of ``[a-zA-Z0-9_]``; a unique one when omitted.
            password: Also used for ``password-repeat``.
            password_repeat: Set it to make the two passwords differ.
            **overrides: Any other form field, e.g. ``zip=""`` or ``firstname=""``.

        Returns:
            201 created, 400 validation error, 409 username taken.
        """
        form = signup_form(username, password, password_repeat, **overrides)
        return self.create_user_form(form)

    def create_user_form(self, form: dict[str, str]) -> httpx.Response:
        """POST /users with an arbitrary body - for tests that drop or rename fields."""
        return self.http.post("/users", data=form)

    def login(self, username: str, password: str) -> httpx.Response:
        """GET /login?username=&password=.

        Returns:
            200 ``{"token": "<jwt>"}``, 401 wrong password, 404 unknown user.
        """
        return self.http.get("/login", params={"username": username, "password": password})

    def get_token(self, username: str, password: str) -> str:
        """Log in and return the JWT, raising on any non-2xx status."""
        resp = self.login(username, password)
        resp.raise_for_status()
        return resp.json()["token"]

    def register(
        self,
        username: str | None = None,
        password: str = DEFAULT_PASSWORD,
        **overrides: str,
    ) -> User:
        """Create a user, log in, and return it with its token and account number.

        The happy path for fixtures. Raises on any non-2xx status, so it never
        hands back a half-built user; use ``create_user`` for negative tests.
        """
        username = username or random_username()
        self.create_user(username, password, **overrides).raise_for_status()
        return User.from_token(username, password, self.get_token(username, password))
