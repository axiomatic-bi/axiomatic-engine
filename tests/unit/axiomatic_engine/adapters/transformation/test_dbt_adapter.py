from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from axiomatic_engine.adapters.transformation.dbt_adapter import DbtTransformationAdapter
from axiomatic_engine.contracts.transformation import TransformationRequest


class DbtTransformationAdapterTests(unittest.TestCase):
    def test_run_executes_run_and_test_commands(self) -> None:
        adapter = DbtTransformationAdapter(
            project_dir=Path("./projects/fake-store/dbt"),
            profiles_dir=Path("./projects/fake-store/dbt"),
            profile_name="fake_store",
            target="dev",
            run_tests=True,
            adapter_package="dbt-duckdb",
            expected_profile_type="duckdb",
        )
        request = TransformationRequest(
            project_dir=Path("./projects/fake-store/dbt"),
            warehouse_kind="motherduck",
            environment={"PATH": "fake-path"},
        )

        with patch(
            "axiomatic_engine.adapters.transformation.dbt_adapter.subprocess.run"
        ) as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""

            result = adapter.run(request=request)

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(mock_run.call_count, 2)

    def test_run_returns_failed_status_when_dbt_command_fails(self) -> None:
        adapter = DbtTransformationAdapter(
            project_dir=Path("./projects/fake-store/dbt"),
            profiles_dir=Path("./projects/fake-store/dbt"),
            profile_name="fake_store",
            target=None,
            run_tests=False,
            adapter_package="dbt-duckdb",
            expected_profile_type="duckdb",
        )
        request = TransformationRequest(
            project_dir=Path("./projects/fake-store/dbt"),
            warehouse_kind="motherduck",
            environment={"PATH": "fake-path"},
        )

        with patch(
            "axiomatic_engine.adapters.transformation.dbt_adapter.subprocess.run"
        ) as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "dbt error"

            result = adapter.run(request=request)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.details["return_code"], "1")
        self.assertEqual(result.details["stderr"], "dbt error")

    def test_run_rejects_non_motherduck_warehouse_kind(self) -> None:
        adapter = DbtTransformationAdapter(
            project_dir=Path("./projects/fake-store/dbt"),
            profiles_dir=Path("./projects/fake-store/dbt"),
            profile_name="fake_store",
            target="dev",
            run_tests=True,
            adapter_package="dbt-duckdb",
            expected_profile_type="duckdb",
        )
        request = TransformationRequest(
            project_dir=Path("./projects/fake-store/dbt"),
            warehouse_kind="duckdb",
            environment={},
        )

        with self.assertRaises(NotImplementedError):
            adapter.run(request=request)


if __name__ == "__main__":
    unittest.main()
