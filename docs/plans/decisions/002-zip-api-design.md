# Decision 002: Generic ZIP Archive Streaming Design

**Date**: 2026-05-20
**Status**: Accepted
**Deciders**: User, AI Assistant

## Context
NHS RTT data is distributed as CSV files within ZIP archives accessed via HTTP. The Axiomatic Engine needs to support this pattern while remaining source-agnostic.

## Decision
**Add generic archive support to `HttpFileResourceDefinition` with the following design:**

### API Design

```python
@dataclass(frozen=True)
class HttpFileResourceDefinition:
    name: str
    url: str
    delimiter: str | None = None
    compression: CompressionKind | None = None
    archive_format: Literal["zip"] | None = None  # NEW
    archive_member: str | None = None               # NEW
    progress_log_every_rows: int = DEFAULT_PROGRESS_LOG_EVERY_ROWS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    load_hints: ResourceLoadHints | None = None
```

### Key Design Principles

1. **Source-Agnostic**: The ZIP streaming capability must work for any HTTP-delivered archive containing delimited files, not just NHS data.

2. **Declarative Configuration**: All parameters (including `archive_format`) should be inferable from the URL where possible, following the existing pattern of `_infer_compression()` and `_infer_delimiter()`.

3. **Memory Efficiency**: Use streaming decompression with `io.BytesIO` to avoid writing archives to disk. The ZIP extraction feeds into the existing `_get_stream()` pipeline.

4. **Nested Path Support**: `archive_member` supports paths like `"subdir/data.csv"` for archives with internal directory structures.

5. **Chainable**: Archive extraction → compression decompression (e.g., `.csv.gz` inside `.zip`) should work seamlessly.

### Usage Example (Generic)

```python
HttpFileResourceDefinition(
    name="research_dataset",
    url="https://academic.org/data/2025/results.zip",
    archive_format="zip",  # Auto-detected from .zip extension
    archive_member="results/csv/metrics.csv",
    delimiter=",",
)
```

### Implementation Notes

- Add `_infer_archive_format()` method to auto-detect from URL (".zip" → "zip")
- Implement `_get_archive_stream()` using `zipfile.ZipFile`
- Modify `read()` to conditionally apply archive extraction before decompression

## Consequences

**Positive:**
- Generic capability benefits all future HTTP-delivered archive sources
- Consistent with existing engine patterns (auto-detection, declarative config)
- Enables NHS RTT ingestion without NHS-specific code

**Negative:**
- Slightly more complex `HttpStreamResource` logic
- Currently only ZIP format; TAR/7Z would require additional work

## Related
- [NHS Inequality v1 Plan](../current/nhs-inequality-v1.md)
- GitHub Issue: #1 (Add ZIP archive streaming to HTTP source)
