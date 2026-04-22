import argparse
import logging

from dotenv import load_dotenv

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.file.http_stream import HttpStreamSource

# Standardise logging for the run
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run cinematic-ledger ingestion with CLI overrides."
    )
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
    parser.add_argument("--force-reload", action="store_true")
    return parser.parse_args()


def main():
    args = _parse_args()
    load_dotenv()

    # 1. Setup the Source (The "What")
    imdb_datasets = {
        "title_basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
        "title_ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    }
    
    source = HttpStreamSource(
        name="imdb_bronze_ingest",
        resource_map=imdb_datasets
    )

    # 2. Setup the Engine (The "How")
    settings = EngineSettings.from_env().with_overrides(
        storage_kind=args.storage_kind,
        storage_path=args.storage_path,
        warehouse_kind=args.warehouse_kind,
        warehouse_path=args.warehouse_path,
        bronze_schema_name=args.schema_bronze,
        silver_schema_name=args.schema_silver,
        gold_schema_name=args.schema_gold,
        analytics_schema_name=args.schema_analytics,
    )
    engine = Pipeline(settings=settings)

    # 3. Execute
    print("🚀 Axiomatic Engine: Initiating IMDb Production Run...")
    engine.run(source, force_reload=args.force_reload)
    print("✅ Run Complete. You can now query your data in DuckDB.")

if __name__ == "__main__":
    main()