from __future__ import annotations

import unittest

from axiomatic_engine.core.report import (
    IngestionReport,
    PipelineReport,
    ResourceIngestionResult,
    TransformReport,
    format_report,
)


class FormatReportTests(unittest.TestCase):
    def test_skipped_ingestion_shows_skipped_label(self) -> None:
        report = PipelineReport(
            pipeline_name="my_source",
            warehouse_label="DuckDB at ./data/warehouse.duckdb",
            ingestion=None,
            transform=None,
        )
        output = format_report(report)
        self.assertIn("Ingestion:  skipped", output)
        self.assertIn("Transform:  skipped", output)
        self.assertIn("DuckDB at ./data/warehouse.duckdb", output)

    def test_loaded_resources_appear_in_output(self) -> None:
        report = PipelineReport(
            pipeline_name="nhs",
            warehouse_label="DuckDB at ./data/warehouse.duckdb",
            ingestion=IngestionReport(
                source_name="nhs_rtt",
                resources=[
                    ResourceIngestionResult(
                        name="apr24",
                        status="loaded",
                        row_count=185_101,
                        duration_seconds=12.3,
                    ),
                    ResourceIngestionResult(
                        name="may24",
                        status="skipped",
                    ),
                ],
                duration_seconds=13.0,
            ),
            transform=None,
        )
        output = format_report(report)
        self.assertIn("apr24", output)
        self.assertIn("185,101", output)
        self.assertIn("loaded", output)
        self.assertIn("may24", output)
        self.assertIn("skipped", output)
        self.assertIn("Total ingestion time: 13.0s", output)

    def test_transform_success_shows_duration(self) -> None:
        report = PipelineReport(
            pipeline_name="my_source",
            warehouse_label="DuckDB at ./data/warehouse.duckdb",
            ingestion=None,
            transform=TransformReport(
                backend="dbt",
                status="succeeded",
                duration_seconds=45.2,
            ),
        )
        output = format_report(report)
        self.assertIn("dbt succeeded", output)
        self.assertIn("45.2s", output)

    def test_transform_failure_surfaces_run_results(self) -> None:
        run_results = {
            "results": [
                {
                    "unique_id": "model.my_project.stg_nhs",
                    "status": "error",
                    "execution_time": 1.5,
                    "message": "column 'period' does not exist",
                }
            ]
        }
        report = PipelineReport(
            pipeline_name="my_source",
            warehouse_label="DuckDB at ./data/warehouse.duckdb",
            ingestion=None,
            transform=TransformReport(
                backend="dbt",
                status="failed",
                duration_seconds=2.1,
                run_results=run_results,
            ),
        )
        output = format_report(report)
        self.assertIn("dbt failed", output)
        self.assertIn("model.my_project.stg_nhs", output)
        self.assertIn("column 'period' does not exist", output)

    def test_pipeline_name_and_warehouse_in_header(self) -> None:
        report = PipelineReport(
            pipeline_name="fake_store",
            warehouse_label="MotherDuck database md:analytics",
            ingestion=None,
            transform=None,
        )
        output = format_report(report)
        self.assertIn("fake_store", output)
        self.assertIn("MotherDuck database md:analytics", output)

    def test_resource_without_row_count_renders_cleanly(self) -> None:
        report = PipelineReport(
            pipeline_name="test",
            warehouse_label="DuckDB at ./data/warehouse.duckdb",
            ingestion=IngestionReport(
                source_name="test_src",
                resources=[
                    ResourceIngestionResult(name="res_a", status="loaded"),
                ],
            ),
            transform=None,
        )
        output = format_report(report)
        self.assertIn("res_a", output)
        self.assertIn("loaded", output)
        self.assertNotIn("rows", output)


if __name__ == "__main__":
    unittest.main()
