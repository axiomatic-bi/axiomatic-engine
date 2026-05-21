from __future__ import annotations

import csv
from dataclasses import dataclass, field
import gzip
import io
import logging
from urllib.parse import urlparse
import zipfile

from typing import Any, BinaryIO, IO, Iterable, Literal, cast

import requests

from axiomatic_engine.contracts.source import (
    CheckpointableResource,
    ResourceLoadHints,
    ResourceProtocol,
    SourceKind,
)
from axiomatic_engine.sources.base import BaseSource

LOGGER = logging.getLogger(__name__)

CompressionKind = Literal["gzip", "none"]
ArchiveFormatKind = Literal["zip"]
DEFAULT_PROGRESS_LOG_EVERY_ROWS = 100_000
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class HttpFileResourceDefinition:
    """
    Declarative definition for one HTTP-delivered file resource.
    """

    name: str
    url: str
    delimiter: str | None = None
    compression: CompressionKind | None = None
    archive_format: ArchiveFormatKind | None = None
    archive_member: str | None = None
    progress_log_every_rows: int = DEFAULT_PROGRESS_LOG_EVERY_ROWS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    load_hints: ResourceLoadHints | None = None


@dataclass(frozen=True)
class HttpFileSourceDefinition:
    """
    Declarative definition for an HTTP file source collection.
    """

    kind: Literal["http_file"] = "http_file"
    name: str = "http_file_source"
    resources: list[HttpFileResourceDefinition] = field(default_factory=list)


class HttpStreamResource(ResourceProtocol):
    """
    Implementation of ResourceProtocol for downloading delimited files over HTTP.
    Supports archive extraction (e.g., ZIP) and compression (e.g., gzip).
    """

    def __init__(
        self,
        name: str,
        url: str,
        delimiter: str | None = None,
        compression: CompressionKind | None = None,
        archive_format: ArchiveFormatKind | None = None,
        archive_member: str | None = None,
        progress_log_every_rows: int = DEFAULT_PROGRESS_LOG_EVERY_ROWS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        load_hints: ResourceLoadHints | None = None,
    ) -> None:
        self.name = name
        self.url = url
        self.delimiter = delimiter or self._infer_delimiter(url)
        self.compression = compression or self._infer_compression(url)
        self.archive_format = archive_format or self._infer_archive_format(url)
        self.archive_member = archive_member
        self.progress_log_every_rows = progress_log_every_rows
        self.timeout_seconds = timeout_seconds
        self._load_hints = load_hints

    def get_load_hints(self) -> ResourceLoadHints | None:
        return self._load_hints

    @staticmethod
    def _infer_compression(url: str) -> CompressionKind:
        """
        Infer compression from URL path so resources remain declarative.
        """
        path = urlparse(url).path.lower()
        if path.endswith(".gz"):
            return "gzip"
        return "none"

    @staticmethod
    def _infer_delimiter(url: str) -> str:
        """
        Infer CSV delimiter from URL extension with a safe default.
        """
        lowered = urlparse(url).path.lower()
        if ".tsv" in lowered:
            return "\t"
        return ","

    @staticmethod
    def _infer_archive_format(url: str) -> ArchiveFormatKind | None:
        """
        Infer archive format from URL path so resources remain declarative.
        Returns None if URL does not indicate an archive.
        """
        path = urlparse(url).path.lower()
        if path.endswith(".zip"):
            return "zip"
        return None

    def _get_stream(self, raw_stream: BinaryIO) -> IO[str]:
        """Helper to handle decompression based on configuration."""
        if self.compression == "gzip":
            return gzip.open(raw_stream, mode="rt", encoding="utf-8")
        return io.TextIOWrapper(raw_stream, encoding="utf-8")

    def _extract_from_archive(self, raw_bytes: bytes) -> BinaryIO:
        """
        Extract a member file from an archive into a BytesIO stream.
        Supports ZIP format; extensible for tar/7z in future.
        """
        if self.archive_format == "zip":
            return self._extract_from_zip(raw_bytes)
        raise ValueError(f"Unsupported archive format: {self.archive_format}")

    def _extract_from_zip(self, raw_bytes: bytes) -> BinaryIO:
        """
        Extract a specific member from a ZIP archive.
        If archive_member is not specified, extracts the first file found.
        """
        zip_buffer = io.BytesIO(raw_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            if self.archive_member:
                member_name = self.archive_member
            else:
                # Default to first file in archive
                member_list = zf.namelist()
                if not member_list:
                    raise ValueError(f"ZIP archive at {self.url} is empty")
                member_name = member_list[0]

            member_data = zf.read(member_name)
            return io.BytesIO(member_data)

    def fetch_etag(self) -> str | None:
        """
        Perform a cheap HTTP HEAD request and return a cache token.

        Returns the ETag header value if present, falling back to
        Last-Modified, or None if neither is available.  Used by the
        checkpoint system to decide whether to skip ingestion.

        Retries transient failures once after a short delay.
        """
        import time

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.head(
                    self.url, timeout=self.timeout_seconds, allow_redirects=True
                )
                response.raise_for_status()

                etag = response.headers.get("ETag")
                if etag:
                    return etag
                last_modified = response.headers.get("Last-Modified")
                if last_modified:
                    return last_modified
                return None

            except requests.RequestException as exc:
                if attempt < max_retries - 1:
                    LOGGER.debug(
                        "HEAD request failed for '%s' (attempt %d/%d): %s. Retrying...",
                        self.name,
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    time.sleep(0.5 * (attempt + 1))  # 0.5s, then 1.0s
                else:
                    LOGGER.warning(
                        "HEAD request failed for '%s' after %d attempts (%s). Treating as changed.",
                        self.name,
                        max_retries,
                        exc,
                    )
                    return None
        return None

    def read(self) -> Iterable[dict[str, Any]]:
        """Streams data according to the configured format."""
        LOGGER.info(
            "Streaming resource '%s' from %s (archive_format=%s, compression=%s, delimiter=%r)",
            self.name,
            self.url,
            self.archive_format,
            self.compression,
            self.delimiter,
        )
        row_count = 0
        with requests.get(self.url, stream=True, timeout=self.timeout_seconds) as response:
            response.raise_for_status()

            # Handle archive extraction if needed
            if self.archive_format:
                # For archives, we need to buffer to extract
                raw_bytes = response.content
                raw_stream = self._extract_from_archive(raw_bytes)
            else:
                raw_stream = cast(BinaryIO, response.raw)

            with self._get_stream(raw_stream) as stream:
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

    def __init__(self, name: str, resource_map: dict[str, str]) -> None:
        self.name = name
        self.kind: SourceKind = "http_file"
        self._resource_map = resource_map
        super().__init__(source_logic=self)

    @classmethod
    def from_definition(cls, definition: HttpFileSourceDefinition) -> HttpStreamSource:
        resources: list[ResourceProtocol] = [
            HttpStreamResource(
                name=resource.name,
                url=resource.url,
                delimiter=resource.delimiter,
                compression=resource.compression,
                archive_format=resource.archive_format,
                archive_member=resource.archive_member,
                progress_log_every_rows=resource.progress_log_every_rows,
                timeout_seconds=resource.timeout_seconds,
                load_hints=resource.load_hints,
            )
            for resource in definition.resources
        ]
        return cls._from_resources(name=definition.name, resources=resources)

    def get_resources(self) -> list[ResourceProtocol]:
        prebuilt_resources = getattr(self, "_resources", None)
        if prebuilt_resources is not None:
            return cast(list[ResourceProtocol], prebuilt_resources)
        return [
            HttpStreamResource(name, url)
            for name, url in self._resource_map.items()
        ]

    @classmethod
    def _from_resources(
        cls, name: str, resources: list[ResourceProtocol]
    ) -> HttpStreamSource:
        """
        Private constructor that builds an HttpStreamSource from a pre-built
        resource list, bypassing the resource_map path entirely.
        """
        instance = cls.__new__(cls)
        instance.name = name
        instance.kind = "http_file"
        instance._resource_map = {}
        instance._resources = resources
        BaseSource.__init__(instance, source_logic=instance)
        return instance

    def with_filtered_resources(self, names: set[str]) -> HttpStreamSource:
        """
        Return a new HttpStreamSource containing only the resources whose
        names appear in *names*.  Used by the checkpoint system to run dlt
        only over resources that have changed since the last load.
        """
        kept = [r for r in self.get_resources() if r.name in names]
        return HttpStreamSource._from_resources(name=self.name, resources=kept)

    def get_checkpointable_resources(self) -> list[CheckpointableResource]:
        return [
            r for r in self.get_resources() if isinstance(r, HttpStreamResource)
        ]

    def supports_storage_cache(self) -> bool:
        return False

    def get_incremental_key(self) -> str | None:
        return None
