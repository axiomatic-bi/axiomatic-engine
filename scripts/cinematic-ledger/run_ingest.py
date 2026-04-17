import logging
from axiomatic_engine.core.pipeline import Pipeline
from axiomatic_engine.sources.filesystem import FileSystemSource

# Standardise logging for the run
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    # 1. Setup the Source (The "What")
    imdb_datasets = {
        "title_basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
        "title_ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    }
    
    source = FileSystemSource(
        name="imdb_bronze_ingest",
        resource_map=imdb_datasets
    )

    # 2. Setup the Engine (The "How")
    engine = Pipeline(
        storage_kind="local",
        storage_path="./data/raw_vault",
        warehouse_kind="duckdb",
        warehouse_path="./data/imdb_analytics.duckdb"
    )

    # 3. Execute
    print("🚀 Axiomatic Engine: Initiating IMDb Production Run...")
    engine.run(source, force_reload=True)
    print("✅ Run Complete. You can now query your data in DuckDB.")

if __name__ == "__main__":
    main()