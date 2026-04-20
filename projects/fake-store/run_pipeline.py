"""
Run the Fake Store API pipeline
"""
import argparse
import logging

from dotenv import load_dotenv

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition, RestApiSource

# Standardise logging for the run
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_FAKE_STORE_BASE_URL = "https://fakestoreapi.com"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Fake Store API ingestion with CLI overrides."
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
    parser.add_argument("--force-reload", action="store_true")
    return parser.parse_args()


def _build_fake_store_source(base_url: str) -> RestApiSource:
    resources = [
        RestApiResourceDefinition(name="products", endpoint_path="products"),
        RestApiResourceDefinition(name="carts", endpoint_path="carts"),
        RestApiResourceDefinition(name="users", endpoint_path="users"),
    ]
    return RestApiSource(
        name="fake_store_bronze_ingest",
        base_url=base_url,
        resources=resources,
    )


def main():
    args = _parse_args()
    load_dotenv()

    source = _build_fake_store_source(base_url=args.base_url)

    settings = EngineSettings.from_env().with_overrides(
        storage_kind=args.storage_kind,
        storage_path=args.storage_path,
        warehouse_kind=args.warehouse_kind,
        warehouse_path=args.warehouse_path,
        warehouse_schema_name=args.warehouse_schema,
    )
    engine = Pipeline(settings=settings)

    print("Axiomatic Engine: Initiating Fake Store API run...")
    engine.run(source, force_reload=args.force_reload)
    print("Run complete. You can now query your data in DuckDB.")


if __name__ == "__main__":
    main()
