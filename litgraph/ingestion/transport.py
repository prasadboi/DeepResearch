"""HTTP transport abstraction for provider clients.

The transport is injectable so construction tests run fully offline against a
fake. The default implementation uses the standard library (`urllib`) — no new
runtime dependency. URLs are redacted before they appear in any error or log so
secrets (API keys passed as query params) are never leaked.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

#: Strips the value of an ``api_key`` query parameter from a URL.
_API_KEY_RE = re.compile(r"(api_key=)[^&]*", re.IGNORECASE)


def redact(url: str) -> str:
    """Return ``url`` with any ``api_key`` query value masked."""
    return _API_KEY_RE.sub(r"\1REDACTED", url)


@dataclass(frozen=True)
class Response:
    """A minimal HTTP response."""

    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)


class TransportError(Exception):
    """Raised by a transport when the request fails below the HTTP layer."""


class Transport(Protocol):
    """Sends an HTTP request and returns a :class:`Response`.

    Implementations must not raise on non-2xx status codes (the client maps
    those to typed errors); they raise :class:`TransportError` only for
    network-level failures (timeouts, DNS, connection reset).
    """

    def fetch(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> Response: ...


class UrllibTransport:
    """Default stdlib-based transport."""

    def __init__(self, timeout_seconds: float) -> None:
        self._timeout = timeout_seconds

    def fetch(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None = None,
    ) -> Response:
        request = urllib.request.Request(
            url, data=body, headers=dict(headers), method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as resp:
                return Response(
                    status=resp.status,
                    body=resp.read(),
                    headers={k.lower(): v for k, v in resp.headers.items()},
                )
        except urllib.error.HTTPError as exc:
            # HTTP-level error: return it so the client maps status -> typed error.
            return Response(
                status=exc.code,
                body=exc.read(),
                headers={k.lower(): v for k, v in (exc.headers or {}).items()},
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransportError(redact(f"{method} {url}: {exc}")) from exc
