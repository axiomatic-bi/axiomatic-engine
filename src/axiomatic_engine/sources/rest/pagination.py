from __future__ import annotations

from typing import Any

from axiomatic_engine.contracts.rest import RestRequestContext


class NoPaginationStrategy:
    """
    Default pagination strategy for single-request resources.
    """

    def get_next_request(
        self,
        current_request: RestRequestContext,
        response_payload: Any,
        page_index: int,
    ) -> RestRequestContext | None:
        _ = current_request
        _ = response_payload
        _ = page_index
        return None
