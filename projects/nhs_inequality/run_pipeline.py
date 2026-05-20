"""
Run the NHS Inequality RTT pipeline

Ingests Referral to Treatment (RTT) waiting times data from NHS England,
staging commissioner-level data for inequality analysis.
"""
import argparse
import logging
import os

from dotenv import load_dotenv

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.base import BaseSource
from axiomatic_engine.sources.factory import HttpFileSourceDefinition, build_source
from axiomatic_engine.sources.file import HttpFileResourceDefinition

DEFAULT_LOG_LEVEL = "INFO"

# NHS England RTT URL pattern
# Format: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/{year}/{month}/
#         Full-CSV-data-file-{Mon}{YY}-ZIP-{size}-revised.zip
RTT_MAR_2025_URL = (
    "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/"
    "Full-CSV-data-file-Mar25-ZIP-4M-revised.zip"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NHS RTT ingestion and transformations with CLI overrides."
    )
    parser.add_argument("--storage-kind", choices=["local", "gcs", "s3"], default=None)
    parser.add_argument("--storage-path", default=None)
    parser.add_argument(
        "--warehouse-kind",
        choices=["duckdb", "motherduck", "bigquery"],
        default=None,
    )
    parser.add_argument("--warehouse-path", default=None)
    parser.add_argument("--dlt-pipelines-dir", default=None)
    parser.add_argument("--schema-bronze", default=None)
    parser.add_argument("--schema-silver", default=None)
    parser.add_argument("--schema-gold", default=None)
    parser.add_argument("--schema-analytics", default=None)
    parser.add_argument(
        "--transform-backend",
        choices=["dbt"],
        default=None,
    )
    parser.add_argument("--dbt-project-dir", default=None)
    parser.add_argument("--dbt-profiles-dir", default=None)
    parser.add_argument("--dbt-profile-name", default=None)
    parser.add_argument("--dbt-target", default=None)

    transform_group = parser.add_mutually_exclusive_group()
    transform_group.add_argument(
        "--run-transforms",
        dest="transform_enabled",
        action="store_true",
    )
    transform_group.add_argument(
        "--skip-transforms",
        dest="transform_enabled",
        action="store_false",
    )
    parser.set_defaults(transform_enabled=None)

    dbt_tests_group = parser.add_mutually_exclusive_group()
    dbt_tests_group.add_argument(
        "--dbt-run-tests",
        dest="dbt_run_tests",
        action="store_true",
    )
    dbt_tests_group.add_argument(
        "--dbt-skip-tests",
        dest="dbt_run_tests",
        action="store_false",
    )
    parser.set_defaults(dbt_run_tests=None)

    parser.add_argument("--force-reload", action="store_true")
    return parser.parse_args()


def _build_rtt_source() -> BaseSource:
    """Build RTT source with commissioner-level data from ZIP archive."""
    resources = [
        HttpFileResourceDefinition(
            name="rtt_commissioner_mar25",
            url=RTT_MAR_2025_URL,
            archive_format="zip",  # Auto-detected if URL ends with .zip
            archive_member="20250331-RTT-March-2025-full-extract-revised.csv",
            delimiter=",",
            load_hints=ResourceLoadHints(
                write_disposition="replace",
                schema_evolution_mode="auto",
            ),
        ),
    ]
    definition = HttpFileSourceDefinition(
        kind="http_file",
        name="nhs_rtt_bronze_ingest",
        resources=resources,
    )
    return build_source(definition=definition)


def main() -> None:
    load_dotenv()
    log_level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    args = _parse_args()

    source = _build_rtt_source()

    settings = EngineSettings.from_env().with_overrides(
        storage_kind=args.storage_kind,
        storage_path=args.storage_path,
        warehouse_kind=args.warehouse_kind,
        warehouse_path=args.warehouse_path,
        dlt_pipelines_dir=args.dlt_pipelines_dir,
        bronze_schema_name=args.schema_bronze,
        silver_schema_name=args.schema_silver,
        gold_schema_name=args.schema_gold,
        analytics_schema_name=args.schema_analytics,
        transform_enabled=args.transform_enabled,
        transform_kind=args.transform_backend,
        dbt_project_dir=args.dbt_project_dir,
        dbt_profiles_dir=args.dbt_profiles_dir,
        dbt_profile_name=args.dbt_profile_name,
        dbt_target=args.dbt_target,
        dbt_run_tests=args.dbt_run_tests,
    )
    engine = Pipeline(settings=settings)

    print("Axiomatic Engine: Initiating NHS RTT pipeline run...")
    engine.run(source, force_reload=args.force_reload)
    print("Run complete.")


if __name__ == "__main__":
    main()
