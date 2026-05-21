from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

from axiomatic_engine.core.checkpoints import (
    CheckpointStore,
    ResourceCheckpoint,
    _CREATE_SCHEMA_SQL,
    _CREATE_TABLE_SQL,
    _UPSERT_SQL,
    _SELECT_SQL,
)


def _make_store() -> tuple[CheckpointStore, MagicMock]:
    warehouse = MagicMock()
    store = CheckpointStore(warehouse=warehouse)
    return store, warehouse


class CheckpointStoreInitialiseTests(unittest.TestCase):
    def test_initialise_creates_schema_and_table(self) -> None:
        store, warehouse = _make_store()
        store.initialise()
        warehouse.execute.assert_any_call(_CREATE_SCHEMA_SQL)
        warehouse.execute.assert_any_call(_CREATE_TABLE_SQL)

    def test_initialise_calls_execute_twice(self) -> None:
        store, warehouse = _make_store()
        store.initialise()
        self.assertEqual(warehouse.execute.call_count, 2)


class CheckpointStoreGetTests(unittest.TestCase):
    def test_get_returns_none_when_no_row(self) -> None:
        store, warehouse = _make_store()
        warehouse.execute.return_value = []
        result = store.get(source_name="src", resource_name="res")
        self.assertIsNone(result)

    def test_get_returns_checkpoint_with_etag(self) -> None:
        store, warehouse = _make_store()
        warehouse.execute.return_value = [("\"abc123\"", None)]
        result = store.get(source_name="nhs", resource_name="apr24")
        self.assertIsNotNone(result)
        self.assertEqual(result.source_name, "nhs")
        self.assertEqual(result.resource_name, "apr24")
        self.assertEqual(result.etag, "\"abc123\"")
        self.assertIsNone(result.content_hash)

    def test_get_passes_correct_parameters(self) -> None:
        store, warehouse = _make_store()
        warehouse.execute.return_value = []
        store.get(source_name="src", resource_name="res")
        warehouse.execute.assert_called_once_with(_SELECT_SQL, ["src", "res"])


class CheckpointStoreSaveTests(unittest.TestCase):
    def test_save_calls_upsert_with_correct_params(self) -> None:
        store, warehouse = _make_store()
        loaded_at = datetime(2025, 5, 1, tzinfo=timezone.utc)
        checkpoint = ResourceCheckpoint(
            source_name="nhs",
            resource_name="apr24",
            last_loaded_at=loaded_at,
            etag="\"abc123\"",
        )
        store.save(checkpoint)
        warehouse.execute.assert_called_once_with(
            _UPSERT_SQL,
            ["nhs", "apr24", loaded_at.isoformat(), "\"abc123\"", None],
        )

    def test_save_with_no_etag_passes_none(self) -> None:
        store, warehouse = _make_store()
        loaded_at = datetime(2025, 5, 1, tzinfo=timezone.utc)
        checkpoint = ResourceCheckpoint(
            source_name="nhs",
            resource_name="apr24",
            last_loaded_at=loaded_at,
            etag=None,
        )
        store.save(checkpoint)
        args = warehouse.execute.call_args[0][1]
        self.assertIsNone(args[3])
