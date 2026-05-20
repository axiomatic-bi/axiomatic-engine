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
from axiomatic_engine.sources.factory import HttpFileSourceDefinition, build_source
from axiomatic_engine.sources.file import HttpFileResourceDefinition

DEFAULT_LOG_LEVEL = "INFO"

# NHS England RTT URL pattern
# Format: https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/{upload_year}/{upload_month}/
#         Full-CSV-data-file-{Mon}{YY}-ZIP-{size}-revised.zip
#
# NOTE: Upload path (year/month) reflects when NHS England published the data,
# NOT the data month. Revised editions for 2024-25 were published in 2025/02
# (Apr-Nov 2024) and 2025/07 (Dec 2024-Mar 2025).
#
# Archive member format: {YYYYMMDD}-RTT-{Month}-{YYYY}-full-extract-revised.csv
# where the date is the last calendar day of the data month.

RTT_RESOURCES: list[dict] = [
    {
        "month_key": "apr24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Apr24-ZIP-4M-revised.zip",
        "archive_member": "20240430-RTT-April-2024-full-extract-revised.csv",
    },
    {
        "month_key": "may24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-May24-ZIP-4M-revised.zip",
        "archive_member": "20240531-RTT-May-2024-full-extract-revised.csv",
    },
    {
        "month_key": "jun24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Jun24-ZIP-4M-revised.zip",
        "archive_member": "20240630-RTT-June-2024-full-extract-revised.csv",
    },
    {
        "month_key": "jul24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Jul24-ZIP-4M-revised.zip",
        "archive_member": "20240731-RTT-July-2024-full-extract-revised.csv",
    },
    {
        "month_key": "aug24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Aug24-ZIP-4M-revised.zip",
        "archive_member": "20240831-RTT-August-2024-full-extract-revised.csv",
    },
    {
        "month_key": "sep24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Sep24-ZIP-4M-revised.zip",
        "archive_member": "20240930-RTT-September-2024-full-extract-revised.csv",
    },
    {
        "month_key": "oct24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Oct24-ZIP-4M-revised.zip",
        "archive_member": "20241031-RTT-October-2024-full-extract-revised.csv",
    },
    {
        "month_key": "nov24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/02/Full-CSV-data-file-Nov24-ZIP-4M-revised.zip",
        "archive_member": "20241130-RTT-November-2024-full-extract-revised.csv",
    },
    {
        "month_key": "dec24",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Dec24-ZIP-4M-revised.zip",
        "archive_member": "20241231-RTT-December-2024-full-extract-revised.csv",
    },
    {
        "month_key": "jan25",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Jan25-ZIP-4M-revised.zip",
        "archive_member": "20250131-RTT-January-2025-full-extract-revised.csv",
    },
    {
        "month_key": "feb25",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Feb25-ZIP-4M-revised.zip",
        "archive_member": "20250228-RTT-February-2025-full-extract-revised.csv",
    },
    {
        "month_key": "mar25",
        "url": "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Mar25-ZIP-4M-revised.zip",
        "archive_member": "20250331-RTT-March-2025-full-extract-revised.csv",
    },
]

ALL_MONTH_KEYS: list[str] = [r["month_key"] for r in RTT_RESOURCES]


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
    parser.add_argument(
        "--months",
        nargs="+",
        metavar="MONTH_KEY",
        default=None,
        help=(
            "One or more month keys to ingest (e.g. mar25 jan25 dec24). "
            f"Valid values: {', '.join(ALL_MONTH_KEYS)}. "
            "Defaults to all 12 months."
        ),
    )
    return parser.parse_args()


def _build_rtt_source(month_keys: list[str] | None = None):
    """Build RTT source with commissioner-level data from ZIP archives.

    Args:
        month_keys: Subset of month keys to load. Defaults to all 12 months.
    """
    selected = month_keys if month_keys is not None else ALL_MONTH_KEYS
    resources = [
        HttpFileResourceDefinition(
            name=f"rtt_commissioner_{entry['month_key']}",
            url=entry["url"],
            archive_format="zip",
            archive_member=entry["archive_member"],
            delimiter=",",
            load_hints=ResourceLoadHints(
                write_disposition="replace",
                schema_evolution_mode="auto",
            ),
        )
        for entry in RTT_RESOURCES
        if entry["month_key"] in selected
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

    source = _build_rtt_source(month_keys=args.months)

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
