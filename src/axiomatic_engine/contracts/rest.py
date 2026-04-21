from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class RestRequestContext:
    """
    Transport-agnostic request context used by REST source strategies.

    This avoids coupling public contracts to a specific HTTP client object
    while still allowing authentication and pagination logic to mutate
    request intent through an explicit model.
    """

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0


@runtime_checkable
class AuthHookProtocol(Protocol):
    """
    Strategy for applying authentication details to a request context.
    """

    def __call__(self, request_context: RestRequestContext) -> RestRequestContext:
        """
        Return an authenticated request context.
        """
        ...


@runtime_checkable
class PaginationStrategyProtocol(Protocol):
    """
    Strategy for deriving the next request in a paginated API flow.
    """

    def get_next_request(
        self,
        current_request: RestRequestContext,
        response_payload: Any,
        page_index: int,
    ) -> RestRequestContext | None:
        """
        Return the next request context, or None when pagination is complete.
        """
        ...


@runtime_checkable
class ResourceNormaliserProtocol(Protocol):
    """
    Strategy for normalising one full record before emission.
    """

    def __call__(self, record: dict[str, Any]) -> dict[str, Any]:
        """
        Accept the entire source record and return a single dictionary.
        """
        ...
