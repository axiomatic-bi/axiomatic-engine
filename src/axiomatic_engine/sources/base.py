from __future__ import annotations
import dlt
from datetime import datetime, timezone
from typing import Iterable, Any
from axiomatic_engine.contracts.source import SourceProtocol, ResourceProtocol

class BaseResource:
    """
    Wraps a ResourceProtocol implementation to inject standardise metadata.
    
    This ensures every record produced by the engine has a consistent 
    audit trail, regardless of the underlying source technology.
    """
    def __init__(self, resource_logic: ResourceProtocol):
        self._logic = resource_logic
        self.name = resource_logic.name

    def __call__(self) -> Iterable[dict[str, Any]]:
        """
        Executes the resource logic and injects 'Axiomatic' metadata.
        Uses a generator to maintain memory efficiency for large datasets.
        """
        extraction_time = datetime.now(timezone.utc).isoformat()
        
        for record in self._logic.read():
            record["_axiomatic_extracted_at_utc"] = extraction_time
            yield record

class BaseSource:
    """
    A blueprint that converts any SourceProtocol into a dlt-compatible source.
    
    This acts as the bridge between the Axiomatic contracts and the 
    dlt framework, allowing for automated schema evolution and loading.
    """
    def __init__(self, source_logic: SourceProtocol):
        self._logic = source_logic
        self.name = source_logic.name

    def to_dlt(self):
        """
        Converts the internal logic into a native dlt source object.
        """
        def _wrap_resource(resource: ResourceProtocol):
            wrapper = BaseResource(resource)

            def _resource_iter() -> Iterable[dict[str, Any]]:
                yield from wrapper()

            _resource_iter.__name__ = resource.name
            return dlt.resource(_resource_iter, name=resource.name)

        resources = [
            _wrap_resource(res)
            for res in self._logic.get_resources()
        ]

        def _source():
            return resources

        return dlt.source(_source, name=self.name)()

    def get_resources(self) -> list[ResourceProtocol]:
        return self._logic.get_resources()