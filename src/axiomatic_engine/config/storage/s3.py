from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class S3StorageSettings:
    kind: Literal["s3"] = "s3"
    path: str = "./data/raw_vault"
    bucket: str | None = None
