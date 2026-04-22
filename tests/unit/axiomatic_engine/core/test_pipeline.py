from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.config.storage import LocalStorageSettings
from axiomatic_engine.config.warehouse import DuckDBWarehouseSettings
from axiomatic_engine.core.pipeline import Pipeline


class PipelineConstructionTests(unittest.TestCase):
    def test_pipeline_initialises_with_engine_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = EngineSettings(
                storage=LocalStorageSettings(path=temp_dir),
                warehouse=DuckDBWarehouseSettings(
                    path=str(Path(temp_dir) / "analytics.duckdb"),
                ),
            )

            pipeline = Pipeline(settings=settings)

            self.assertIsNotNone(pipeline.storage)
            self.assertIsNotNone(pipeline.warehouse)
            self.assertIsNotNone(pipeline.ingestor)

    def test_pipeline_runs_transformations_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
                with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
                    with patch("axiomatic_engine.core.pipeline.get_transformation_adapter") as mock_transform_factory:
                        mock_storage = Mock()
                        mock_storage.list_files.return_value = []
                        mock_warehouse = Mock()
                        mock_storage_factory.return_value = mock_storage
                        mock_warehouse_factory.return_value = mock_warehouse

                        mock_transform = Mock()
                        mock_transform.kind = "dbt"
                        mock_transform.run.return_value = Mock(
                            status="succeeded",
                            backend="dbt",
                            details={},
                        )
                        mock_transform_factory.return_value = mock_transform

                        settings = EngineSettings.from_env(
                            {
                                "AXIOMATIC_STORAGE_KIND": "local",
                                "AXIOMATIC_STORAGE_PATH": temp_dir,
                                "AXIOMATIC_WAREHOUSE_KIND": "motherduck",
                                "AXIOMATIC_WAREHOUSE_PATH": "md:analytics",
                                "AXIOMATIC_SCHEMA_BRONZE": "raw_zone",
                                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
                                "AXIOMATIC_TRANSFORM_ENABLED": "true",
                                "AXIOMATIC_TRANSFORM_BACKEND": "dbt",
                                "AXIOMATIC_DBT_PROJECT_DIR": "./projects/fake-store/dbt",
                                "AXIOMATIC_DBT_PROFILES_DIR": "./projects/fake-store/dbt",
                                "AXIOMATIC_DBT_PROFILE_NAME": "fake_store",
                                "AXIOMATIC_DBT_TARGET": "dev",
                            }
                        )
                        pipeline = Pipeline(settings=settings)
                        pipeline.ingestor = Mock()
                        pipeline.land_raw_data = Mock(return_value=False)

                        source = Mock()
                        source.name = "fake_store"

                        pipeline.run(source=source, force_reload=True)

                        pipeline.ingestor.run.assert_called_once_with(
                            source=source,
                            dataset_name="raw_zone",
                        )
                        mock_transform.run.assert_called_once()

    def test_pipeline_skips_transformations_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
                with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
                    with patch("axiomatic_engine.core.pipeline.get_transformation_adapter") as mock_transform_factory:
                        mock_storage = Mock()
                        mock_storage.list_files.return_value = []
                        mock_storage_factory.return_value = mock_storage
                        mock_warehouse_factory.return_value = Mock()

                        settings = EngineSettings.from_env(
                            {
                                "AXIOMATIC_STORAGE_KIND": "local",
                                "AXIOMATIC_STORAGE_PATH": temp_dir,
                                "AXIOMATIC_WAREHOUSE_KIND": "duckdb",
                                "AXIOMATIC_WAREHOUSE_PATH": str(
                                    Path(temp_dir) / "analytics.duckdb"
                                ),
                                "AXIOMATIC_TRANSFORM_ENABLED": "false",
                            }
                        )
                        pipeline = Pipeline(settings=settings)
                        pipeline.ingestor = Mock()
                        pipeline.land_raw_data = Mock(return_value=False)

                        source = Mock()
                        source.name = "fake_store"

                        pipeline.run(source=source, force_reload=False)

                        mock_transform_factory.assert_not_called()

    def test_pipeline_raises_when_transformations_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
                with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
                    with patch("axiomatic_engine.core.pipeline.get_transformation_adapter") as mock_transform_factory:
                        mock_storage = Mock()
                        mock_storage.list_files.return_value = []
                        mock_storage_factory.return_value = mock_storage
                        mock_warehouse_factory.return_value = Mock()

                        failing_transform = Mock()
                        failing_transform.kind = "dbt"
                        failing_transform.run.return_value = Mock(
                            status="failed",
                            backend="dbt",
                            details={"stderr": "dbt error"},
                        )
                        mock_transform_factory.return_value = failing_transform

                        settings = EngineSettings.from_env(
                            {
                                "AXIOMATIC_STORAGE_KIND": "local",
                                "AXIOMATIC_STORAGE_PATH": temp_dir,
                                "AXIOMATIC_WAREHOUSE_KIND": "motherduck",
                                "AXIOMATIC_WAREHOUSE_PATH": "md:analytics",
                                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
                                "AXIOMATIC_TRANSFORM_ENABLED": "true",
                                "AXIOMATIC_TRANSFORM_BACKEND": "dbt",
                                "AXIOMATIC_DBT_PROJECT_DIR": "./projects/fake-store/dbt",
                                "AXIOMATIC_DBT_PROFILES_DIR": "./projects/fake-store/dbt",
                                "AXIOMATIC_DBT_PROFILE_NAME": "fake_store",
                                "AXIOMATIC_DBT_TARGET": "dev",
                            }
                        )
                        pipeline = Pipeline(settings=settings)
                        pipeline.ingestor = Mock()
                        pipeline.land_raw_data = Mock(return_value=False)

                        source = Mock()
                        source.name = "fake_store"

                        with self.assertRaises(RuntimeError):
                            pipeline.run(source=source, force_reload=True)


if __name__ == "__main__":
    unittest.main()
