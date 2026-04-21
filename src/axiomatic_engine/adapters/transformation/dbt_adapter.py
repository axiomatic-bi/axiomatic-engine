from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from axiomatic_engine.contracts.transformation import (
    TransformationKind,
    TransformationProtocol,
    TransformationRequest,
    TransformationResult,
)


@dataclass(frozen=True)
class DbtTransformationAdapter(TransformationProtocol):
    """
    Execute dbt transformations through the dbt CLI.
    """

    project_dir: Path
    profiles_dir: Path
    profile_name: str
    target: str | None
    run_tests: bool
    adapter_package: str
    expected_profile_type: str
    kind: TransformationKind = "dbt"

    def run(self, request: TransformationRequest) -> TransformationResult:
        self._validate_request(request=request)
        start = perf_counter()

        environment = dict(request.environment)
        environment["AXIOMATIC_DBT_ADAPTER_PACKAGE"] = self.adapter_package
        environment["AXIOMATIC_DBT_EXPECTED_PROFILE_TYPE"] = self.expected_profile_type
        axiomatic_md_token = environment.get("AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN")
        if axiomatic_md_token and not environment.get("MOTHERDUCK_TOKEN"):
            environment["MOTHERDUCK_TOKEN"] = axiomatic_md_token

        commands: list[list[str]] = [self._build_command(subcommand="run")]
        if self.run_tests:
            commands.append(self._build_command(subcommand="test"))

        for command in commands:
            completed = subprocess.run(
                command,
                cwd=str(self.project_dir),
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                return TransformationResult(
                    backend=self.kind,
                    status="failed",
                    duration_seconds=perf_counter() - start,
                    details={
                        "command": " ".join(command),
                        "return_code": str(completed.returncode),
                        "stderr": completed.stderr.strip(),
                    },
                )

        return TransformationResult(
            backend=self.kind,
            status="succeeded",
            duration_seconds=perf_counter() - start,
            details={"commands_executed": str(len(commands))},
        )

    def _build_command(self, subcommand: str) -> list[str]:
        resolved_project_dir = str(self.project_dir.resolve())
        resolved_profiles_dir = str(self.profiles_dir.resolve())

        if shutil.which("dbt") is None:
            command = [sys.executable, "-m", "dbt.cli.main", subcommand]
        else:
            command = ["dbt", subcommand]

        command.extend(
            [
                "--project-dir",
                resolved_project_dir,
                "--profiles-dir",
                resolved_profiles_dir,
                "--profile",
                self.profile_name,
            ]
        )
        if self.target is not None:
            command.extend(["--target", self.target])
        return command

    def _validate_request(self, request: TransformationRequest) -> None:
        if request.warehouse_kind != "motherduck":
            raise NotImplementedError(
                "DbtTransformationAdapter currently supports only motherduck warehouse."
            )
