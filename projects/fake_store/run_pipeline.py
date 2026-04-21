"""
Run the Fake Store API pipeline
"""
import argparse
import logging

from dotenv import load_dotenv

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.contracts.source import ResourceLoadHints
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition, RestApiSource

# Standardise logging for the run
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_FAKE_STORE_BASE_URL = "https://fakestoreapi.com"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Fake Store API ingestion and transformations with CLI overrides."
    )
    parser.add_argument("--base-url", default=DEFAULT_FAKE_STORE_BASE_URL)
    parser.add_argument("--storage-kind", choices=["local", "gcs", "s3"], default=None)
    parser.add_argument("--storage-path", default=None)
    parser.add_argument(
        "--warehouse-kind",
        choices=["duckdb", "motherduck", "bigquery"],
        default=None,
    )
    parser.add_argument("--warehouse-path", default=None)
    parser.add_argument("--warehouse-schema", default=None)
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


def _build_fake_store_source(base_url: str) -> RestApiSource:
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
    return RestApiSource(
        name="fake_store_bronze_ingest",
        base_url=base_url,
        resources=resources,
    )


def main() -> None:
    args = _parse_args()
    load_dotenv()

    source = _build_fake_store_source(base_url=args.base_url)

    settings = EngineSettings.from_env().with_overrides(
        storage_kind=args.storage_kind,
        storage_path=args.storage_path,
        warehouse_kind=args.warehouse_kind,
        warehouse_path=args.warehouse_path,
        warehouse_schema_name=args.warehouse_schema,
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
