"""Typed provider errors.

Provider failures surface as a small typed hierarchy so callers can branch on
failure mode without parsing strings. Messages must never contain secrets
(API keys are redacted before they reach here).
"""

from __future__ import annotations

from litgraph.schemas import Provider


class ProviderError(Exception):
    """Base class for all provider client failures."""

    def __init__(
        self,
        provider: Provider,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


class ProviderBadRequestError(ProviderError):
    """The request was malformed (HTTP 400)."""


class ProviderAuthError(ProviderError):
    """Authentication failed or is required (HTTP 401/403)."""


class ProviderNotFoundError(ProviderError):
    """The requested record does not exist (HTTP 404)."""


class ProviderRateLimitError(ProviderError):
    """The provider rate limit was exceeded (HTTP 429)."""


class ProviderTimeoutError(ProviderError):
    """The request timed out or the connection failed at the network layer."""


class ProviderResponseError(ProviderError):
    """Unexpected status (e.g. 5xx after retries) or an unparseable body."""


def error_for_status(
    provider: Provider, status: int, message: str
) -> ProviderError:
    """Map an HTTP status code to the matching typed error."""
    if status == 400:
        return ProviderBadRequestError(provider, message, status_code=status)
    if status in (401, 403):
        return ProviderAuthError(provider, message, status_code=status)
    if status == 404:
        return ProviderNotFoundError(provider, message, status_code=status)
    if status == 429:
        return ProviderRateLimitError(provider, message, status_code=status)
    return ProviderResponseError(provider, message, status_code=status)
