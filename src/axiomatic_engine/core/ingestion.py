import logging
from time import perf_counter
from typing import Any

import dlt

from axiomatic_engine.contracts.warehouse import WarehouseProtocol
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

    def run(self, source: BaseSource, dataset_name: str):
        """
        Executes the ingestion pipeline.

        Triggers dlt loading using destination config from the warehouse adapter.
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
        load_info = pipeline.run(
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
        return load_info
