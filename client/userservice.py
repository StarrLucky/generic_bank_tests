"""userservice: signup and login. Issues RS256 JWTs that every other service verifies."""

import httpx

from client.base import BaseClient

# Fields userservice requires on signup (see __validate_new_user in userservice.py).
SIGNUP_FIELDS = (
    "username",
    "password",
    "password-repeat",
    "firstname",
    "lastname",
    "birthday",
    "timezone",
    "address",
    "state",
    "zip",
    "ssn",
)


def signup_form(username: str, password: str, **overrides: str) -> dict[str, str]:
    """Build a valid signup form; override any field to make it invalid.

    Args:
        username: 2-15 chars of ``[a-zA-Z0-9_]``.
        password: Also used for ``password-repeat`` unless overridden.
        **overrides: Field values to replace, e.g. ``zip=""``. Use ``**{"password-repeat": "x"}``
            for the hyphenated field.

    Returns:
        Form data ready for ``UserServiceClient.create_user``.
    """
    form = {
        "username": username,
        "password": password,
        "password-repeat": password,
        "firstname": "Qa",
        "lastname": "Robot",
        "birthday": "1990-01-01",
        "timezone": "GMT+1",
        "address": "1 Test St",
        "state": "CA",
        "zip": "94000",
        "ssn": "000-00-0000",
    }
    form.update(overrides)
    return form


class UserServiceClient(BaseClient):
    """Client for userservice (accounts-db)."""

    def create_user(self, form: dict[str, str]) -> httpx.Response:
        """POST /users (form-encoded).

        Returns:
            201 created, 400 validation error, 409 username taken.
        """
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
