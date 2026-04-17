import dlt
from axiomatic_engine.contracts.warehouse import WarehouseProtocol
from axiomatic_engine.sources.base import BaseSource
import logging

LOGGER = logging.getLogger(__name__)

class Ingestor:
    """
    The Axiomatic worker responsible for executing data movement.
    
    It orchestrates the flow from a BaseSource implementation into 
     a WarehouseProtocol implementation using dlt.
    """
    
    def __init__(self, warehouse: WarehouseProtocol):
        self.warehouse = warehouse

    def run(self, source: BaseSource, dataset_name: str = "bronze"):
        """
        Executes the ingestion pipeline.
        
        Triggers dlt loading using destination config from the warehouse adapter.
        """
        LOGGER.info(f"Starting ingestion for source: {source.name}")

        pipeline = dlt.pipeline(
            pipeline_name=source.name,
            dataset_name=dataset_name
        )
        load_info = pipeline.run(
            source.to_dlt(),
            destination=self.warehouse.get_dlt_destination(),
            credentials=self.warehouse.get_dlt_credentials(),
        )
        LOGGER.info(f"Ingestion complete for {source.name}. Status: {load_info}")
        return load_info