from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.config.storage import LocalStorageSettings
from axiomatic_engine.config.warehouse import DuckDBWarehouseSettings
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.core.report import IngestionReport


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
                            duration_seconds=1.0,
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
                        pipeline.ingestor.run.return_value = IngestionReport(
                            source_name="fake_store", resources=[]
                        )

                        source = Mock()
                        source.name = "fake_store"
                        source.get_checkpointable_resources.return_value = []
                        source.get_resources.return_value = []

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

                        source = Mock()
                        source.name = "fake_store"
                        source.get_checkpointable_resources.return_value = []
                        source.supports_storage_cache.return_value = True
                        source.get_resources.return_value = []

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
                        pipeline.ingestor.run.return_value = IngestionReport(
                            source_name="fake_store", resources=[]
                        )

                        source = Mock()
                        source.name = "fake_store"
                        source.get_checkpointable_resources.return_value = []
                        source.get_resources.return_value = []

                        with self.assertRaises(RuntimeError):
                            pipeline.run(source=source, force_reload=True)

    def test_force_reload_forces_ingestion_when_cache_has_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
                with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
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
                    pipeline.ingestor.run.return_value = IngestionReport(
                        source_name="fake_store", resources=[]
                    )

                    source = Mock()
                    source.name = "fake_store"
                    source.get_checkpointable_resources.return_value = []
                    source.get_resources.return_value = []

                    pipeline.run(source=source, force_reload=True)

                    pipeline.ingestor.run.assert_called_once()


class ResolvSourceToRunTests(unittest.TestCase):
    """
    Tests for Pipeline._resolve_source_to_run — the checkpoint-aware
    ingestion gating logic.
    """

    def _make_pipeline(self, temp_dir: str) -> Pipeline:
        with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
            with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
                mock_storage = Mock()
                mock_storage.list_files.return_value = []
                mock_storage_factory.return_value = mock_storage
                mock_warehouse_factory.return_value = Mock()

                settings = EngineSettings.from_env(
                    {
                        "AXIOMATIC_STORAGE_KIND": "local",
                        "AXIOMATIC_STORAGE_PATH": temp_dir,
                        "AXIOMATIC_WAREHOUSE_KIND": "duckdb",
                        "AXIOMATIC_WAREHOUSE_PATH": str(Path(temp_dir) / "analytics.duckdb"),
                        "AXIOMATIC_TRANSFORM_ENABLED": "false",
                    }
                )
                pipeline = Pipeline(settings=settings)
                # Patches are scoped to construction only: the factory mock instances
                # are stored on pipeline.storage / pipeline.warehouse during __init__
                # and remain live after the with blocks exit.  Tests that need to
                # call through a factory a second time must manage patches themselves.
                pipeline.storage = mock_storage
                return pipeline

    def test_force_reload_bypasses_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            source = Mock()
            source.name = "src"
            source.get_checkpointable_resources.return_value = []

            result, etag_cache = pipeline._resolve_source_to_run(source=source, force_reload=True)

            self.assertIs(result, source)
            self.assertEqual(etag_cache, {})
            pipeline.storage.list_files.assert_not_called()

    def test_non_http_source_without_storage_cache_always_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            source = Mock()
            source.name = "rest_api_src"
            source.get_checkpointable_resources.return_value = []
            source.supports_storage_cache.return_value = False

            result, _ = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIs(result, source)
            pipeline.storage.list_files.assert_not_called()

    def test_file_backed_source_runs_when_cache_is_cold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            resource = Mock()
            resource.name = "my_resource"
            source = Mock()
            source.name = "file_source"
            source.get_checkpointable_resources.return_value = []
            source.supports_storage_cache.return_value = True
            source.get_resources.return_value = [resource]
            pipeline.storage.list_files.return_value = []

            result, _ = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIs(result, source)
            pipeline.storage.list_files.assert_called_once()

    def test_file_backed_source_skips_when_cache_is_warm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            resource = Mock()
            resource.name = "my_resource"
            cached_file = Mock()
            cached_file.file_name = "my_resource"
            source = Mock()
            source.name = "file_source"
            source.get_checkpointable_resources.return_value = []
            source.supports_storage_cache.return_value = True
            source.get_resources.return_value = [resource]
            pipeline.storage.list_files.return_value = [cached_file]

            result, _ = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIsNone(result)

    def test_all_checkpointed_resources_unchanged_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)

            res = Mock()
            res.name = "apr24"
            res.fetch_etag.return_value = '"etag-abc"'

            pipeline.checkpoints.get = Mock(
                return_value=Mock(etag='"etag-abc"')
            )

            source = Mock()
            source.name = "nhs"
            source.get_checkpointable_resources.return_value = [res]
            source.get_resources.return_value = [res]

            result, etag_cache = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIsNone(result)
            self.assertEqual(etag_cache, {})

    def test_all_checkpointed_resources_changed_returns_full_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)

            res = Mock()
            res.name = "apr24"
            res.fetch_etag.return_value = '"etag-new"'

            pipeline.checkpoints.get = Mock(
                return_value=Mock(etag='"etag-old"')
            )

            source = Mock()
            source.name = "nhs"
            source.get_checkpointable_resources.return_value = [res]
            source.get_resources.return_value = [res]

            result, etag_cache = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIs(result, source)
            self.assertEqual(etag_cache, {"apr24": '"etag-new"'})

    def test_partial_checkpoint_change_returns_filtered_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)

            res_changed = Mock()
            res_changed.name = "may24"
            res_changed.fetch_etag.return_value = '"etag-new"'

            res_unchanged = Mock()
            res_unchanged.name = "apr24"
            res_unchanged.fetch_etag.return_value = '"etag-stable"'

            def _get_checkpoint(source_name, resource_name):
                if resource_name == "apr24":
                    return Mock(etag='"etag-stable"')
                return None

            pipeline.checkpoints.get = Mock(side_effect=_get_checkpoint)

            filtered_source = Mock()
            source = Mock()
            source.name = "nhs"
            source.get_checkpointable_resources.return_value = [res_changed, res_unchanged]
            source.get_resources.return_value = [res_changed, res_unchanged]
            source.with_filtered_resources.return_value = filtered_source

            result, etag_cache = pipeline._resolve_source_to_run(source=source, force_reload=False)

            self.assertIs(result, filtered_source)
            source.with_filtered_resources.assert_called_once_with({"may24"})
            self.assertEqual(etag_cache, {"may24": '"etag-new"'})


class SaveCheckpointsTests(unittest.TestCase):
    def _make_pipeline(self, temp_dir: str) -> Pipeline:
        with patch("axiomatic_engine.core.pipeline.get_storage_adapter") as mock_storage_factory:
            with patch("axiomatic_engine.core.pipeline.get_warehouse_adapter") as mock_warehouse_factory:
                mock_storage_factory.return_value = Mock(list_files=Mock(return_value=[]))
                mock_warehouse_factory.return_value = Mock()
                settings = EngineSettings.from_env(
                    {
                        "AXIOMATIC_STORAGE_KIND": "local",
                        "AXIOMATIC_STORAGE_PATH": temp_dir,
                        "AXIOMATIC_WAREHOUSE_KIND": "duckdb",
                        "AXIOMATIC_WAREHOUSE_PATH": str(Path(temp_dir) / "analytics.duckdb"),
                        "AXIOMATIC_TRANSFORM_ENABLED": "false",
                    }
                )
                return Pipeline(settings=settings)

    def test_save_checkpoints_persists_etag_from_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            pipeline.checkpoints.save = Mock()

            res = Mock()
            res.name = "apr24"
            source = Mock()
            source.name = "nhs"
            source.get_checkpointable_resources.return_value = [res]

            pipeline._save_checkpoints(
                source=source,
                etag_cache={"apr24": '"etag-abc"'},
            )

            pipeline.checkpoints.save.assert_called_once()
            saved: object = pipeline.checkpoints.save.call_args[0][0]
            self.assertEqual(saved.source_name, "nhs")
            self.assertEqual(saved.resource_name, "apr24")
            self.assertEqual(saved.etag, '"etag-abc"')

    def test_save_checkpoints_is_noop_for_non_checkpointable_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = self._make_pipeline(temp_dir)
            pipeline.checkpoints.save = Mock()

            source = Mock()
            source.name = "file_source"
            source.get_checkpointable_resources.return_value = []

            pipeline._save_checkpoints(source=source, etag_cache={})

            pipeline.checkpoints.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
