from __future__ import annotations
import pathlib
from axiomatic_engine.contracts.storage import RawStorageProtocol, RawFileRef

class LocalStorage(RawStorageProtocol):
    """
    Adapter for interacting with the local filesystem.
    Treats a local directory as a standardised object store.
    """
    def __init__(self, base_path: str | pathlib.Path):
        self.base_path = pathlib.Path(base_path)

    def list_files(self, prefix: str | None = None) -> list[RawFileRef]:
        """
        Scans the local directory and returns canonical file references.
        """
        search_path = self.base_path
        if prefix:
            search_path = search_path / prefix

        if not search_path.exists():
            return []

        # We return RawFileRef objects to keep the engine logic decoupled
        # from OS-specific path strings.
        return [
            RawFileRef(
                file_name=f.name,
                read_uri=str(f.absolute()),
                content_type="application/octet-stream" # Default for raw files
            )
            for f in search_path.iterdir() if f.is_file()
        ]
