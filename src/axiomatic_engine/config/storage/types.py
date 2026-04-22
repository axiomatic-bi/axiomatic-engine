from __future__ import annotations

from axiomatic_engine.config.storage.gcs import GcsStorageSettings
from axiomatic_engine.config.storage.local import LocalStorageSettings
from axiomatic_engine.config.storage.s3 import S3StorageSettings

StorageSettings = LocalStorageSettings | GcsStorageSettings | S3StorageSettings
