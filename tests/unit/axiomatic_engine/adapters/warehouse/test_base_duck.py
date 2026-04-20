from __future__ import annotations

import unittest
from pathlib import Path

from axiomatic_engine.adapters.warehouse.base_duck import (
    _looks_like_uri,
    _normalise_read_uri,
)


class DuckBaseHelperTests(unittest.TestCase):
    def test_normalise_read_uri_preserves_explicit_uri_schemes(self) -> None:
        self.assertEqual(
            _normalise_read_uri("s3://bucket/path/file.parquet"),
            "s3://bucket/path/file.parquet",
        )
        self.assertEqual(_normalise_read_uri("md:warehouse"), "md:warehouse")

    def test_normalise_read_uri_resolves_relative_local_path(self) -> None:
        relative_path = "data/sample.csv"
        normalised = _normalise_read_uri(relative_path)

        self.assertTrue(Path(normalised).is_absolute())
        self.assertTrue(normalised.endswith(str(Path("data") / "sample.csv")))

    def test_looks_like_uri_distinguishes_windows_absolute_path(self) -> None:
        self.assertFalse(_looks_like_uri(r"C:\data\input.csv"))
        self.assertTrue(_looks_like_uri("https://example.com/data.csv"))


if __name__ == "__main__":
    unittest.main()
