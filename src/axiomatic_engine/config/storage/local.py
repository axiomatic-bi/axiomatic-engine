from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LocalStorageSettings:
    kind: Literal["local"] = "local"
    path: str = "./data/raw_vault"
