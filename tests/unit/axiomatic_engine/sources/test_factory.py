from __future__ import annotations

import unittest

from axiomatic_engine.sources.factory import RestApiSourceDefinition, build_source
from axiomatic_engine.sources.file.http_stream import (
    HttpFileResourceDefinition,
    HttpFileSourceDefinition,
    HttpStreamSource,
)
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition, RestApiSource


class SourceFactoryTests(unittest.TestCase):
    def test_build_source_returns_rest_api_source(self) -> None:
        definition = RestApiSourceDefinition(
            kind="rest_api",
            name="fake_store",
            base_url="https://fakestoreapi.com",
            resources=[RestApiResourceDefinition(name="products", endpoint_path="products")],
        )

        source = build_source(definition=definition)

        self.assertIsInstance(source, RestApiSource)
        self.assertEqual(source.kind, "rest_api")
        self.assertEqual(source.name, "fake_store")

    def test_build_source_returns_http_file_source(self) -> None:
        definition = HttpFileSourceDefinition(
            kind="http_file",
            name="imdb",
            resources=[
                HttpFileResourceDefinition(
                    name="title_basics",
                    url="https://datasets.imdbws.com/title.basics.tsv.gz",
                )
            ],
        )

        source = build_source(definition=definition)

        self.assertIsInstance(source, HttpStreamSource)
        self.assertEqual(source.kind, "http_file")
        self.assertEqual(source.name, "imdb")


if __name__ == "__main__":
    unittest.main()
