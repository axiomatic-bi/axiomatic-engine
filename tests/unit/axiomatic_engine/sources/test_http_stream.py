from __future__ import annotations

import gzip
import io
import unittest
from unittest.mock import patch

from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.sources.file.http_stream import (
    HttpFileResourceDefinition,
    HttpFileSourceDefinition,
    HttpStreamResource,
    HttpStreamSource,
)


class _FakeResponse:
    def __init__(self, raw_payload: bytes, raise_error: Exception | None = None) -> None:
        self.raw = io.BytesIO(raw_payload)
        self._raise_error = raise_error

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)

    def raise_for_status(self) -> None:
        if self._raise_error is not None:
            raise self._raise_error
        return None


class HttpStreamResourceTests(unittest.TestCase):
    def test_inference_handles_case_and_query_suffixes(self) -> None:
        resource = HttpStreamResource(
            name="query",
            url="https://example.com/export.TSV.GZ?download=1",
        )

        self.assertEqual(resource.delimiter, "\t")
        self.assertEqual(resource.compression, "gzip")

    @patch("axiomatic_engine.sources.file.http_stream.requests.get")
    def test_read_streams_csv_with_default_inference(self, mock_get) -> None:
        csv_payload = "id,name\n1,alpha\n2,beta\n".encode("utf-8")
        mock_get.return_value = _FakeResponse(raw_payload=csv_payload)

        resource = HttpStreamResource(
            name="users",
            url="https://example.com/users.csv",
        )
        rows = list(resource.read())

        self.assertEqual(
            rows,
            [
                {"id": "1", "name": "alpha"},
                {"id": "2", "name": "beta"},
            ],
        )
        mock_get.assert_called_once_with(
            "https://example.com/users.csv",
            stream=True,
            timeout=30.0,
        )
        self.assertEqual(resource.delimiter, ",")
        self.assertEqual(resource.compression, "none")

    @patch("axiomatic_engine.sources.file.http_stream.requests.get")
    def test_read_streams_gzipped_tsv_with_inference(self, mock_get) -> None:
        tsv_payload = "id\tname\n10\tgamma\n".encode("utf-8")
        gzipped_payload = gzip.compress(tsv_payload)
        mock_get.return_value = _FakeResponse(raw_payload=gzipped_payload)

        resource = HttpStreamResource(
            name="events",
            url="https://example.com/events.tsv.gz",
        )
        rows = list(resource.read())

        self.assertEqual(rows, [{"id": "10", "name": "gamma"}])
        self.assertEqual(resource.delimiter, "\t")
        self.assertEqual(resource.compression, "gzip")

    @patch("axiomatic_engine.sources.file.http_stream.requests.get")
    def test_read_honours_explicit_delimiter_and_compression(self, mock_get) -> None:
        payload = "id|value\n5|overridden\n".encode("utf-8")
        mock_get.return_value = _FakeResponse(raw_payload=payload)

        resource = HttpStreamResource(
            name="custom",
            url="https://example.com/custom.tsv.gz",
            delimiter="|",
            compression="none",
        )
        rows = list(resource.read())

        self.assertEqual(rows, [{"id": "5", "value": "overridden"}])
        self.assertEqual(resource.delimiter, "|")
        self.assertEqual(resource.compression, "none")

    @patch("axiomatic_engine.sources.file.http_stream.requests.get")
    def test_read_propagates_http_errors(self, mock_get) -> None:
        expected_error = RuntimeError("upstream unavailable")
        mock_get.return_value = _FakeResponse(
            raw_payload=b"",
            raise_error=expected_error,
        )
        resource = HttpStreamResource(
            name="broken",
            url="https://example.com/broken.csv",
        )

        with self.assertRaises(RuntimeError):
            _ = list(resource.read())

    def test_get_load_hints_returns_definition_hints(self) -> None:
        expected_hints = ResourceLoadHints(
            write_disposition="merge",
            primary_key="id",
            schema_evolution_mode="auto",
        )
        resource = HttpStreamResource(
            name="hinted",
            url="https://example.com/hinted.csv",
            load_hints=expected_hints,
        )

        self.assertEqual(resource.get_load_hints(), expected_hints)


class HttpStreamSourceTests(unittest.TestCase):
    def test_source_exposes_expected_resources_and_metadata(self) -> None:
        source = HttpStreamSource(
            name="http_files",
            resource_map={
                "customers": "https://example.com/customers.csv",
                "orders": "https://example.com/orders.tsv.gz",
            },
        )

        resources = source.get_resources()

        self.assertEqual(source.kind, "http_file")
        self.assertEqual(source.get_incremental_key(), None)
        self.assertEqual([resource.name for resource in resources], ["customers", "orders"])
        self.assertEqual(resources[0].delimiter, ",")
        self.assertEqual(resources[1].compression, "gzip")

    def test_from_definition_builds_resources_with_overrides(self) -> None:
        definition = HttpFileSourceDefinition(
            kind="http_file",
            name="imdb_http",
            resources=[
                HttpFileResourceDefinition(
                    name="title_basics",
                    url="https://datasets.imdbws.com/title.basics.tsv.gz",
                    timeout_seconds=12.5,
                    load_hints=ResourceLoadHints(write_disposition="replace"),
                )
            ],
        )

        source = HttpStreamSource.from_definition(definition=definition)
        resources = source.get_resources()

        self.assertEqual(source.kind, "http_file")
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].name, "title_basics")
        self.assertEqual(resources[0].timeout_seconds, 12.5)
        self.assertEqual(resources[0].get_load_hints().write_disposition, "replace")


if __name__ == "__main__":
    unittest.main()
