from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .catalog_store import ScientificReleaseCatalog


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    release_id: str | None = None
    campaign_id: str | None = None
    experiment_id: str | None = None
    release_name: str | None = None
    evidence_type: str | None = None
    evidence_id: str | None = None
    component_kind: str | None = None
    verified_only: bool = True


class ScientificReleaseCatalogQueryService:
    def __init__(
        self,
        catalog: ScientificReleaseCatalog,
    ):
        self.catalog = catalog

    def search(
        self,
        query: CatalogQuery | None = None,
    ) -> tuple[dict[str, Any], ...]:
        query = query or CatalogQuery()
        records = self.catalog.list_records()

        result = [
            record
            for record in records
            if self._matches(record, query)
        ]

        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item["campaign_id"],
                    item["experiment_id"],
                    item["release_name"],
                    item["release_id"],
                ),
            )
        )

    def by_release_id(self, release_id: str) -> dict[str, Any]:
        return self.catalog.get(release_id)

    def campaigns(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    item["campaign_id"]
                    for item in self.catalog.list_records()
                }
            )
        )

    def experiments(
        self,
        *,
        campaign_id: str | None = None,
    ) -> tuple[str, ...]:
        values = {
            item["experiment_id"]
            for item in self.catalog.list_records()
            if (
                campaign_id is None
                or item["campaign_id"] == campaign_id
            )
        }
        return tuple(sorted(values))

    def evidence_types(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    evidence["evidence_type"]
                    for item in self.catalog.list_records()
                    for evidence in item.get("evidence", [])
                }
            )
        )

    @staticmethod
    def _matches(
        record: dict[str, Any],
        query: CatalogQuery,
    ) -> bool:
        if query.verified_only and not record.get("verified", False):
            return False
        for field in (
            "release_id",
            "campaign_id",
            "experiment_id",
            "release_name",
        ):
            expected = getattr(query, field)
            if expected is not None and record.get(field) != expected:
                return False

        if query.component_kind is not None:
            if query.component_kind not in record.get(
                "component_kinds",
                [],
            ):
                return False

        if (
            query.evidence_type is not None
            or query.evidence_id is not None
        ):
            matched = False
            for evidence in record.get("evidence", []):
                if (
                    query.evidence_type is not None
                    and evidence.get("evidence_type")
                    != query.evidence_type
                ):
                    continue
                if (
                    query.evidence_id is not None
                    and evidence.get("evidence_id")
                    != query.evidence_id
                ):
                    continue
                matched = True
                break
            if not matched:
                return False

        return True
