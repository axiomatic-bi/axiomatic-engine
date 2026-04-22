from __future__ import annotations

from axiomatic_engine.config.storage.gcs import GcsStorageSettings
from axiomatic_engine.config.storage.local import LocalStorageSettings
from axiomatic_engine.config.storage.s3 import S3StorageSettings
from axiomatic_engine.config.storage.types import StorageSettings
from axiomatic_engine.contracts.storage import RawStorageKind


def build_storage_settings(
    kind: RawStorageKind,
    path: str,
    existing: StorageSettings | None = None,
) -> StorageSettings:
    if kind == "local":
        return LocalStorageSettings(path=path)
    if kind == "gcs":
        bucket = existing.bucket if isinstance(existing, GcsStorageSettings) else None
        return GcsStorageSettings(path=path, bucket=bucket)
    if kind == "s3":
        bucket = existing.bucket if isinstance(existing, S3StorageSettings) else None
        return S3StorageSettings(path=path, bucket=bucket)
    raise ValueError(f"Unsupported storage kind: {kind}")
