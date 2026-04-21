from __future__ import annotations
import dlt
from datetime import datetime, timezone
from typing import Any, Iterable, cast
from axiomatic_engine.contracts.source import ResourceLoadHints, ResourceProtocol, SourceProtocol

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
        schema_evolution_map: dict[str, str] = {
            "auto": "evolve",
            "strict": "freeze",
            "discard": "discard_value",
        }

        def _get_resource_load_hints(resource: ResourceProtocol) -> ResourceLoadHints | None:
            get_load_hints = getattr(resource, "get_load_hints", None)
            if callable(get_load_hints):
                return cast(ResourceLoadHints | None, get_load_hints())
            return None

        def _build_resource_kwargs(load_hints: ResourceLoadHints | None) -> dict[str, Any]:
            if load_hints is None:
                return {}

            if (
                load_hints.write_disposition == "merge"
                and load_hints.primary_key in (None, "", [])
            ):
                raise ValueError(
                    "Resource configured with merge disposition must provide primary_key."
                )

            resource_kwargs: dict[str, Any] = {}
            if load_hints.write_disposition is not None:
                resource_kwargs["write_disposition"] = load_hints.write_disposition
            if load_hints.primary_key is not None:
                resource_kwargs["primary_key"] = load_hints.primary_key
            if load_hints.schema_evolution_mode is not None:
                resource_kwargs["schema_contract"] = schema_evolution_map[
                    load_hints.schema_evolution_mode
                ]
            return resource_kwargs

        def _wrap_resource(resource: ResourceProtocol):
            wrapper = BaseResource(resource)
            load_hints = _get_resource_load_hints(resource)
            resource_kwargs = _build_resource_kwargs(load_hints)

            def _resource_iter() -> Iterable[dict[str, Any]]:
                yield from wrapper()

            _resource_iter.__name__ = resource.name
            return dlt.resource(_resource_iter, name=resource.name, **resource_kwargs)

        resources = [
            _wrap_resource(res)
            for res in self._logic.get_resources()
        ]

        def _source():
            return resources

        return dlt.source(_source, name=self.name)()

    def get_resources(self) -> list[ResourceProtocol]:
        return self._logic.get_resources()