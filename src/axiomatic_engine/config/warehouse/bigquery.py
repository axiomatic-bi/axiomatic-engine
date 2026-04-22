from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class BigQueryWarehouseSettings:
    kind: Literal["bigquery"] = "bigquery"
    path: str = "project.dataset"
