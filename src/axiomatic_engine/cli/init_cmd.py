"""
axiomatic-engine init — scaffold a new client project directory.
"""
from __future__ import annotations

from pathlib import Path

import click

from axiomatic_engine.cli.templates import minimal as t


def _write(path: Path, content: str, *, exist_ok: bool = False) -> None:
    if path.exists() and not exist_ok:
        click.echo(f"  skip  {path}  (already exists)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    click.echo(f"  create  {path}")


@click.command("init")
@click.option(
    "--project",
    required=True,
    help="Project name (used as directory name and dbt profile name).",
)
@click.option(
    "--template",
    default="minimal",
    show_default=True,
    type=click.Choice(["minimal"]),
    help="Scaffold template to use.",
)
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    help="Parent directory in which to create the project folder.",
)
def init_cmd(project: str, template: str, output_dir: str) -> None:
    """Scaffold a new axiomatic-engine client project."""

    root = Path(output_dir) / project

    if root.exists():
        raise click.ClickException(
            f"Directory '{root}' already exists. "
            "Choose a different --project name or --output-dir."
        )

    click.echo(f"\nScaffolding project '{project}' in {root.resolve()}\n")

    _write(root / "pipeline.yml", t.pipeline_yml(project))
    _write(root / "pyproject.toml", t.pyproject_toml(project))
    _write(root / "env-template", t.env_template(project))
    _write(root / ".gitignore", t.gitignore())
    _write(root / "README.md", t.readme(project))

    _write(root / "dbt_project" / "dbt_project.yml", t.dbt_project_yml(project))
    _write(root / "dbt_project" / "profiles.yml", t.dbt_profiles_yml(project))
    _write(root / "dbt_project" / "models" / "sources.yml", t.sources_yml(project))
    (root / "dbt_project" / "models" / "silver").mkdir(parents=True, exist_ok=True)
    (root / "dbt_project" / "models" / "gold").mkdir(parents=True, exist_ok=True)

    _write(root / ".ai" / "context.md", t.ai_context_md(project))
    _write(root / ".ai" / "checklist.md", t.ai_checklist_md(project))
    _write(root / ".ai" / "reference.md", t.ai_reference_md(project))

    click.echo(
        f"\nDone. Next steps:\n"
        f"  1. cd {root}\n"
        f"  2. cp env-template .env  — fill in warehouse path and credentials\n"
        f"  3. Edit pipeline.yml     — add your source URLs\n"
        f"  4. Edit .ai/context.md   — describe the project for AI assistants\n"
        f"  5. axiomatic-engine run --config pipeline.yml\n"
    )
