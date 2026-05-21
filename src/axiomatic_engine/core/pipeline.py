from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from axiomatic_engine.adapters.factory import (
    get_storage_adapter,
    get_transformation_adapter,
    get_warehouse_adapter,
)
from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.contracts.warehouse import WarehouseKind
from axiomatic_engine.core.checkpoints import CheckpointStore, ResourceCheckpoint
from axiomatic_engine.core.ingestion import Ingestor
from axiomatic_engine.core.report import (
    IngestionReport,
    PipelineReport,
    ResourceIngestionResult,
    TransformReport,
    format_report,
)
from axiomatic_engine.core.transformation import Transformer
from axiomatic_engine.sources.base import BaseSource

LOGGER = logging.getLogger(__name__)


class Pipeline:
    """
    The central orchestrator of the Axiomatic Engine.

    It manages the ingestion and optional transformation stages.
    """

    def __init__(self, settings: EngineSettings) -> None:
        self.storage = get_storage_adapter(settings=settings.storage)
        self.warehouse = get_warehouse_adapter(settings=settings.warehouse)
        self.warehouse_kind: WarehouseKind = settings.warehouse.kind
        self.warehouse_path = settings.warehouse.path
        self.schema_settings = settings.schema
        self.ingestor = Ingestor(
            warehouse=self.warehouse,
            dlt_pipelines_dir=settings.dlt_pipelines_dir,
        )
        self.transform_settings = settings.transform
        self.transformer: Transformer | None = None

        if self.transform_settings.enabled:
            transformation_adapter = get_transformation_adapter(
                transform_settings=self.transform_settings,
                warehouse_settings=settings.warehouse,
            )
            dbt_project_dir = self.transform_settings.dbt_project_dir
            if dbt_project_dir is None:
                raise ValueError("dbt_project_dir must be set before running transformations.")
            self.transformer = Transformer(
                adapter=transformation_adapter,
                warehouse_kind=self.warehouse_kind,
                project_dir=dbt_project_dir,
            )

        self.checkpoints = CheckpointStore(warehouse=self.warehouse)
        self.checkpoints.initialise()

    def _existing_storage_resource_names(self) -> set[str]:
        names: set[str] = set()
        for file_ref in self.storage.list_files():
            names.add(file_ref.file_name)
            names.add(Path(file_ref.file_name).stem)
        return names

    def _check_checkpointable_resources(
        self, source: BaseSource
    ) -> dict[str, str | None]:
        """
        For each checkpointable resource, do a cheap ETag fetch and compare
        against the stored checkpoint.

        Returns a dict mapping resource_name -> current_etag for resources
        that are new or have changed.  Unchanged resources are omitted.
        Caching the ETags here avoids a second HEAD request in _save_checkpoints.
        """
        changed: dict[str, str | None] = {}
        for resource in source.get_checkpointable_resources():
            current_etag = resource.fetch_etag()
            checkpoint = self.checkpoints.get(
                source_name=source.name,
                resource_name=resource.name,
            )

            if checkpoint is None:
                LOGGER.info(
                    "Resource '%s' has no checkpoint. Will ingest.", resource.name
                )
                changed[resource.name] = current_etag
            elif current_etag is None:
                LOGGER.info(
                    "Resource '%s' has no ETag from server. Will ingest.", resource.name
                )
                changed[resource.name] = None
            elif checkpoint.etag != current_etag:
                LOGGER.info(
                    "Resource '%s' ETag changed (%s -> %s). Will ingest.",
                    resource.name,
                    checkpoint.etag,
                    current_etag,
                )
                changed[resource.name] = current_etag
            else:
                LOGGER.info(
                    "Resource '%s' unchanged (ETag=%s). Skipping.",
                    resource.name,
                    current_etag,
                )

        return changed

    def run(self, source: BaseSource, force_reload: bool = False) -> PipelineReport:
        """
        The main execution loop.

        Returns a PipelineReport summarising ingestion and transformation outcomes.
        """
        LOGGER.info("Initialising Axiomatic Pipeline: %s", source.name)

        source_to_run, etag_cache = self._resolve_source_to_run(
            source=source, force_reload=force_reload
        )

        ingestion_report: IngestionReport | None = None
        if source_to_run is not None:
            LOGGER.info("Ingesting data into the warehouse")
            ingestion_report = self.ingestor.run(
                source=source_to_run,
                dataset_name=self.schema_settings.bronze,
            )
            self._save_checkpoints(source=source_to_run, etag_cache=etag_cache)
            LOGGER.info("Ingestion completed successfully.")
            ingestion_report = self._merge_skipped_resources(
                source=source,
                source_to_run=source_to_run,
                ingestion_report=ingestion_report,
            )
        else:
            LOGGER.info("Warehouse is already up to date. Skipping load.")

        transform_report: TransformReport | None = None
        if self.transformer is not None:
            transform_result = self.transformer.run()
            run_results = None
            if transform_result.status == "failed":
                raw = transform_result.details.get("run_results_json")
                if raw:
                    try:
                        run_results = json.loads(raw)
                    except Exception:  # noqa: BLE001
                        pass
            transform_report = TransformReport(
                backend=transform_result.backend,
                status=transform_result.status,
                duration_seconds=transform_result.duration_seconds,
                run_results=run_results,
            )
            LOGGER.info("Pipeline completed with transformations.")
        else:
            LOGGER.info("Pipeline completed without transformations.")

        warehouse_label = self._warehouse_location_label()
        report = PipelineReport(
            pipeline_name=source.name,
            warehouse_label=warehouse_label,
            ingestion=ingestion_report,
            transform=transform_report,
        )
        print(format_report(report))  # noqa: T201
        LOGGER.info("Warehouse location: %s", warehouse_label)
        return report

    def _resolve_source_to_run(
        self,
        source: BaseSource,
        force_reload: bool,
    ) -> tuple[BaseSource | None, dict[str, str | None]]:
        """
        Determine which (sub)set of resources actually needs ingesting.

        Returns a (source_to_run, etag_cache) tuple where:
        - source_to_run is None if nothing needs ingesting.
        - etag_cache maps resource_name -> current_etag for every resource
          that will be ingested; passed to _save_checkpoints to avoid a
          redundant HEAD request after ingestion.

        Decision order:
        - force_reload=True        → always run the full source.
        - has checkpointable res.  → per-resource ETag check; partial or None.
        - supports_storage_cache() → legacy file-name check; full or None.
        - otherwise                → always run (e.g. REST API sources).
        """
        if force_reload:
            LOGGER.info("Force reload enabled. Ingestion will run.")
            return source, {}

        checkpointable = source.get_checkpointable_resources()
        if checkpointable:
            changed_etags = self._check_checkpointable_resources(source)
            all_names = {r.name for r in source.get_resources()}
            if not changed_etags:
                LOGGER.info("All resources unchanged. Skipping ingestion.")
                return None, {}
            if set(changed_etags) == all_names:
                return source, changed_etags
            LOGGER.info(
                "%d of %d resource(s) changed. Running partial ingestion.",
                len(changed_etags),
                len(all_names),
            )
            return source.with_filtered_resources(set(changed_etags)), changed_etags

        if not source.supports_storage_cache():
            LOGGER.info("Source does not use storage cache. Ingestion will run.")
            return source, {}

        existing_resource_names = self._existing_storage_resource_names()
        missing_resources = [
            resource.name
            for resource in source.get_resources()
            if resource.name not in existing_resource_names
        ]
        if missing_resources:
            LOGGER.info(
                "Ingestion will run. Resources not detected in storage cache: %s",
                ", ".join(missing_resources),
            )
            return source, {}

        LOGGER.info("Ingestion skipped. Storage cache suggests no new resources.")
        return None, {}

    def _merge_skipped_resources(
        self,
        source: BaseSource,
        source_to_run: BaseSource,
        ingestion_report: IngestionReport,
    ) -> IngestionReport:
        """
        When only a subset of resources was ingested (partial run), prepend the
        skipped resources to the report so every resource appears in the output.
        """
        loaded_names = {r.name for r in source_to_run.get_resources()}
        skipped = [
            ResourceIngestionResult(name=res.name, status="skipped")
            for res in source.get_resources()
            if res.name not in loaded_names
        ]
        if not skipped:
            return ingestion_report
        return IngestionReport(
            source_name=ingestion_report.source_name,
            resources=skipped + ingestion_report.resources,
            duration_seconds=ingestion_report.duration_seconds,
        )

    def _save_checkpoints(
        self,
        source: BaseSource,
        etag_cache: dict[str, str | None],
    ) -> None:
        """
        Persist ETag checkpoints after a successful ingestion run.

        Uses etag_cache (populated during _resolve_source_to_run) to avoid
        a redundant HEAD request per resource.
        """
        checkpointable = {r.name: r for r in source.get_checkpointable_resources()}
        if not checkpointable:
            return

        loaded_at = datetime.now(timezone.utc)
        for resource_name, resource in checkpointable.items():
            etag = etag_cache.get(resource_name)
            self.checkpoints.save(
                ResourceCheckpoint(
                    source_name=source.name,
                    resource_name=resource_name,
                    last_loaded_at=loaded_at,
                    etag=etag,
                )
            )

    def _warehouse_location_label(self) -> str:
        if self.warehouse_kind == "duckdb":
            if self.warehouse_path == ":memory:":
                return "DuckDB in-memory database (:memory:)"
            resolved_path = Path(self.warehouse_path).expanduser().resolve()
            return f"DuckDB file at {resolved_path}"
        if self.warehouse_kind == "motherduck":
            return f"MotherDuck database {self.warehouse_path}"
        return f"{self.warehouse_kind} warehouse at {self.warehouse_path}"
