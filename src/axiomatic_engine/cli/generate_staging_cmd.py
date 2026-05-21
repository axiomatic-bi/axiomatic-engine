"""
axiomatic-engine generate-staging — introspect a bronze table and emit a silver staging model.
"""
from __future__ import annotations

import difflib
import logging
from pathlib import Path

import click

from axiomatic_engine.adapters.factory import get_warehouse_adapter
from axiomatic_engine.cli.pipeline_config import PipelineConfigError, load_pipeline_config
from axiomatic_engine.cli.staging_generator import generate_staging_sql

LOGGER = logging.getLogger(__name__)


@click.command("generate-staging")
@click.option(
    "--config",
    "config_path",
    default="pipeline.yml",
    show_default=True,
    help="Path to pipeline.yml config file.",
)
@click.option(
    "--source",
    "source_name",
    required=True,
    help="Source name as declared in pipeline.yml (source.name).",
)
@click.option(
    "--resource",
    "resource_name",
    default=None,
    help=(
        "Resource name within the source. "
        "If omitted, generates a model for every resource in the source."
    ),
)
@click.option(
    "--diff",
    "diff_only",
    is_flag=True,
    default=False,
    help="Show a diff against the existing file instead of overwriting it.",
)
@click.option(
    "--output-dir",
    default=None,
    help=(
        "Directory to write the staging model(s) into. "
        "Defaults to <dbt_project_dir>/models/silver/."
    ),
)
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Logging verbosity.",
)
def generate_staging_cmd(
    config_path: str,
    source_name: str,
    resource_name: str | None,
    diff_only: bool,
    output_dir: str | None,
    log_level: str,
) -> None:
    """Introspect a bronze table and generate a silver staging dbt model."""

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    try:
        engine_settings, source_def = load_pipeline_config(config_path)
    except PipelineConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    if source_def.name != source_name:
        raise click.ClickException(
            f"Source '{source_name}' not found in {config_path}. "
            f"Declared source name is '{source_def.name}'."
        )

    resources = list(source_def.resources)
    if resource_name is not None:
        resources = [r for r in resources if r.name == resource_name]
        if not resources:
            raise click.ClickException(
                f"Resource '{resource_name}' not found in source '{source_name}'."
            )

    output_path = _resolve_output_dir(output_dir, engine_settings)

    warehouse = get_warehouse_adapter(engine_settings.warehouse)
    bronze_schema = engine_settings.schema.bronze

    generated: list[Path] = []

    for resource in resources:
        table = resource.name
        LOGGER.info("Introspecting %s.%s …", bronze_schema, table)

        try:
            columns = warehouse.introspect_schema(schema=bronze_schema, table=table)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

        sql = generate_staging_sql(
            source_name=source_name,
            table_name=table,
            columns=columns,
        )

        dest = output_path / f"stg_{table}.sql"

        if diff_only:
            _show_diff(dest, sql)
        else:
            _write_model(dest, sql)
            generated.append(dest)

    if not diff_only and generated:
        click.echo(
            f"\nGenerated {len(generated)} staging model(s) in {output_path}.\n"
            "Review the files — columns marked with TODO need manual type verification."
        )


def _resolve_output_dir(output_dir: str | None, engine_settings: object) -> Path:
    if output_dir:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    dbt_project_dir = getattr(engine_settings.transform, "dbt_project_dir", None)  # type: ignore[union-attr]
    if dbt_project_dir:
        path = Path(dbt_project_dir) / "models" / "silver"
        path.mkdir(parents=True, exist_ok=True)
        return path

    path = Path("dbt_project") / "models" / "silver"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_model(dest: Path, sql: str) -> None:
    existed = dest.exists()
    dest.write_text(sql, encoding="utf-8")
    verb = "overwrite" if existed else "create "
    click.echo(f"  {verb}  {dest}")


def _show_diff(dest: Path, new_sql: str) -> None:
    if not dest.exists():
        click.echo(f"  (new)  {dest}")
        click.echo(new_sql)
        return

    old_lines = dest.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = new_sql.splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(dest),
            tofile=f"{dest} (regenerated)",
        )
    )
    if diff:
        click.echo("".join(diff))
    else:
        click.echo(f"  no diff  {dest}")
