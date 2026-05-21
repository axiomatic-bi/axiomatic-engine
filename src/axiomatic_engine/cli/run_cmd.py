"""
axiomatic-engine run — execute a pipeline from a declarative pipeline.yml.
"""
from __future__ import annotations

import logging

import click

from axiomatic_engine.cli.pipeline_config import PipelineConfigError, load_pipeline_config
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.factory import build_source


@click.command("run")
@click.option(
    "--config",
    "config_path",
    default="pipeline.yml",
    show_default=True,
    help="Path to pipeline.yml config file.",
)
@click.option(
    "--force-reload",
    is_flag=True,
    default=False,
    help="Force re-ingestion even if the warehouse already has data.",
)
@click.option(
    "--skip-transforms",
    is_flag=True,
    default=False,
    help="Run ingestion only; skip the dbt transformation stage.",
)
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Logging verbosity.",
)
def run_cmd(
    config_path: str,
    force_reload: bool,
    skip_transforms: bool,
    log_level: str,
) -> None:
    """Run a pipeline defined in a pipeline.yml config file."""

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    try:
        engine_settings, source_def = load_pipeline_config(config_path)
    except PipelineConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    if skip_transforms and engine_settings.transform.enabled:
        engine_settings = engine_settings.with_overrides(transform_enabled=False)

    source = build_source(source_def)
    pipeline = Pipeline(settings=engine_settings)
    pipeline.run(source=source, force_reload=force_reload)
