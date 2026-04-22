from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaSettings:
    """
    Typed schema names for medallion-style layers.
    """

    bronze: str = "bronze"
    silver: str = "silver"
    gold: str = "gold"
    analytics: str = "analytics"
