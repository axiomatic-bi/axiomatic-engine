from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DuckDBWarehouseSettings:
    kind: Literal["duckdb"] = "duckdb"
    path: str = "./data/warehouse.duckdb"
