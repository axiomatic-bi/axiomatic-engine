"""
Loads and validates a declarative pipeline.yml config file.

Translates the YAML structure into EngineSettings + a SourceDefinition,
which are the two objects Pipeline and build_source() expect.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.config.schema import SchemaSettings
from axiomatic_engine.config.storage import build_storage_settings
from axiomatic_engine.config.transform import TransformSettings, validate_transform_settings
from axiomatic_engine.config.warehouse import build_warehouse_settings
from axiomatic_engine.sources.factory import RestApiSourceDefinition, SourceDefinition
from axiomatic_engine.sources.file.http_stream import (
    HttpFileResourceDefinition,
    HttpFileSourceDefinition,
)
from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


def _resolve_env(value: str) -> str:
    """
    Expand ${VAR} and ${VAR:default} placeholders in a string using os.environ.
    """

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        raise ValueError(
            f"Environment variable '{var_name}' is not set and has no default "
            f"(referenced in pipeline.yml as ${{{var_name}}})."
        )

    return _ENV_VAR_RE.sub(_replace, value)


def _resolve_value(value: Any) -> Any:
    if isinstance(value, str):
        return _resolve_env(value)
    return value


class PipelineConfigError(ValueError):
    """Raised when pipeline.yml is structurally invalid."""


def load_pipeline_config(config_path: str | Path) -> tuple[EngineSettings, SourceDefinition]:
    """
    Parse a pipeline.yml file and return (EngineSettings, SourceDefinition).

    Raises PipelineConfigError for structural problems or missing required fields.
    """
    path = Path(config_path).resolve()
    if not path.exists():
        raise PipelineConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    source_def = _parse_source(raw.get("source", {}))
    engine_settings = _parse_engine_settings(raw, base_dir=path.parent)

    return engine_settings, source_def


def _parse_source(source_block: dict[str, Any]) -> SourceDefinition:
    kind = source_block.get("kind")
    if not kind:
        raise PipelineConfigError("pipeline.yml 'source' block is missing a 'kind' field.")

    name = source_block.get("name", f"{kind}_source")

    if kind == "http_file":
        return _parse_http_file_source(name, source_block)
    if kind == "rest_api":
        return _parse_rest_api_source(name, source_block)

    raise PipelineConfigError(
        f"Unsupported source kind: '{kind}'. "
        "Supported kinds: http_file, rest_api."
    )


def _parse_http_file_source(name: str, block: dict[str, Any]) -> HttpFileSourceDefinition:
    raw_resources = block.get("resources", [])
    if not raw_resources:
        raise PipelineConfigError(
            "pipeline.yml http_file source must have at least one entry under 'resources'."
        )

    resources: list[HttpFileResourceDefinition] = []
    for r in raw_resources:
        res_name = r.get("name")
        url = r.get("url")
        if not res_name:
            raise PipelineConfigError(
                "Each http_file resource must have a 'name' field."
            )
        if not url:
            raise PipelineConfigError(
                f"http_file resource '{res_name}' is missing a 'url' field."
            )
        resources.append(
            HttpFileResourceDefinition(
                name=res_name,
                url=_resolve_value(url),
                delimiter=r.get("delimiter"),
                compression=r.get("compression"),
                archive_format=r.get("archive_format"),
                archive_member=r.get("archive_member"),
            )
        )

    return HttpFileSourceDefinition(kind="http_file", name=name, resources=resources)


def _parse_rest_api_source(name: str, block: dict[str, Any]) -> RestApiSourceDefinition:
    base_url = _resolve_value(block.get("base_url", ""))
    raw_resources = block.get("resources", [])

    resources: list[RestApiResourceDefinition] = []
    for r in raw_resources:
        res_name = r.get("name")
        endpoint = r.get("endpoint", "")
        if not res_name:
            raise PipelineConfigError(
                "Each rest_api resource must have a 'name' field."
            )

        # Parse optional load_hints
        hints_block = r.get("load_hints")
        load_hints: ResourceLoadHints | None = None
        if hints_block:
            load_hints = ResourceLoadHints(
                write_disposition=hints_block.get("write_disposition"),
                primary_key=hints_block.get("primary_key"),
                schema_evolution_mode=hints_block.get("schema_evolution_mode"),
            )

        resources.append(
            RestApiResourceDefinition(
                name=res_name,
                endpoint_path=endpoint,
                load_hints=load_hints,
            )
        )

    return RestApiSourceDefinition(kind="rest_api", name=name, base_url=base_url, resources=resources)


def _parse_engine_settings(raw: dict[str, Any], base_dir: Path) -> EngineSettings:
    warehouse_block = raw.get("warehouse", {})
    schema_block = raw.get("schema", {})
    transform_block = raw.get("transform", {})

    warehouse_kind = warehouse_block.get("kind", "duckdb")
    warehouse_path_raw = warehouse_block.get("path", "./data/warehouse.duckdb")
    warehouse_path = _resolve_value(warehouse_path_raw)

    bronze = _resolve_value(schema_block.get("bronze", "${AXIOMATIC_SCHEMA_BRONZE:bronze}"))
    silver = _resolve_value(schema_block.get("silver", "${AXIOMATIC_SCHEMA_SILVER:silver}"))
    gold = _resolve_value(schema_block.get("gold", "${AXIOMATIC_SCHEMA_GOLD:gold}"))

    transform_enabled = transform_block.get("enabled", False)
    dbt_project_dir_raw = transform_block.get("dbt_project_dir")
    dbt_profiles_dir_raw = transform_block.get("dbt_profiles_dir")
    dbt_profile_name = transform_block.get("dbt_profile_name")

    dbt_project_dir: str | None = None
    dbt_profiles_dir: str | None = None

    if dbt_project_dir_raw:
        resolved = Path(dbt_project_dir_raw)
        dbt_project_dir = str(
            resolved if resolved.is_absolute() else (base_dir / resolved).resolve()
        )
    if dbt_profiles_dir_raw:
        resolved = Path(dbt_profiles_dir_raw)
        dbt_profiles_dir = str(
            resolved if resolved.is_absolute() else (base_dir / resolved).resolve()
        )

    transform_settings = TransformSettings(
        enabled=bool(transform_enabled),
        kind="dbt",
        dbt_project_dir=dbt_project_dir,
        dbt_profiles_dir=dbt_profiles_dir,
        dbt_profile_name=dbt_profile_name,
    )
    validate_transform_settings(transform_settings)

    return EngineSettings(
        storage=build_storage_settings(kind="local", path="./data/raw_vault"),
        warehouse=build_warehouse_settings(
            kind=warehouse_kind,
            path=warehouse_path,
        ),
        schema=SchemaSettings(bronze=bronze, silver=silver, gold=gold),
        transform=transform_settings,
    )
