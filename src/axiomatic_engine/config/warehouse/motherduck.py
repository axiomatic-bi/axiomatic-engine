from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MotherDuckWarehouseSettings:
    kind: Literal["motherduck"] = "motherduck"
    path: str = "md:analytics"
    access_token: str | None = None
