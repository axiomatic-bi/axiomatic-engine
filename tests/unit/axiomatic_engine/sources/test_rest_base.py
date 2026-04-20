from __future__ import annotations

import unittest
from unittest.mock import patch

from axiomatic_engine.contracts.rest import RestRequestContext
from axiomatic_engine.sources.rest.base import RestApiResource, RestApiResourceDefinition


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _TwoPagePaginationStrategy:
    def get_next_request(
        self,
        current_request: RestRequestContext,
        response_payload: object,
        page_index: int,
    ) -> RestRequestContext | None:
        _ = response_payload
        if page_index == 0:
            return RestRequestContext(
                method=current_request.method,
                url=current_request.url,
                headers=current_request.headers,
                query_params={**current_request.query_params, "page": "2"},
                timeout_seconds=current_request.timeout_seconds,
            )
        return None


class RestApiResourceTests(unittest.TestCase):
    @patch("axiomatic_engine.sources.rest.base.requests.request")
    def test_read_applies_normaliser_before_yield(self, mock_request) -> None:
        mock_request.return_value = _FakeResponse(
            {"data": {"items": [{"id": 1, "value": "alpha"}]}}
        )

        observed_inputs: list[dict[str, object]] = []

        def resource_normaliser(record: dict[str, object]) -> dict[str, object]:
            observed_inputs.append(record)
            return {"identifier": record["id"], "value": record["value"]}

        resource = RestApiResource(
            base_url="https://example.com",
            definition=RestApiResourceDefinition(
                name="sample",
                endpoint_path="items",
                resource_normaliser=resource_normaliser,
            ),
        )

        emitted = list(resource.read())

        self.assertEqual(observed_inputs, [{"id": 1, "value": "alpha"}])
        self.assertEqual(emitted, [{"identifier": 1, "value": "alpha"}])

    @patch("axiomatic_engine.sources.rest.base.requests.request")
    def test_read_follows_pagination_strategy(self, mock_request) -> None:
        mock_request.side_effect = [
            _FakeResponse([{"id": 1}]),
            _FakeResponse([{"id": 2}]),
        ]

        resource = RestApiResource(
            base_url="https://example.com",
            definition=RestApiResourceDefinition(
                name="paged",
                endpoint_path="items",
                query_params={"page": "1"},
                pagination_strategy=_TwoPagePaginationStrategy(),
            ),
        )

        emitted = list(resource.read())

        self.assertEqual(emitted, [{"id": 1}, {"id": 2}])
        self.assertEqual(mock_request.call_count, 2)
        first_call = mock_request.call_args_list[0].kwargs
        second_call = mock_request.call_args_list[1].kwargs
        self.assertEqual(first_call["params"]["page"], "1")
        self.assertEqual(second_call["params"]["page"], "2")

    @patch("axiomatic_engine.sources.rest.base.requests.request")
    def test_read_rejects_invalid_normaliser_output(self, mock_request) -> None:
        mock_request.return_value = _FakeResponse([{"id": 1}])

        def invalid_normaliser(record: dict[str, object]) -> dict[str, object]:
            _ = record
            return ["not-a-dict"]  # type: ignore[return-value]

        resource = RestApiResource(
            base_url="https://example.com",
            definition=RestApiResourceDefinition(
                name="invalid-normaliser",
                endpoint_path="items",
                resource_normaliser=invalid_normaliser,
            ),
        )

        with self.assertRaises(TypeError):
            _ = list(resource.read())


if __name__ == "__main__":
    unittest.main()
