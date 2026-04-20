from __future__ import annotations

from dataclasses import dataclass

from axiomatic_engine.contracts.storage import RawStorageKind


@dataclass(frozen=True)
class StorageSettings:
    """
    Typed settings for raw storage adapter selection.
    """

    kind: RawStorageKind = "local"
    path: str = "./data/raw_vault"
