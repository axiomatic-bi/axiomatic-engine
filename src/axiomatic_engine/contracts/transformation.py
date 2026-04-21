from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from axiomatic_engine.contracts.warehouse import WarehouseKind

TransformationKind = Literal["dbt"]
TransformationStatus = Literal["succeeded", "failed"]


@dataclass(frozen=True)
class TransformationRequest:
    """
    Runtime inputs for a transformation execution.

    The contract stays backend-agnostic: callers provide paths and environment
    context, while adapters decide how to execute.
    """

    project_dir: Path
    warehouse_kind: WarehouseKind
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TransformationResult:
    """
    Normalised outcome returned by any transformation adapter.
    """

    backend: TransformationKind
    status: TransformationStatus
    duration_seconds: float
    details: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class TransformationProtocol(Protocol):
    """
    Engine contract for transformation adapters.
    """

    kind: TransformationKind

    def run(self, request: TransformationRequest) -> TransformationResult:
        """
        Execute transformations and return a normalised outcome.
        """

        ...
