"""Provider ingestion clients (Stage 1, Task 1.1).

Read-only fetch clients that return *raw* provider records plus fetch metadata
behind a common :class:`~litgraph.ingestion.base.ProviderClient` interface. No
normalization, identity creation, deduplication, or persistence happens here.
"""

from litgraph.ingestion.base import FetchContext, ProviderClient
from litgraph.ingestion.errors import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from litgraph.ingestion.openalex import OpenAlexClient
from litgraph.ingestion.semantic_scholar import SemanticScholarClient

__all__ = [
    "FetchContext",
    "OpenAlexClient",
    "ProviderAuthError",
    "ProviderBadRequestError",
    "ProviderClient",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "SemanticScholarClient",
]
