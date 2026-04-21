from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Iterable, cast
from urllib.parse import urljoin

import requests

from axiomatic_engine.contracts.rest import (
    AuthHookProtocol,
    PaginationStrategyProtocol,
    RestRequestContext,
    ResourceNormaliserProtocol,
)
from axiomatic_engine.contracts.source import ResourceLoadHints, ResourceProtocol, SourceKind
from axiomatic_engine.sources.base import BaseSource
from axiomatic_engine.sources.rest.auth import NoAuthHook
from axiomatic_engine.sources.rest.pagination import NoPaginationStrategy

LOGGER = logging.getLogger(__name__)


def _identity_resource_normaliser(record: dict[str, Any]) -> dict[str, Any]:
    return record


def _as_record_list(candidate: Any) -> list[dict[str, Any]] | None:
    """
    Return candidate as a record list when it is a list of dictionaries.
    """
    if not isinstance(candidate, list):
        return None
    candidate_list = cast(list[Any], candidate)
    for list_item in candidate_list:
        if not isinstance(list_item, dict):
            return None
    return cast(list[dict[str, Any]], candidate_list)


@dataclass(frozen=True)
class RestApiResourceDefinition:
    """
    Declarative definition for a single REST-backed resource.
    """

    name: str
    endpoint_path: str
    query_params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    http_method: str = "GET"
    timeout_seconds: float = 30.0
    auth_hook: AuthHookProtocol = field(default_factory=NoAuthHook)
    pagination_strategy: PaginationStrategyProtocol = field(
        default_factory=NoPaginationStrategy
    )
    resource_normaliser: ResourceNormaliserProtocol = _identity_resource_normaliser
    load_hints: ResourceLoadHints | None = None


class RestApiResource(ResourceProtocol):
    """
    Resource wrapper for a single REST endpoint definition.
    """

    def __init__(
        self,
        base_url: str,
        definition: RestApiResourceDefinition,
    ) -> None:
        self.name = definition.name
        self.base_url = base_url
        self.definition = definition

    def _log_context(self) -> dict[str, str]:
        """
        Build consistent structured context for REST resource logging.
        """
        return {
            "resource_name": self.name,
            "endpoint_path": self.definition.endpoint_path,
            "base_url": self.base_url,
            "http_method": self.definition.http_method,
        }

    def get_load_hints(self) -> ResourceLoadHints | None:
        return self.definition.load_hints

    def _build_initial_request_context(self) -> RestRequestContext:
        endpoint_url = urljoin(f"{self.base_url.rstrip('/')}/", self.definition.endpoint_path)
        return RestRequestContext(
            method=self.definition.http_method.upper(),
            url=endpoint_url,
            headers=dict(self.definition.headers),
            query_params=dict(self.definition.query_params),
            timeout_seconds=self.definition.timeout_seconds,
        )

    def _execute_request(self, request_context: RestRequestContext) -> Any:
        response = requests.request(
            method=request_context.method,
            url=request_context.url,
            headers=request_context.headers,
            params=request_context.query_params,
            timeout=request_context.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _extract_records(self, response_payload: Any) -> list[dict[str, Any]]:
        """
        Convert common JSON API payload patterns into record dictionaries.

        Supports:
        - top-level list payloads
        - top-level object payloads
        - wrapped list payloads in `data` or `data.items`
        """
        top_level_list = _as_record_list(response_payload)
        if top_level_list is not None:
            return top_level_list

        if isinstance(response_payload, dict):
            payload_dict = cast(dict[str, Any], response_payload)
            data_value = payload_dict.get("data")
            data_list = _as_record_list(data_value)
            if data_list is not None:
                return data_list

            if isinstance(data_value, dict):
                data_dict = cast(dict[str, Any], data_value)
                items_value = data_dict.get("items")
                items_list = _as_record_list(items_value)
                if items_list is not None:
                    return items_list

            return [payload_dict]

        raise TypeError(
            f"Resource '{self.name}' received unsupported JSON payload type: "
            f"{type(response_payload).__name__}."
        )

    def read(self) -> Iterable[dict[str, Any]]:
        """
        Stream records from a REST endpoint with auth, pagination, and normalisation.
        """
        LOGGER.info(
            "Starting REST extraction for resource '%s'.",
            self.name,
            extra=self._log_context(),
        )

        current_request = self._build_initial_request_context()
        page_index = 0
        yielded_records = 0

        while current_request is not None:
            authenticated_request = self.definition.auth_hook(current_request)
            LOGGER.info(
                "Requesting page %s for resource '%s'.",
                page_index,
                self.name,
                extra={
                    **self._log_context(),
                    "page_index": str(page_index),
                    "request_url": authenticated_request.url,
                },
            )
            response_payload = self._execute_request(authenticated_request)
            extracted_records = self._extract_records(response_payload)

            LOGGER.info(
                "Fetched %s raw records for resource '%s' on page %s.",
                len(extracted_records),
                self.name,
                page_index,
                extra={**self._log_context(), "page_index": str(page_index)},
            )

            for raw_record in extracted_records:
                normalised_record: Any = self.definition.resource_normaliser(raw_record)
                if not isinstance(normalised_record, dict):
                    raise TypeError(
                        f"Resource '{self.name}' normaliser must return dict[str, Any], "
                        f"received {type(normalised_record).__name__}."
                    )
                yielded_records += 1
                yield normalised_record

            current_request = self.definition.pagination_strategy.get_next_request(
                current_request=authenticated_request,
                response_payload=response_payload,
                page_index=page_index,
            )
            page_index += 1

        LOGGER.info(
            "Completed REST extraction for resource '%s': pages=%s records=%s.",
            self.name,
            page_index,
            yielded_records,
            extra={**self._log_context(), "records_yielded": str(yielded_records)},
        )


class RestApiSource(BaseSource):
    """
    Collection of REST resources composed into a BaseSource bridge.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        resources: list[RestApiResourceDefinition],
    ) -> None:
        self.name = name
        self.kind: SourceKind = "api"
        self.base_url = base_url
        self._definitions = resources
        super().__init__(source_logic=self)

    def get_resources(self) -> list[ResourceProtocol]:
        return [
            RestApiResource(base_url=self.base_url, definition=definition)
            for definition in self._definitions
        ]

    def get_incremental_key(self) -> str | None:
        return None
