from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class GcsStorageSettings:
    kind: Literal["gcs"] = "gcs"
    path: str = "./data/raw_vault"
    bucket: str | None = None
