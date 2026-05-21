"""
axiomatic-engine CLI entry point.

Registered as a console script in pyproject.toml:
    axiomatic-engine = "axiomatic_engine.cli.main:cli"
"""
from __future__ import annotations

import click

from axiomatic_engine.cli.generate_staging_cmd import generate_staging_cmd
from axiomatic_engine.cli.init_cmd import init_cmd
from axiomatic_engine.cli.run_cmd import run_cmd


@click.group()
@click.version_option(package_name="axiomatic-engine")
def cli() -> None:
    """Axiomatic Engine — declarative data pipeline orchestration."""


cli.add_command(init_cmd, name="init")
cli.add_command(run_cmd, name="run")
cli.add_command(generate_staging_cmd, name="generate-staging")
