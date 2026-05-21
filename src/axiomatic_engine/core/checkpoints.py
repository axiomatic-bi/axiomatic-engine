from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from axiomatic_engine.contracts.warehouse import WarehouseProtocol

LOGGER = logging.getLogger(__name__)

_STATE_SCHEMA = "_axiomatic_state"
_CHECKPOINTS_TABLE = "checkpoints"
_QUALIFIED_TABLE = f'"{_STATE_SCHEMA}"."{_CHECKPOINTS_TABLE}"'

_CREATE_SCHEMA_SQL = f'CREATE SCHEMA IF NOT EXISTS "{_STATE_SCHEMA}"'

_CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {_QUALIFIED_TABLE} (
    source_name   VARCHAR NOT NULL,
    resource_name VARCHAR NOT NULL,
    last_loaded_at TIMESTAMPTZ NOT NULL,
    etag          VARCHAR,
    content_hash  VARCHAR,
    PRIMARY KEY (source_name, resource_name)
)
"""

_UPSERT_SQL = f"""
INSERT INTO {_QUALIFIED_TABLE}
    (source_name, resource_name, last_loaded_at, etag, content_hash)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (source_name, resource_name)
DO UPDATE SET
    last_loaded_at = excluded.last_loaded_at,
    etag           = excluded.etag,
    content_hash   = excluded.content_hash
"""

_SELECT_SQL = f"""
SELECT etag, content_hash, last_loaded_at
FROM   {_QUALIFIED_TABLE}
WHERE  source_name = ?
  AND  resource_name = ?
"""


@dataclass
class ResourceCheckpoint:
    """
    Stored state for a single ingested resource.
    """

    source_name: str
    resource_name: str
    last_loaded_at: datetime
    etag: str | None = None
    content_hash: str | None = None


class CheckpointStore:
    """
    Reads and writes checkpoint state to the warehouse.

    State is stored in _axiomatic_state.checkpoints so it travels with
    the warehouse file and requires no external infrastructure.
    """

    def __init__(self, warehouse: WarehouseProtocol) -> None:
        self._warehouse = warehouse

    def initialise(self) -> None:
        """
        Ensure the state schema and checkpoints table exist.
        Safe to call on every pipeline run.
        """
        self._warehouse.execute(_CREATE_SCHEMA_SQL)
        self._warehouse.execute(_CREATE_TABLE_SQL)
        LOGGER.debug("Checkpoint store initialised.")

    def get(self, source_name: str, resource_name: str) -> ResourceCheckpoint | None:
        """
        Return the stored checkpoint for a resource, or None if not yet loaded.
        """
        rows = self._warehouse.execute(_SELECT_SQL, [source_name, resource_name])
        if not rows:
            return None
        etag, content_hash, loaded_at_str = rows[0]
        try:
            loaded_at = datetime.fromisoformat(loaded_at_str)
        except (ValueError, TypeError):
            loaded_at = datetime.now(timezone.utc)
        return ResourceCheckpoint(
            source_name=source_name,
            resource_name=resource_name,
            last_loaded_at=loaded_at,
            etag=etag,
            content_hash=content_hash,
        )

    def save(self, checkpoint: ResourceCheckpoint) -> None:
        """
        Upsert a checkpoint record after a successful resource load.
        """
        self._warehouse.execute(
            _UPSERT_SQL,
            [
                checkpoint.source_name,
                checkpoint.resource_name,
                checkpoint.last_loaded_at.isoformat(),
                checkpoint.etag,
                checkpoint.content_hash,
            ],
        )
        LOGGER.debug(
            "Checkpoint saved: %s / %s (etag=%s)",
            checkpoint.source_name,
            checkpoint.resource_name,
            checkpoint.etag,
        )
