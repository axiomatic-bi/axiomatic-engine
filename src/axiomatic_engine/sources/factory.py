from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from axiomatic_engine.sources.base import BaseSource
from axiomatic_engine.sources.file.http_stream import (
    HttpFileSourceDefinition,
    HttpStreamSource,
)
from axiomatic_engine.sources.rest.base import RestApiResourceDefinition, RestApiSource


@dataclass(frozen=True)
class RestApiSourceDefinition:
    """
    Declarative definition for a REST API source collection.
    """

    kind: Literal["rest_api"] = "rest_api"
    name: str = "rest_api_source"
    base_url: str = ""
    resources: list[RestApiResourceDefinition] = field(default_factory=list)


SourceDefinition = RestApiSourceDefinition | HttpFileSourceDefinition


def build_source(definition: SourceDefinition) -> BaseSource:
    """
    Build a source implementation from a typed source definition.
    """

    if definition.kind == "rest_api":
        return RestApiSource(
            name=definition.name,
            base_url=definition.base_url,
            resources=definition.resources,
        )
    if definition.kind == "http_file":
        return HttpStreamSource.from_definition(definition=definition)
    raise ValueError(f"Unsupported source definition kind: {definition.kind}")
