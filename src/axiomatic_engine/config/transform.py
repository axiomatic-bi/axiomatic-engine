from __future__ import annotations

from dataclasses import dataclass

from axiomatic_engine.contracts.transformation import TransformationKind


@dataclass(frozen=True)
class TransformSettings:
    """
    Typed configuration for the transformation stage.
    """

    enabled: bool = False
    kind: TransformationKind = "dbt"
    dbt_project_dir: str | None = None
    dbt_profiles_dir: str | None = None
    dbt_profile_name: str | None = None
    dbt_target: str | None = None
    dbt_run_tests: bool = True


def validate_transform_settings(transform_settings: TransformSettings) -> None:
    if not transform_settings.enabled:
        return
    if transform_settings.kind == "dbt" and not transform_settings.dbt_project_dir:
        raise ValueError(
            "AXIOMATIC_DBT_PROJECT_DIR is required when transformations are enabled "
            "with AXIOMATIC_TRANSFORM_BACKEND=dbt."
        )
