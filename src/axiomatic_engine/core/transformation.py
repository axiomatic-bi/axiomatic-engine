from __future__ import annotations

import logging
import os
from pathlib import Path

from axiomatic_engine.contracts.transformation import (
    TransformationProtocol,
    TransformationRequest,
    TransformationResult,
)
from axiomatic_engine.contracts.warehouse import WarehouseKind

LOGGER = logging.getLogger(__name__)


class Transformer:
    """
    Orchestrates the transformation stage independent of pipeline control flow.
    """

    def __init__(
        self,
        adapter: TransformationProtocol,
        warehouse_kind: WarehouseKind,
        project_dir: str,
    ) -> None:
        self.adapter = adapter
        self.warehouse_kind: WarehouseKind = warehouse_kind
        self.project_dir = Path(project_dir)

    def run(self) -> TransformationResult:
        LOGGER.info("Running transformations using backend: %s", self.adapter.kind)
        result = self.adapter.run(
            request=TransformationRequest(
                project_dir=self.project_dir,
                warehouse_kind=self.warehouse_kind,
                environment=dict(os.environ),
            )
        )
        if result.status != "succeeded":
            raise RuntimeError(
                f"Transformation stage failed with backend {result.backend}: {result.details}"
            )
        return result
