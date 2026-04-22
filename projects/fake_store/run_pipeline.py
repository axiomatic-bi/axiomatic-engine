"""
Run the Fake Store API pipeline
"""
import argparse
import logging
import os

from dotenv import load_dotenv

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.base import BaseSource
from axiomatic_engine.sources.factory import RestApiSourceDefinition, build_source
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition

DEFAULT_FAKE_STORE_BASE_URL = "https://fakestoreapi.com"
DEFAULT_LOG_LEVEL = "INFO"


def _parse_args() -> argparse.Namespace:
    default_base_url = os.getenv("FAKE_STORE_API_URL", DEFAULT_FAKE_STORE_BASE_URL)
    parser = argparse.ArgumentParser(
        description="Run Fake Store API ingestion and transformations with CLI overrides."
    )
    parser.add_argument("--base-url", default=default_base_url)
    parser.add_argument("--storage-kind", choices=["local", "gcs", "s3"], default=None)
    parser.add_argument("--storage-path", default=None)
    parser.add_argument(
        "--warehouse-kind",
        choices=["duckdb", "motherduck", "bigquery"],
        default=None,
    )
    parser.add_argument("--warehouse-path", default=None)
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


def _build_fake_store_source(base_url: str) -> BaseSource:
    resources = [
        RestApiResourceDefinition(
            name="products",
            endpoint_path="products",
            load_hints=ResourceLoadHints(
                write_disposition="merge",
                primary_key="id",
                schema_evolution_mode="auto",
            ),
        ),
        RestApiResourceDefinition(
            name="carts",
            endpoint_path="carts",
            load_hints=ResourceLoadHints(
                write_disposition="replace",
                schema_evolution_mode="auto",
            ),
        ),
        RestApiResourceDefinition(
            name="users",
            endpoint_path="users",
            load_hints=ResourceLoadHints(
                write_disposition="merge",
                primary_key="id",
                schema_evolution_mode="auto",
            ),
        ),
    ]
    definition = RestApiSourceDefinition(
        kind="rest_api",
        name="fake_store_bronze_ingest",
        base_url=base_url,
        resources=resources,
    )
    return build_source(definition=definition)


def main() -> None:
    load_dotenv()
    log_level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    args = _parse_args()

    source = _build_fake_store_source(base_url=args.base_url)

    settings = EngineSettings.from_env().with_overrides(
        storage_kind=args.storage_kind,
        storage_path=args.storage_path,
        warehouse_kind=args.warehouse_kind,
        warehouse_path=args.warehouse_path,
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

    print("Axiomatic Engine: Initiating Fake Store API run...")
    engine.run(source, force_reload=args.force_reload)
    print("Run complete.")


if __name__ == "__main__":
    main()
