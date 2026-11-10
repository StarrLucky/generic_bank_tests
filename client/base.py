"""Shared HTTP plumbing for all service clients."""

from types import TracebackType
from typing import Any, Self

import httpx


class BaseClient:
    """Thin wrapper over httpx.Client bound to one service.

    Methods of subclasses return the raw ``httpx.Response`` so tests decide what to assert:
    status code, body text or JSON.
    """

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        """Create a client.

        Args:
            base_url: Service root, e.g. ``http://localhost:8081``.
            timeout: Per-request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(base_url=self.base_url, timeout=timeout)

    @staticmethod
    def auth(token: str | None) -> dict[str, str]:
        """Build the Authorization header; empty when token is None (for negative tests)."""
        return {"Authorization": f"Bearer {token}"} if token else {}

    def request(self, method: str, path: str, token: str | None = None, **kwargs: Any) -> httpx.Response:
        """Send a request, adding the bearer token if given."""
        headers = {**self.auth(token), **kwargs.pop("headers", {})}
        return self.http.request(method, path, headers=headers, **kwargs)

    def ready(self) -> httpx.Response:
        """GET /ready: readiness probe every Bank of Anthos service exposes."""
        return self.http.get("/ready")

    def version(self) -> httpx.Response:
        """GET /version."""
        return self.http.get("/version")

    def close(self) -> None:
        """Close the underlying connection pool."""
        self.http.close()

    def __enter__(self) -> Self:
        """Use as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close on exit."""
        self.close()
