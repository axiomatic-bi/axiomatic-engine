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

    def test_run_redacts_token_like_values_in_stderr(self) -> None:
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
            mock_run.return_value.stderr = (
                "connection failed: motherduck_token=abc123 "
                "MOTHERDUCK_TOKEN=xyz999 authorization: bearer verysecret"
            )

            result = adapter.run(request=request)

        self.assertEqual(result.status, "failed")
        self.assertIn("motherduck_token=[REDACTED]", result.details["stderr"])
        self.assertIn("MOTHERDUCK_TOKEN=[REDACTED]", result.details["stderr"])
        self.assertIn("authorization: bearer [REDACTED]", result.details["stderr"])

    def test_run_passes_only_allowed_environment_variables(self) -> None:
        adapter = DbtTransformationAdapter(
            project_dir=Path("./projects/fake-store/dbt"),
            profiles_dir=Path("./projects/fake-store/dbt"),
            profile_name="fake_store",
            target="dev",
            run_tests=False,
            adapter_package="dbt-duckdb",
            expected_profile_type="duckdb",
        )
        request = TransformationRequest(
            project_dir=Path("./projects/fake-store/dbt"),
            warehouse_kind="motherduck",
            environment={
                "PATH": "fake-path",
                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
                "DBT_THREADS": "4",
                "UNRELATED_SECRET": "must-not-pass",
            },
        )

        with patch(
            "axiomatic_engine.adapters.transformation.dbt_adapter.subprocess.run"
        ) as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""

            adapter.run(request=request)

        called_env = mock_run.call_args.kwargs["env"]
        self.assertEqual(called_env["PATH"], "fake-path")
        self.assertEqual(called_env["DBT_THREADS"], "4")
        self.assertEqual(called_env["MOTHERDUCK_TOKEN"], "secret-token")
        self.assertEqual(
            called_env["AXIOMATIC_DBT_ADAPTER_PACKAGE"],
            "dbt-duckdb",
        )
        self.assertNotIn("UNRELATED_SECRET", called_env)

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
