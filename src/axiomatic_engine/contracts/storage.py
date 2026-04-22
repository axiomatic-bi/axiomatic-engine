from __future__ import annotations
from typing import Protocol, runtime_checkable, Literal
from dataclasses import dataclass

RawStorageKind = Literal["local", "gcs", "s3"]

@dataclass(frozen=True)
class RawFileRef:
    """
    A canonical reference to a file in storage.
    Explicit names are preferred over abbreviations.
    """
    file_name: str
    read_uri: str
    content_type: str | None = None

@runtime_checkable
class RawStorageProtocol(Protocol):
    """
    Abstraction for where Bronze inputs live before warehouse load.
    This is the 'Rule Book' for any storage adapter (Local, GCS, S3).
    """

    def list_files(self, prefix: str | None = None) -> list[RawFileRef]:
        """
        Return canonical file references from the storage backend.
        The 'prefix' allows us to filter for specific folders or datasets.
        """
        ...
