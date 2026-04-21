from __future__ import annotations

from axiomatic_engine.contracts.rest import RestRequestContext


class NoAuthHook:
    """
    Default authentication strategy that performs no mutation.
    """

    def __call__(self, request_context: RestRequestContext) -> RestRequestContext:
        return request_context
