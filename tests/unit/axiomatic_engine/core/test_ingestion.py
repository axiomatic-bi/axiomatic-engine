from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from axiomatic_engine.core.ingestion import Ingestor


class IngestorTests(unittest.TestCase):
    def test_run_configures_pipeline_with_destination_and_pipelines_dir(self) -> None:
        warehouse = Mock()
        destination = object()
        warehouse.get_dlt_destination.return_value = destination
        warehouse.get_dlt_credentials.return_value = "data/warehouse.duckdb"

        source = Mock()
        source.name = "fake_store_bronze_ingest"
        source.to_dlt.return_value = "dlt_source"

        mock_pipeline = Mock()
        mock_pipeline.run.return_value = {"status": "ok"}

        with patch("axiomatic_engine.core.ingestion.dlt.pipeline", return_value=mock_pipeline) as mock_dlt_pipeline:
            ingestor = Ingestor(
                warehouse=warehouse,
                dlt_pipelines_dir="./projects/fake_store/.dlt/pipelines",
            )

            ingestor.run(source=source, dataset_name="bronze")

        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="fake_store_bronze_ingest",
            dataset_name="bronze",
            progress="log",
            destination=destination,
            pipelines_dir="./projects/fake_store/.dlt/pipelines",
        )
        mock_pipeline.run.assert_called_once_with(
            "dlt_source",
            destination=destination,
            credentials="data/warehouse.duckdb",
        )

    def test_run_omits_pipelines_dir_when_not_configured(self) -> None:
        warehouse = Mock()
        warehouse.get_dlt_destination.return_value = "duckdb"
        warehouse.get_dlt_credentials.return_value = "data/warehouse.duckdb"

        source = Mock()
        source.name = "fake_store_bronze_ingest"
        source.to_dlt.return_value = "dlt_source"

        mock_pipeline = Mock()
        mock_pipeline.run.return_value = {"status": "ok"}

        with patch("axiomatic_engine.core.ingestion.dlt.pipeline", return_value=mock_pipeline) as mock_dlt_pipeline:
            ingestor = Ingestor(warehouse=warehouse)
            ingestor.run(source=source, dataset_name="bronze")

        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="fake_store_bronze_ingest",
            dataset_name="bronze",
            progress="log",
            destination="duckdb",
        )


if __name__ == "__main__":
    unittest.main()
