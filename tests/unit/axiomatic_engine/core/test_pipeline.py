from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import WarehouseSettings
from axiomatic_engine.core.pipeline import Pipeline


class PipelineConstructionTests(unittest.TestCase):
    def test_pipeline_initialises_with_engine_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = EngineSettings(
                storage=StorageSettings(kind="local", path=temp_dir),
                warehouse=WarehouseSettings(
                    kind="duckdb",
                    path=str(Path(temp_dir) / "analytics.duckdb"),
                ),
            )

            pipeline = Pipeline(settings=settings)

            self.assertIsNotNone(pipeline.storage)
            self.assertIsNotNone(pipeline.warehouse)
            self.assertIsNotNone(pipeline.ingestor)


if __name__ == "__main__":
    unittest.main()
