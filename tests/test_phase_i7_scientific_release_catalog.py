from dataclasses import replace
from pathlib import Path
import json

import pytest

from campaign_repository import (
    CatalogEvidenceRef,
    CatalogQuery,
    CatalogTrustStatus,
    EvidenceIdentity,
    ScientificReleaseBundleBuilder,
    ScientificReleaseCatalog,
    ScientificReleaseCatalogQueryService,
    ScientificReleaseCatalogRecord,
    ScientificReleaseImporter,
    ScientificReleaseVerifier,
    export_catalog_snapshot,
    inspect_release,
    record_from_verified_import,
)
from kernel.exceptions import ValidationError


def sample_record(
    *,
    release_id="R1",
    campaign_id="C1",
    experiment_id="E1",
    release_name="release-1",
    bundle_sha="a" * 64,
    manifest_sha="b" * 64,
    evidence=(),
    kinds=("scientific_evidence",),
):
    return ScientificReleaseCatalogRecord(
        release_id=release_id,
        release_name=release_name,
        campaign_id=campaign_id,
        experiment_id=experiment_id,
        release_manifest_sha256=manifest_sha,
        bundle_sha256=bundle_sha,
        import_path=f"import/{release_id}",
        trust_status=CatalogTrustStatus.VERIFIED,
        component_kinds=kinds,
        evidence=evidence,
    )


def build_verified_import(tmp_path, *, release_name="release-1", sha="1" * 64):
    release = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "producer",
        release_name=release_name,
        campaign_id="C1",
        experiment_id="E1",
        scientific_evidence=(
            EvidenceIdentity(
                "h6.result_set",
                "RESULT-1",
                sha,
            ),
            EvidenceIdentity(
                "h8.publication",
                "PUB-1",
                "2" * 64,
            ),
        ),
        metadata={"source": "I7-test"},
    )
    verification = ScientificReleaseVerifier().verify(
        release.bundle_path,
        expected_bundle_sha256=release.bundle_sha256,
    )
    inspection = inspect_release(release.bundle_path)
    imported = ScientificReleaseImporter(
        tmp_path / "consumer"
    ).import_bundle(
        release.bundle_path,
        expected_bundle_sha256=release.bundle_sha256,
    )
    return release, verification, inspection, imported


def test_evidence_ref():
    value = CatalogEvidenceRef("h6.result_set", "R", "1" * 64)
    assert value.evidence_id == "R"


def test_evidence_bad_sha():
    with pytest.raises(ValidationError):
        CatalogEvidenceRef("x", "y", "bad")


def test_record_verified():
    assert sample_record().verified


def test_record_string_status():
    value = replace(sample_record(), trust_status="verified")
    assert value.trust_status == CatalogTrustStatus.VERIFIED


def test_record_bad_status():
    with pytest.raises(ValidationError):
        replace(sample_record(), trust_status="bad")


def test_record_identity_stable():
    assert sample_record().record_sha256 == sample_record().record_sha256


def test_record_to_dict():
    assert sample_record().to_dict()["schema_version"] == "i7.0"


def test_record_dedup_kinds():
    value = sample_record(kinds=("b", "a", "b"))
    assert value.component_kinds == ("a", "b")


def test_record_duplicate_evidence():
    evidence = CatalogEvidenceRef("x", "y", "1" * 64)
    with pytest.raises(ValidationError):
        sample_record(evidence=(evidence, evidence))


def test_catalog_initialize(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.initialize()
    assert (tmp_path / "catalog.json").is_file()


def test_catalog_register(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    assert catalog.register(sample_record()) is True


def test_catalog_idempotent_register(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    assert catalog.register(sample_record()) is True
    assert catalog.register(sample_record()) is False


def test_catalog_conflict(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    with pytest.raises(ValidationError):
        catalog.register(
            replace(
                sample_record(),
                bundle_sha256="c" * 64,
            )
        )


def test_catalog_contains(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    assert catalog.contains("R1")


def test_catalog_get(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    assert catalog.get("R1")["release_id"] == "R1"


def test_catalog_missing_get(tmp_path):
    with pytest.raises(KeyError):
        ScientificReleaseCatalog(tmp_path).get("missing")


def test_catalog_list_sorted(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R2"))
    catalog.register(sample_record(release_id="R1"))
    assert [x["release_id"] for x in catalog.list_records()] == ["R1", "R2"]


def test_catalog_sha_stable(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    assert catalog.catalog_sha256() == catalog.catalog_sha256()


def test_record_from_verified_import(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    record = record_from_verified_import(
        verification=verification,
        inspection=inspection,
        imported=imported,
    )
    assert record.verified


def test_registration_extracts_evidence(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    record = record_from_verified_import(
        verification=verification,
        inspection=inspection,
        imported=imported,
    )
    assert len(record.evidence) == 2


def test_registration_extracts_component_kinds(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    record = record_from_verified_import(
        verification=verification,
        inspection=inspection,
        imported=imported,
    )
    assert "scientific_evidence" in record.component_kinds


def test_registration_rejects_unverified(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    bad = replace(verification, valid=False, errors=("forced",))
    with pytest.raises(ValidationError):
        record_from_verified_import(
            verification=bad,
            inspection=inspection,
            imported=imported,
        )


def test_registration_rejects_release_id_mismatch(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    bad = replace(imported, release_id="OTHER")
    with pytest.raises(ValidationError):
        record_from_verified_import(
            verification=verification,
            inspection=inspection,
            imported=bad,
        )


def test_registration_rejects_bundle_sha_mismatch(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    bad = replace(imported, bundle_sha256="f" * 64)
    with pytest.raises(ValidationError):
        record_from_verified_import(
            verification=verification,
            inspection=inspection,
            imported=bad,
        )


def test_query_all(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1"))
    catalog.register(sample_record(release_id="R2", campaign_id="C2"))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search()) == 2


def test_query_release_id(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.search(CatalogQuery(release_id="R1"))[0]["release_id"] == "R1"


def test_query_campaign(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1", campaign_id="C1"))
    catalog.register(sample_record(release_id="R2", campaign_id="C2"))
    service = ScientificReleaseCatalogQueryService(catalog)
    result = service.search(CatalogQuery(campaign_id="C2"))
    assert [x["release_id"] for x in result] == ["R2"]


def test_query_experiment(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1", experiment_id="E1"))
    catalog.register(sample_record(release_id="R2", experiment_id="E2"))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search(CatalogQuery(experiment_id="E2"))) == 1


def test_query_release_name(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search(CatalogQuery(release_name="release-1"))) == 1


def test_query_component_kind(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(kinds=("artifact_manifest",)))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search(CatalogQuery(component_kind="artifact_manifest"))) == 1


def test_query_evidence_type(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(
        sample_record(
            evidence=(
                CatalogEvidenceRef("h6.result_set", "R", "1" * 64),
            )
        )
    )
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search(CatalogQuery(evidence_type="h6.result_set"))) == 1


def test_query_evidence_id(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(
        sample_record(
            evidence=(
                CatalogEvidenceRef("h8.publication", "PUB", "1" * 64),
            )
        )
    )
    service = ScientificReleaseCatalogQueryService(catalog)
    assert len(service.search(CatalogQuery(evidence_id="PUB"))) == 1


def test_query_by_release_id(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.by_release_id("R1")["campaign_id"] == "C1"


def test_campaigns(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1", campaign_id="C2"))
    catalog.register(sample_record(release_id="R2", campaign_id="C1"))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.campaigns() == ("C1", "C2")


def test_experiments(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1", experiment_id="E2"))
    catalog.register(sample_record(release_id="R2", experiment_id="E1"))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.experiments() == ("E1", "E2")


def test_experiments_by_campaign(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R1", campaign_id="C1", experiment_id="E1"))
    catalog.register(sample_record(release_id="R2", campaign_id="C2", experiment_id="E2"))
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.experiments(campaign_id="C2") == ("E2",)


def test_evidence_types(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(
        sample_record(
            evidence=(
                CatalogEvidenceRef("h8.publication", "P", "1" * 64),
                CatalogEvidenceRef("h6.result_set", "R", "2" * 64),
            )
        )
    )
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.evidence_types() == ("h6.result_set", "h8.publication")


def test_export_snapshot(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path / "catalog")
    catalog.register(sample_record())
    payload = export_catalog_snapshot(
        catalog,
        tmp_path / "snapshot.json",
    )
    assert payload["record_count"] == 1


def test_export_snapshot_file(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path / "catalog")
    catalog.register(sample_record())
    path = tmp_path / "snapshot.json"
    export_catalog_snapshot(catalog, path)
    assert path.is_file()


def test_export_snapshot_stable(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path / "catalog")
    catalog.register(sample_record())
    a = export_catalog_snapshot(catalog, tmp_path / "a.json")
    b = export_catalog_snapshot(catalog, tmp_path / "b.json")
    assert a["snapshot_sha256"] == b["snapshot_sha256"]


def test_full_i6_i7_flow(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    record = record_from_verified_import(
        verification=verification,
        inspection=inspection,
        imported=imported,
        metadata={"registered_by": "I7-test"},
    )
    catalog = ScientificReleaseCatalog(tmp_path / "catalog")
    assert catalog.register(record)

    service = ScientificReleaseCatalogQueryService(catalog)
    found = service.search(
        CatalogQuery(
            campaign_id="C1",
            evidence_type="h8.publication",
        )
    )

    assert len(found) == 1
    assert found[0]["release_id"] == record.release_id


def test_query_order_deterministic(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record(release_id="R2", campaign_id="C1", experiment_id="E1"))
    catalog.register(sample_record(release_id="R1", campaign_id="C1", experiment_id="E1"))
    service = ScientificReleaseCatalogQueryService(catalog)
    a = service.search()
    b = service.search()
    assert a == b


def test_metadata_preserved(tmp_path):
    record = replace(sample_record(), metadata={"x": 1})
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(record)
    assert catalog.get("R1")["metadata"] == {"x": 1}


def test_record_import_path_preserved(tmp_path):
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(sample_record())
    assert catalog.get("R1")["import_path"] == "import/R1"


def test_unverified_filtered_by_default(tmp_path):
    record = replace(
        sample_record(),
        trust_status=CatalogTrustStatus.UNVERIFIED,
    )
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(record)
    service = ScientificReleaseCatalogQueryService(catalog)
    assert service.search() == ()


def test_unverified_visible_when_requested(tmp_path):
    record = replace(
        sample_record(),
        trust_status=CatalogTrustStatus.UNVERIFIED,
    )
    catalog = ScientificReleaseCatalog(tmp_path)
    catalog.register(record)
    service = ScientificReleaseCatalogQueryService(catalog)
    result = service.search(CatalogQuery(verified_only=False))
    assert len(result) == 1


def test_verified_registration_metadata(tmp_path):
    _, verification, inspection, imported = build_verified_import(tmp_path)
    record = record_from_verified_import(
        verification=verification,
        inspection=inspection,
        imported=imported,
        metadata={"source": "test"},
    )
    assert record.metadata == {"source": "test"}
