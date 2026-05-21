import logging
from time import perf_counter
from typing import Any

import dlt

from axiomatic_engine.contracts.warehouse import WarehouseProtocol
from axiomatic_engine.core.report import IngestionReport, ResourceIngestionResult
from axiomatic_engine.sources.base import BaseSource

LOGGER = logging.getLogger(__name__)


class Ingestor:
    """
    The Axiomatic worker responsible for executing data movement.

    It orchestrates the flow from a BaseSource implementation into
     a WarehouseProtocol implementation using dlt.
    """

    def __init__(
        self,
        warehouse: WarehouseProtocol,
        dlt_pipelines_dir: str | None = None,
    ) -> None:
        self.warehouse = warehouse
        self.dlt_pipelines_dir = dlt_pipelines_dir

    def run(self, source: BaseSource, dataset_name: str) -> IngestionReport:
        """
        Executes the ingestion pipeline.

        Triggers dlt loading using destination config from the warehouse adapter.
        Returns an IngestionReport with per-resource row counts and timing.
        """
        LOGGER.info("Starting ingestion for source: %s", source.name)

        destination = self.warehouse.get_dlt_destination()
        credentials = self.warehouse.get_dlt_credentials()

        pipeline_kwargs: dict[str, Any] = {
            "pipeline_name": source.name,
            "dataset_name": dataset_name,
            "progress": "log",
            "destination": destination,
        }
        if self.dlt_pipelines_dir is not None:
            pipeline_kwargs["pipelines_dir"] = self.dlt_pipelines_dir

        pipeline = dlt.pipeline(
            **pipeline_kwargs,
        )
        LOGGER.info(
            "Starting dlt pipeline run for source: %s (extract, normalise, load)",
            source.name,
        )
        load_start = perf_counter()
        pipeline.run(
            source.to_dlt(),
            destination=destination,
            credentials=credentials,
        )
        duration_s = perf_counter() - load_start
        LOGGER.info(
            "Ingestion complete for %s in %.1fs.",
            source.name,
            duration_s,
        )

        row_counts = self._extract_row_counts(pipeline)
        resources = [
            ResourceIngestionResult(
                name=res.name,
                status="loaded",
                row_count=row_counts.get(res.name),
            )
            for res in source.get_resources()
        ]
        return IngestionReport(
            source_name=source.name,
            resources=resources,
            duration_seconds=duration_s,
        )

    @staticmethod
    def _extract_row_counts(pipeline: Any) -> dict[str, int]:
        """
        Pull per-table row counts from dlt's normalisation trace.
        Returns an empty dict if trace information is unavailable.
        """
        try:
            normalize_info = pipeline.last_trace.last_normalize_info
            if normalize_info is None:
                return {}
            counts = normalize_info.row_counts
            return {k: v for k, v in counts.items() if not k.startswith("_dlt")}
        except Exception:  # noqa: BLE001
            return {}
