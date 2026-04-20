import csv
import gzip
import io
import logging

from typing import Any, BinaryIO, IO, Iterable, Literal, cast

import requests

from axiomatic_engine.contracts.source import ResourceProtocol, SourceKind
from axiomatic_engine.sources.base import BaseSource

LOGGER = logging.getLogger(__name__)

CompressionKind = Literal["gzip", "none"]
DEFAULT_PROGRESS_LOG_EVERY_ROWS = 100_000


class HttpStreamResource(ResourceProtocol):
    """
    Implementation of ResourceProtocol for downloading delimited files over HTTP.
    """

    def __init__(
        self,
        name: str,
        url: str,
        delimiter: str | None = None,
        compression: CompressionKind | None = None,
        progress_log_every_rows: int = DEFAULT_PROGRESS_LOG_EVERY_ROWS,
    ):
        self.name = name
        self.url = url
        self.delimiter = delimiter or self._infer_delimiter(url)
        self.compression = compression or self._infer_compression(url)
        self.progress_log_every_rows = progress_log_every_rows

    @staticmethod
    def _infer_compression(url: str) -> CompressionKind:
        """
        Infer compression from URL path so resources remain declarative.
        """
        if url.lower().endswith(".gz"):
            return "gzip"
        return "none"

    @staticmethod
    def _infer_delimiter(url: str) -> str:
        """
        Infer CSV delimiter from URL extension with a safe default.
        """
        lowered = url.lower()
        if ".tsv" in lowered:
            return "\t"
        return ","

    def _get_stream(self, raw_stream: BinaryIO) -> IO[str]:
        """Helper to handle decompression based on configuration."""
        if self.compression == "gzip":
            return gzip.open(raw_stream, mode="rt", encoding="utf-8")
        return io.TextIOWrapper(raw_stream, encoding="utf-8")

    def read(self) -> Iterable[dict[str, Any]]:
        """Streams data according to the configured format."""
        LOGGER.info(
            "Streaming resource '%s' from %s (compression=%s, delimiter=%r)",
            self.name,
            self.url,
            self.compression,
            self.delimiter,
        )
        row_count = 0
        with requests.get(self.url, stream=True) as response:
            response.raise_for_status()

            with self._get_stream(cast(BinaryIO, response.raw)) as stream:
                reader = csv.DictReader(stream, delimiter=self.delimiter)
                for row in reader:
                    row_count += 1
                    if (
                        self.progress_log_every_rows > 0
                        and row_count % self.progress_log_every_rows == 0
                    ):
                        LOGGER.info(
                            "Resource '%s': processed %s rows",
                            self.name,
                            f"{row_count:,}",
                        )
                    yield row

        LOGGER.info(
            "Completed resource '%s': processed %s rows",
            self.name,
            f"{row_count:,}",
        )


class HttpStreamSource(BaseSource):
    """
    A collection of HTTP-streamed delimited file resources.
    """

    def __init__(self, name: str, resource_map: dict[str, str]):
        self.name = name
        self.kind: SourceKind = "filesystem"
        self._resource_map = resource_map
        super().__init__(source_logic=self)

    def get_resources(self) -> list[ResourceProtocol]:
        return [
            HttpStreamResource(name, url)
            for name, url in self._resource_map.items()
        ]

    def get_incremental_key(self) -> str | None:
        return None
