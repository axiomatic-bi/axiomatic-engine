from __future__ import annotations

import unittest
from unittest.mock import patch

from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.sources.base import BaseSource


class _FakeResource:
    def __init__(self, name: str, load_hints: ResourceLoadHints | None = None) -> None:
        self.name = name
        self._load_hints = load_hints

    def read(self):
        return iter([{"id": 1}])

    def get_load_hints(self) -> ResourceLoadHints | None:
        return self._load_hints


class _FakeSourceLogic:
    def __init__(self, resources: list[_FakeResource]) -> None:
        self.name = "fake_source"
        self.resources = resources

    def get_resources(self):
        return self.resources

    def get_incremental_key(self):
        return None


class BaseSourceTests(unittest.TestCase):
    @patch("axiomatic_engine.sources.base.dlt.source", side_effect=lambda fn, name: fn)
    @patch("axiomatic_engine.sources.base.dlt.resource")
    def test_to_dlt_without_hints_keeps_default_resource_kwargs(
        self, mock_resource, _mock_source
    ) -> None:
        source = BaseSource(source_logic=_FakeSourceLogic(resources=[_FakeResource(name="items")]))

        source.to_dlt()

        self.assertEqual(mock_resource.call_count, 1)
        _, kwargs = mock_resource.call_args
        self.assertEqual(kwargs["name"], "items")
        self.assertNotIn("write_disposition", kwargs)
        self.assertNotIn("primary_key", kwargs)
        self.assertNotIn("schema_contract", kwargs)

    @patch("axiomatic_engine.sources.base.dlt.source", side_effect=lambda fn, name: fn)
    @patch("axiomatic_engine.sources.base.dlt.resource")
    def test_to_dlt_with_hints_maps_expected_resource_kwargs(
        self, mock_resource, _mock_source
    ) -> None:
        hinted_resource = _FakeResource(
            name="items",
            load_hints=ResourceLoadHints(
                write_disposition="merge",
                primary_key="id",
                schema_evolution_mode="strict",
            ),
        )
        source = BaseSource(source_logic=_FakeSourceLogic(resources=[hinted_resource]))

        source.to_dlt()

        self.assertEqual(mock_resource.call_count, 1)
        _, kwargs = mock_resource.call_args
        self.assertEqual(kwargs["name"], "items")
        self.assertEqual(kwargs["write_disposition"], "merge")
        self.assertEqual(kwargs["primary_key"], "id")
        self.assertEqual(kwargs["schema_contract"], {"schema_evolution": "strict"})

    def test_to_dlt_merge_without_primary_key_raises(self) -> None:
        invalid_resource = _FakeResource(
            name="items",
            load_hints=ResourceLoadHints(write_disposition="merge"),
        )
        source = BaseSource(source_logic=_FakeSourceLogic(resources=[invalid_resource]))

        with self.assertRaises(ValueError):
            source.to_dlt()


if __name__ == "__main__":
    unittest.main()
