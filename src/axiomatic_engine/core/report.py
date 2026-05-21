from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

IngestionStatus = Literal["loaded", "skipped", "failed"]
TransformStatus = Literal["succeeded", "failed", "skipped"]


@dataclass
class ResourceIngestionResult:
    """
    Per-resource outcome from the ingestion stage.
    """

    name: str
    status: IngestionStatus
    row_count: int | None = None
    duration_seconds: float | None = None


@dataclass
class IngestionReport:
    """
    Summary of the ingestion stage for one source.
    """

    source_name: str
    resources: list[ResourceIngestionResult] = field(default_factory=list)
    duration_seconds: float | None = None


@dataclass
class TransformReport:
    """
    Summary of the transformation stage.
    """

    backend: str
    status: TransformStatus
    duration_seconds: float | None = None
    run_results: dict | None = None


@dataclass
class PipelineReport:
    """
    Unified run summary produced at the end of every Pipeline.run() call.
    """

    pipeline_name: str
    warehouse_label: str
    ingestion: IngestionReport | None = None
    transform: TransformReport | None = None


def format_report(report: PipelineReport) -> str:
    """
    Render a PipelineReport as a human-readable string suitable for printing
    to the terminal or writing to a log file.
    """
    lines: list[str] = []
    sep = "=" * 50
    lines.append(sep)
    lines.append(f"Axiomatic Pipeline Report — {report.pipeline_name}")
    lines.append(sep)

    if report.ingestion is not None:
        ing = report.ingestion
        lines.append("Ingestion:")
        lines.append(f"  {ing.source_name}")
        for res in ing.resources:
            parts = [f"    {res.name:<40}"]
            if res.row_count is not None:
                parts.append(f"{res.row_count:>10,} rows")
            if res.duration_seconds is not None:
                parts.append(f"  {res.duration_seconds:.1f}s")
            parts.append(f"  {res.status}")
            lines.append("".join(parts))
        if ing.duration_seconds is not None:
            lines.append(f"  Total ingestion time: {ing.duration_seconds:.1f}s")
    else:
        lines.append("Ingestion:  skipped")

    lines.append("")

    if report.transform is not None:
        tr = report.transform
        dur = f"  {tr.duration_seconds:.1f}s" if tr.duration_seconds is not None else ""
        lines.append(f"Transform:  {tr.backend} {tr.status}{dur}")
        if tr.status == "failed" and tr.run_results:
            lines.append("  dbt run_results.json:")
            results = tr.run_results.get("results", [])
            for node in results:
                node_status = node.get("status", "?")
                node_id = node.get("unique_id", "?")
                timing = node.get("execution_time")
                timing_str = f"  {timing:.1f}s" if timing is not None else ""
                if node_status in ("error", "fail"):
                    lines.append(f"    [{node_status}] {node_id}{timing_str}")
                    message = node.get("message") or ""
                    if message:
                        for msg_line in message.strip().splitlines():
                            lines.append(f"           {msg_line}")
    else:
        lines.append("Transform:  skipped")

    lines.append("")
    lines.append(f"Warehouse:  {report.warehouse_label}")
    lines.append(sep)

    return "\n".join(lines)
